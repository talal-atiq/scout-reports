from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import json
from bson import json_util

async def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    collections = await db.list_collection_names()
    print("Collections:", collections)
    
    # Print one document from likely collections
    for coll_name in collections:
        if "player" in coll_name or "stat" in coll_name or "profile" in coll_name or "understat" in coll_name:
            doc = await db[coll_name].find_one()
            if doc:
                print(f"\n--- {coll_name} ---")
                keys = list(doc.keys())
                print(f"Sample keys: {keys[:20]}")
                # print some nested keys for match_player_stats or player_spatial_profiles
                if "metrics" in doc:
                    print("Metrics keys:", list(doc["metrics"].keys())[:10])

asyncio.run(main())
