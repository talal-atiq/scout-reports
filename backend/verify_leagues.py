from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    
    from bson import ObjectId
    
    # Get all player_ids for AM pos_group
    cursor = db["player_spatial_profiles"].find({"pos_group": "AM"}, {"player_id": 1})
    player_ids = [ObjectId(doc["player_id"]) async for doc in cursor]
    
    # Lookup these players in player_lookup
    lookup_cursor = db["player_lookup"].find({"_id": {"$in": player_ids}})
    
    leagues = set()
    teams = set()
    
    async for p in lookup_cursor:
        if "league" in p:
            leagues.add(p["league"])
        if "competitions" in p:
            for c in p["competitions"]:
                leagues.add(c)
        if "latest_team" in p:
            teams.add(p["latest_team"])
            
    print(f"Total AM players found in lookup: {len(teams)}")
    print("Leagues directly found in lookup:", leagues)
    print("Sample teams:", list(teams)[:20])

asyncio.run(main())
