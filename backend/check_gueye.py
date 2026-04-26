import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb+srv://statscout_db_user:zZhokZEXZiCDVjza@statscout-cluster.im4diqm.mongodb.net/?appName=StatScout-Cluster")
    db = client["statscout_db"]
    
    player_name = "Idrissa Gueye"
    
    # 1. Match Player Stats
    print("--- MATCH PLAYER STATS ---")
    cursor = db["match_player_stats"].find({
        "player_name": {"$regex": player_name, "$options": "i"},
        "season": {"$in": ["2025-26", "25-26", "2025/26"]}
    })
    matches = await cursor.to_list(length=100)
    print(f"Matches played in match_player_stats: {len(matches)}")
    if matches:
        print(f"First match example: {matches[0].get('team')} - {matches[0].get('match_id')}")

    # 2. Understat cache
    print("--- UNDERSTAT CACHE ---")
    gueye = await db["understat_league_cache"].aggregate([
        {"$unwind": "$players"},
        {"$match": {"players.player_name": {"$regex": "Gueye", "$options": "i"}}}
    ]).to_list(length=10)
    for g in gueye:
        p = g["players"]
        print(f"Name: {p.get('player_name')}, Team: {p.get('team_title')}, Goals: {p.get('goals')}, Assists: {p.get('assists')}, Games: {p.get('games')}")

asyncio.run(main())
