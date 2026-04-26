from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["statscout"]
    collections = await db.list_collection_names()
    print("Collections:", collections)
    
    # Print one document from likely collections
    for coll_name in collections:
        if "player" in coll_name or "stat" in coll_name:
            doc = await db[coll_name].find_one()
            if doc:
                print(f"\n--- {coll_name} ---")
                keys = list(doc.keys())
                print(f"Sample keys: {keys[:20]}")

asyncio.run(main())
