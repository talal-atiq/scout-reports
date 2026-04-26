import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import pprint

async def main():
    client = AsyncIOMotorClient("mongodb+srv://statscout_db_user:zZhokZEXZiCDVjza@statscout-cluster.im4diqm.mongodb.net/?appName=StatScout-Cluster")
    db = client["statscout_db"]
    
    # 1. Check match_player_stats for position
    print("--- MATCH PLAYER STATS ---")
    doc = await db["match_player_stats"].find_one()
    print("Keys in match_player_stats:", doc.keys() if doc else "No docs")
    if doc:
        print("Position field present?", "position" in doc, "pos" in doc)
        pprint.pprint({k: v for k, v in doc.items() if "pos" in k.lower()})
        
    # 2. Check player_spatial_profiles
    print("\n--- PLAYER SPATIAL PROFILES ---")
    count = await db["player_spatial_profiles"].count_documents({})
    print("Total docs in spatial_profiles:", count)
    
    spatial_docs = await db["player_spatial_profiles"].find().to_list(length=2)
    for sdoc in spatial_docs:
        print("\nDoc Keys:")
        pprint.pprint(list(sdoc.keys()))
        print("Player Name:", sdoc.get("player_name"))
        print("Match/Season context:")
        pprint.pprint({k: v for k, v in sdoc.items() if k in ["season", "match_id", "team"]})
        print("Position fields:", {k: v for k, v in sdoc.items() if "pos" in k.lower()})
        # print first few keys
        pprint.pprint({k: sdoc[k] for k in list(sdoc.keys())[:5]})

asyncio.run(main())
