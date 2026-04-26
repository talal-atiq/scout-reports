import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb+srv://statscout_db_user:zZhokZEXZiCDVjza@statscout-cluster.im4diqm.mongodb.net/?appName=StatScout-Cluster")
    db = client["statscout_db"]
    
    cursor = db["match_player_stats"].aggregate([
        {"$match": {"player_name": {"$regex": "Gueye", "$options": "i"}, "season": "25-26"}},
        {"$group": {"_id": "$player_name", "count": {"$sum": 1}, "team": {"$first": "$team"}}}
    ])
    res = await cursor.to_list(length=10)
    print("Match Player Stats Gueyes:", res)

    print("Checking understat for Idrissa Gueye Everton:")
    gueye = await db["understat_league_cache"].aggregate([
        {"$unwind": "$players"},
        {"$match": {"players.player_name": "Idrissa Gueye"}}
    ]).to_list(length=10)
    for g in gueye:
        p = g["players"]
        print(f"Name: {p.get('player_name')}, Team: {p.get('team_title')}, Goals: {p.get('goals')}, Assists: {p.get('assists')}, Games: {p.get('games')}")

asyncio.run(main())
