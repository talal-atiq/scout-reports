from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    
    teams = await db["player_spatial_profiles"].distinct("team")
    teams.sort()
    print("All teams:")
    for t in teams:
        print(t)

asyncio.run(main())
