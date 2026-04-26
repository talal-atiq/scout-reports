import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb+srv://statscout_db_user:zZhokZEXZiCDVjza@statscout-cluster.im4diqm.mongodb.net/?appName=StatScout-Cluster")
    db = client["statscout_db"]
    
    col = db["understat_league_cache"]
    print("Total documents in understat_league_cache:", await col.count_documents({}))
    
    docs = await col.find().to_list(length=10)
    for doc in docs:
        print("League:", doc.get("league"), "Season:", doc.get("season"), "Players count:", len(doc.get("players", [])))

    # Look for Mbappe
    mbappe = await col.aggregate([
        {"$unwind": "$players"},
        {"$match": {"players.player_name": {"$regex": "Mbapp", "$options": "i"}}}
    ]).to_list(length=10)
    print("Mbappe found:", len(mbappe), mbappe[0] if mbappe else "Not found")

    # Look for Igor Thiago
    igor = await col.aggregate([
        {"$unwind": "$players"},
        {"$match": {"players.player_name": {"$regex": "Igor", "$options": "i"}}}
    ]).to_list(length=10)
    print("Igor Thiago found:", len(igor), igor[0] if igor else "Not found")

asyncio.run(main())
