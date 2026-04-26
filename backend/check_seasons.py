from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    
    colls = ["performance_stats", "match_player_stats", "players_outfield_v2", "players", "understat_league_cache"]
    for coll in colls:
        try:
            seasons = await db[coll].distinct("season")
            print(f"{coll} seasons: {seasons}")
        except Exception as e:
            print(f"Error checking {coll}: {e}")

asyncio.run(main())
