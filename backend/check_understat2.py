import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb+srv://statscout_db_user:zZhokZEXZiCDVjza@statscout-cluster.im4diqm.mongodb.net/?appName=StatScout-Cluster")
    db = client["statscout_db"]
    col = db["understat_league_cache"]

    brentford = await col.aggregate([
        {"$match": {"league": "EPL"}},
        {"$unwind": "$players"},
        {"$match": {"players.team_title": "Brentford"}},
        {"$project": {"player_name": "$players.player_name", "team": "$players.team_title"}}
    ]).to_list(length=100)
    
    print("Brentford players:", [p["player_name"] for p in brentford])
    
    # Real madrid players
    rm = await col.aggregate([
        {"$match": {"league": "La_liga"}},
        {"$unwind": "$players"},
        {"$match": {"players.team_title": "Real Madrid"}},
        {"$project": {"player_name": "$players.player_name", "team": "$players.team_title"}}
    ]).to_list(length=100)
    print("RM players:", [p["player_name"] for p in rm])

asyncio.run(main())
