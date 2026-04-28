import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
from thefuzz import fuzz

load_dotenv()

app = FastAPI(title="Smart Campus Lost & Found Matching Worker")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class MatchRequest(BaseModel):
    item_id: int


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "matching-worker"
    }


@app.post("/rpc/match-item")
def match_item(request: MatchRequest):
    """
    RPC endpoint called by the Gateway.
    It matches one newly submitted item with existing open opposite-type items.
    """

    try:
        # 1. Get the newly submitted item
        new_item_response = (
            supabase.table("items")
            .select("*")
            .eq("id", request.item_id)
            .execute()
        )

        if not new_item_response.data:
            raise HTTPException(status_code=404, detail="Item not found")

        new_item = new_item_response.data[0]

        if new_item["status"] != "open":
            return {
                "matched": False,
                "message": "Item is not open, no matching needed"
            }

        # 2. Decide the opposite type
        if new_item["item_type"] == "lost":
            opposite_type = "found"
        else:
            opposite_type = "lost"

        # 3. Fetch candidate items
        candidates_response = (
            supabase.table("items")
            .select("*")
            .eq("status", "open")
            .eq("item_type", opposite_type)
            .execute()
        )

        candidates = candidates_response.data

        best_match = None
        best_score = 0

        # 4. Compare with candidates
        for candidate in candidates:
            category_match = (
                str(new_item["category"]).lower()
                == str(candidate["category"]).lower()
            )

            if not category_match:
                continue

            name_score = fuzz.token_set_ratio(
                str(new_item["name"]),
                str(candidate["name"])
            )

            color_score = fuzz.token_set_ratio(
                str(new_item["color"]),
                str(candidate["color"])
            )

            average_score = (name_score + color_score) / 2

            if average_score > best_score:
                best_score = average_score
                best_match = candidate

        # 5. Update database if match is strong enough
        if best_match and best_score >= 80:
            supabase.table("items").update(
                {"status": "matched"}
            ).eq("id", new_item["id"]).execute()

            supabase.table("items").update(
                {"status": "matched"}
            ).eq("id", best_match["id"]).execute()

            return {
                "matched": True,
                "message": "Match found",
                "new_item_id": new_item["id"],
                "matched_item_id": best_match["id"],
                "score": best_score
            }

        return {
            "matched": False,
            "message": "No match found",
            "new_item_id": new_item["id"],
            "best_score": best_score
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))