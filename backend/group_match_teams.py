from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    
    # Aggregate teams by competition in match_player_stats for season 25/26
    pipeline = [
        {"$match": {"season": "2025/2026"}},
        {"$group": {
            "_id": "$competition",
            "teams": {"$addToSet": "$team"}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    results = await db["match_player_stats"].aggregate(pipeline).to_list(length=None)
    
    for result in results:
        league = result["_id"]
        teams = sorted(result["teams"])
        print(f"\n--- {league} ({len(teams)} teams) ---")
        for t in teams:
            print(t)

asyncio.run(main())
