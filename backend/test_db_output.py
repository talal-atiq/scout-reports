import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND_DIR = Path("d:/scout-reports/backend")
load_dotenv(BACKEND_DIR / ".env")

def analyze_players():
    url = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DB_NAME", "statscout_db")
    client = MongoClient(url, serverSelectionTimeoutMS=15000)
    db = client[db_name]

    targets = ["Erling Haaland", "Igor Thiago", "Pedro Porro", "Bruno Fernandes"]

    for t in targets:
        # Case insensitive search using regex
        doc = db.player_spatial_profiles.find_one({"player_name": {"$regex": f"^{t}$", "$options": "i"}})
        
        print(f"\n{'='*50}")
        if not doc:
            print(f"[x] {t} not found in database!")
            continue
            
        print(f"[PROFILE] {doc['player_name'].upper()} ({doc['team']})")
        print(f"Position: {doc['pos_group']}")
        print(f"Playstyle Tag: {doc['style_cluster'].get('cluster_label', 'Unknown')}")
        print(f"Touches Processed: {sum(sum(row) for row in doc['touch_heatmap']['all'])}")
        
        print("\n--- ELITE PERCENTILES (14-Slice Pizza Chart) ---")
        percentiles = doc.get("percentiles_2526", {})
        if not percentiles:
            print("No percentiles calculated.")
            continue
            
        # Sort percentiles descending for display
        sorted_p = sorted(percentiles.items(), key=lambda x: x[1], reverse=True)
        for stat, val in sorted_p:
            # Highlight elite stats
            if val >= 90:
                print(f"  [++] {stat:22}: {val:.1f}th")
            elif val >= 75:
                print(f"  [+]  {stat:22}: {val:.1f}th")
            elif val >= 50:
                print(f"  [=]  {stat:22}: {val:.1f}th")
            else:
                print(f"  [-]  {stat:22}: {val:.1f}th")

if __name__ == "__main__":
    analyze_players()
