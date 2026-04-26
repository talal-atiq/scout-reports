from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    
    doc = await db["player_lookup"].find_one()
    print(f"Sample player_lookup keys: {doc.keys()}")
    for k, v in doc.items():
        if k not in ['_id']:
            print(f"{k}: {v}")
    
asyncio.run(main())
