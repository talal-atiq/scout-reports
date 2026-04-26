import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("d:/scout-reports/backend/.env")

url = os.getenv("MONGODB_URL")
client = MongoClient(url)
db = client["statscout_db"]

# 25/26 LSM (League Strength Multiplier)
LSM = {
    "Premier League": 1.10, "La Liga": 1.08, "Serie A": 1.02, 
    "Bundesliga": 1.02, "Ligue 1": 0.95
}

def get_top_players(pool_name, limit=5):
    projection = {
        "player_name": 1, "league": 1, "percentiles_2526": 1, 
        "sub_role": 1, "similar_players": 1
    }
    
    players = list(db.player_spatial_profiles.find({"sub_role": pool_name}, projection))
    
    scored_players = []
    for p in players:
        p_data = p.get("percentiles_2526", {})
        if not p_data: continue
        
        # Scouting logic for score
        score = sum(p_data.values()) / len(p_data)
        coeff = LSM.get(p.get("league"), 1.0)
        
        # Get the #1 Twin
        twin = p.get("similar_players", [{}])[0]
        twin_str = f"{twin.get('player_name', 'N/A')} ({twin.get('similarity', 0)}%)"

        scored_players.append({
            "name": p["player_name"],
            "league": p.get("league"),
            "score": score * coeff,
            "twin": twin_str
        })

    scored_players.sort(key=lambda x: x["score"], reverse=True)
    return scored_players[:limit]

print("--- 25/26 TACTICAL TWINS (Top 5 Per Pool) ---")

for role in ["Striker", "Winger", "MF", "CenterBack", "Fullback"]:
    print(f"\n--- TOP {role.upper()}S & THEIR TWINS ---")
    for i, p in enumerate(get_top_players(role), 1):
        print(f"{i}. {p['name']} ({p['league']}) -> Most Similar: {p['twin']}")
