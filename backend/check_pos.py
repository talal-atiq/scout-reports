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
    
    pos_groups = await db["player_spatial_profiles"].distinct("pos_group")
    print("Unique pos_groups:", pos_groups)
    
    for pg in pos_groups:
        doc = await db["player_spatial_profiles"].find_one({"pos_group": pg})
        if doc:
            rankings = doc.get("rankings", {})
            total_players = rankings.get("tackles_total") or rankings.get("shots_total", 0)
            print(f"\n[{pg}] Example Player: {doc.get('player_id')}")
            print(f"Total players in pool: {total_players}")
            print("percentiles_2526 keys:", list(doc.get("percentiles_2526", {}).keys()))

asyncio.run(main())
