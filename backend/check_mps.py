from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    
    doc = await db["match_player_stats"].find_one({"season": "2025/2026"})
    if doc:
        print("Keys:", doc.keys())
        for k, v in doc.items():
            if type(v) in [int, float] and k not in ['_id']:
                print(f"{k}: {v}")
    else:
        print("No doc found")

asyncio.run(main())
