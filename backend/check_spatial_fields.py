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
    
    doc = await db["player_spatial_profiles"].find_one()
    if doc:
        print("Keys:", doc.keys())
        for k, v in doc.items():
            if k not in ['_id', 'pass_map_points', 'heat_map_matrix', 'cluster_zones']:
                if isinstance(v, dict):
                    print(f"{k}: keys={list(v.keys())}")
                else:
                    print(f"{k}: {v}")
    else:
        print("No doc found")

asyncio.run(main())
