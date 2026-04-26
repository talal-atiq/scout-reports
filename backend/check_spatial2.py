import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb+srv://statscout_db_user:zZhokZEXZiCDVjza@statscout-cluster.im4diqm.mongodb.net/?appName=StatScout-Cluster")
    db = client["statscout_db"]
    
    doc = await db["player_spatial_profiles"].find_one()
    print("Keys in player_spatial_profiles:")
    print(list(doc.keys()))
    print("Context fields:")
    for k in ["player_name", "league", "season", "pos_group"]:
        print(f"{k}: {doc.get(k)}")

asyncio.run(main())
