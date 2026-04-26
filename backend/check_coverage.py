from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    
    # Check player_spatial_profiles count
    spatial_count = await db["player_spatial_profiles"].count_documents({})
    spatial_teams = await db["player_spatial_profiles"].distinct("team")
    print(f"player_spatial_profiles: {spatial_count} players across {len(spatial_teams)} teams.")
    
    # Check match_player_stats for 2025/2026
    match_teams = await db["match_player_stats"].distinct("team", {"season": "2025/2026"})
    match_players = len(await db["match_player_stats"].distinct("player_name", {"season": "2025/2026"}))
    match_comps = await db["match_player_stats"].distinct("competition", {"season": "2025/2026"})
    print(f"match_player_stats (25/26): {match_players} players across {len(match_teams)} teams.")
    print(f"match_player_stats (25/26) competitions: {match_comps}")

asyncio.run(main())
