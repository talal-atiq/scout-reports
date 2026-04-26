from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from collections import defaultdict
from dotenv import load_dotenv

async def main():
    load_dotenv()
    mongo_url = os.environ.get("MONGODB_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["statscout_db"]
    
    # 1. Get the 49 teams from player_spatial_profiles
    spatial_teams = await db["player_spatial_profiles"].distinct("team")
    
    # 2. Find their competition in match_player_stats for season 25/26
    team_to_league = {}
    for team in spatial_teams:
        # Some teams might have slightly different names, but let's try exact match
        doc = await db["match_player_stats"].find_one({"team": team, "season": "2025/2026"})
        if doc and "competition" in doc:
            team_to_league[team] = doc["competition"]
        else:
            # Fallback if the team is not found in match_player_stats for 25/26
            # Maybe look in player_lookup to see if there's league info
            team_to_league[team] = "Unknown/Other Leagues"
            
    # Group by league
    league_groups = defaultdict(list)
    for team, league in team_to_league.items():
        league_groups[league].append(team)
        
    for league, teams in sorted(league_groups.items()):
        print(f"\n--- {league} ({len(teams)} teams) ---")
        teams.sort()
        for t in teams:
            print(t)

asyncio.run(main())
