import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb+srv://statscout_db_user:zZhokZEXZiCDVjza@statscout-cluster.im4diqm.mongodb.net/?appName=StatScout-Cluster")
    db = client["statscout_db"]
    
    seasons = ["25-26", "2025-26", "2025/26", "2025-2026", "2025/2026"]
    
    cursor = db["match_player_stats"].aggregate([
        {"$match": {"team": "Everton", "season": {"$in": seasons}, "player_name": {"$regex": "Gueye", "$options": "i"}}},
        {"$group": {"_id": "$player_name", "count": {"$sum": 1}, "team": {"$first": "$team"}}}
    ])
    res = await cursor.to_list(length=10)
    print("Everton Gueyes:", res)

asyncio.run(main())
