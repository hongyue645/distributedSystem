import os
import time
import threading
import httpx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Smart Campus Lost & Found Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

MATCHING_WORKER_URL = os.environ.get(
    "MATCHING_WORKER_URL",
    "http://localhost:8001"
)

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def monitor_system_health():
    """
    Background thread for basic gateway health monitoring.
    This is used to demonstrate threading in the distributed system.
    """
    while True:
        print("🧵 [THREAD] Gateway API is running.")
        time.sleep(60)


health_thread = threading.Thread(target=monitor_system_health, daemon=True)
health_thread.start()


class ItemPayload(BaseModel):
    item_type: str
    name: str
    category: str
    color: str


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "gateway"
    }


@app.post("/items")
async def report_item(item: ItemPayload):
    """
    Receives a lost/found item, stores it in the database,
    and remotely calls the matching worker through REST-based RPC.
    """

    try:
        data = item.model_dump()
        data["status"] = "open"

        # 1. Save the item to Supabase
        response = supabase.table("items").insert(data).execute()

        if not response.data:
            raise HTTPException(
                status_code=400,
                detail="Failed to insert item into database"
            )

        new_item = response.data[0]
        new_item_id = new_item["id"]

        # 2. RPC call to Matching Worker
        matching_result = None

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                rpc_response = await client.post(
                    f"{MATCHING_WORKER_URL}/rpc/match-item",
                    json={"item_id": new_item_id}
                )

                rpc_response.raise_for_status()
                matching_result = rpc_response.json()

        except Exception as rpc_error:
            # Fault tolerance:
            # If the matching worker is down, the gateway still accepts the item.
            matching_result = {
                "matched": False,
                "message": "Item saved, but matching worker is unavailable",
                "error": str(rpc_error)
            }

        return {
            "message": "Item reported successfully",
            "data": new_item,
            "matching_result": matching_result
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/items")
async def get_items():
    """
    Fetches all items so the frontend can display them.
    """

    try:
        response = supabase.table("items").select("*").execute()

        return {
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))