from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
import pprint
from dotenv import load_dotenv

async def main():
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    
    # Try an Attacker
    doc_fwd = await db["player_spatial_profiles"].find_one({"pos_group": "FWD"})
    if doc_fwd:
        print("FWD player percentiles keys:", list(doc_fwd.get("percentiles_2526", {}).keys()))
        print("FWD player rankings keys:", list(doc_fwd.get("rankings", {}).keys()))

    # Try a Midfielder
    doc_mid = await db["player_spatial_profiles"].find_one({"pos_group": "MID"})
    if doc_mid:
        print("\nMID player percentiles keys:", list(doc_mid.get("percentiles_2526", {}).keys()))

    print("\nFWD rankings sample:", doc_fwd.get("rankings", {}))
    
    # Also we need to check if rankings are domestic or top 5 leagues.
    # Actually, we can check how many players are ranked. 
    # e.g., tackles_total = 400 means top 5 leagues (a single league only has ~50-80 players per position).
    if doc_fwd and "tackles_total" in doc_fwd.get("rankings", {}):
        print(f"\nFWD tackles_total: {doc_fwd['rankings']['tackles_total']} players in this pool")
    if doc_mid and "tackles_total" in doc_mid.get("rankings", {}):
        print(f"MID tackles_total: {doc_mid['rankings']['tackles_total']} players in this pool")


asyncio.run(main())
