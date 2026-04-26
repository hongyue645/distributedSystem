import os
import time
from supabase import create_client, Client
from dotenv import load_dotenv
from thefuzz import fuzz  # <-- New fuzzy matching library

# Load the exact same keys from your .env file
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

print("🚀 Matching Engine Worker started! Scanning the database every 10 seconds...")

def find_matches():
    try:
        # 1. Fetch all items that haven't been matched yet
        response = supabase.table("items").select("*").eq("status", "open").execute()
        items = response.data

        # Separate them into two lists
        lost_items = [item for item in items if item["item_type"] == "lost"]
        found_items = [item for item in items if item["item_type"] == "found"]

        # 2. Compare every lost item to every found item
        for lost in lost_items:
            for found in found_items:
                
                # We still want the Category to be an exact match (e.g., "Electronics" == "electronics")
                category_match = lost["category"].lower() == found["category"].lower()
                
                # FUZZY MATCHING: Calculate similarity scores (0 to 100)
                # token_set_ratio ignores extra words and word order
                name_score = fuzz.token_set_ratio(lost["name"], found["name"])
                color_score = fuzz.token_set_ratio(lost["color"], found["color"])

                # The New Rule: Category must match, and Name/Color must be at least 80% similar
                if category_match and name_score > 80 and color_score > 80:
                    
                    print(f"🎉 FUZZY MATCH! Name: {name_score}%, Color: {color_score}%")
                    print(f"   Mapped Lost '{lost['name']}' to Found '{found['name']}'")
                    
                    # 3. Update both items in the database to show they are matched!
                    supabase.table("items").update({"status": "matched"}).eq("id", lost["id"]).execute()
                    supabase.table("items").update({"status": "matched"}).eq("id", found["id"]).execute()
                    
                    # Remove the found item from our temporary list so we don't match it twice
                    found_items.remove(found)
                    break # Move on to check the next lost item

    except Exception as e:
        print(f"❌ Error communicating with database: {e}")

# The Infinite Loop
while True:
    find_matches()
    # Go to sleep for 10 seconds before waking up and checking again
    time.sleep(10)