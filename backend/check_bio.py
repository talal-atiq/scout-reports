import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import pprint

async def main():
    client = AsyncIOMotorClient("mongodb+srv://statscout_db_user:zZhokZEXZiCDVjza@statscout-cluster.im4diqm.mongodb.net/?appName=StatScout-Cluster")
    db = client["statscout_db"]
    
    count = await db["player_bio"].count_documents({})
    print(f"Total documents in player_bio: {count}")
    
    sample = await db["player_bio"].find().to_list(length=2)
    print("\nSample Data:")
    for doc in sample:
        pprint.pprint(doc)

asyncio.run(main())
