from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    
    # Use a known player ID from previous check
    pid = "69a588af4d777bc0ff70b8bf" # An AM player
    
    # Get his spatial profile
    profile = await db["player_spatial_profiles"].find_one({"player_id": pid})
    if not profile:
        print("No spatial profile found for this player")
        return
        
    pos_group = profile.get("pos_group")
    rankings = profile.get("rankings", {})
    
    print(f"\n--- Rankings for Player {pid} (pos_group: {pos_group}) ---")
    for k, v in rankings.items():
        if "rank" in k or "total" in k:
            print(f"{k}: {v}")
            
    # Now let's verify the pool!
    # How many total players are in this pos_group in player_spatial_profiles?
    count_in_profiles = await db["player_spatial_profiles"].count_documents({"pos_group": pos_group})
    print(f"\nTotal documents in player_spatial_profiles with pos_group={pos_group}: {count_in_profiles}")
    
    # What leagues do these players belong to?
    cursor = db["player_spatial_profiles"].find({"pos_group": pos_group}, {"player_id": 1})
    player_ids = [doc["player_id"] async for doc in cursor]
    
    # Lookup their leagues in player_lookup or match_player_stats
    lookup_cursor = db["player_lookup"].find({"statscout_id": {"$in": player_ids}})
    leagues = set()
    async for p in lookup_cursor:
        # Some player_lookups might have 'league' or 'competitions'
        # Or we can check what team they play for
        if "teams" in p:
             pass
    
    # Get the distinct competitions for all players in this pos group

    # Let's get the distinct competitions for all players in this pos group
    # To do this efficiently, let's just get 10 random players from this pos_group and check their competition
    import random
    sample_ids = random.sample(player_ids, min(100, len(player_ids)))
    
    # Get names
    sample_names = []
    async for p in db["player_lookup"].find({"statscout_id": {"$in": sample_ids}}):
        sample_names.append(p["player_name"])
        
    comps = await db["match_player_stats"].distinct("competition", {"player_name": {"$in": sample_names}})
    print(f"Competitions found in this pool: {comps}")

asyncio.run(main())
