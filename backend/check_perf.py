from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
import pprint
from dotenv import load_dotenv

async def main():
    load_dotenv()
    client = AsyncIOMotorClient(os.environ.get("MONGODB_URL"))
    db = client["statscout_db"]
    
    doc = await db["performance_stats"].find_one()
    print("--- performance_stats sample ---")
    if doc:
        print("Keys:", doc.keys())
        if "stats" in doc:
            print("Stats keys:", doc["stats"].keys())
            if "Attacking" in doc["stats"] or any(isinstance(v, dict) for v in doc["stats"].values()):
                 print("Sample of nested stats:")
                 pprint.pprint(doc["stats"])
    else:
        print("Empty")

asyncio.run(main())
