import os
import time
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

# Load the keys from your .env file
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Smart Campus Lost & Found Gateway")

# Allow the frontend to talk to this API safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can lock this down to your frontend URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def monitor_system_health():
    """A background thread that runs independently to log system health."""
    while True:
        print("🧵 [THREAD] Health Check: Gateway API is active and ready for requests.")
        time.sleep(60) # Logs every 60 seconds

# Start the background thread as a daemon so it closes when the server closes
health_thread = threading.Thread(target=monitor_system_health, daemon=True)
health_thread.start()

# Define what an incoming Item should look like
class ItemPayload(BaseModel):
    item_type: str  # "lost" or "found"
    name: str
    category: str
    color: str

@app.post("/items")
async def report_item(item: ItemPayload):
    """Receives a new lost or found item and saves it to the database."""
    try:
        # Convert the payload to a dictionary and force the status to "open"
        data = item.model_dump()
        data["status"] = "open" 
        
        # Insert into the Supabase 'items' table
        response = supabase.table("items").insert(data).execute()
        return {"message": "Item reported successfully", "data": response.data}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/items")
async def get_items():
    """Fetches all items so the frontend can display them."""
    try:
        response = supabase.table("items").select("*").execute()
        return {"data": response.data}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))