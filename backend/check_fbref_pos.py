import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND_DIR = Path("d:/scout-reports/backend")
load_dotenv(BACKEND_DIR / ".env")

def get_distinct_positions():
    url = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DB_NAME", "statscout_db")
    client = MongoClient(url, serverSelectionTimeoutMS=15000)
    db = client[db_name]

    print("Fetching distinct positions from players_outfield_v2...")
    distinct_pos = db.players_outfield_v2.distinct("pos")
    
    print("\n--- DISTINCT POSITIONS ---")
    for pos in sorted(distinct_pos):
        print(f"'{pos}'")

if __name__ == "__main__":
    get_distinct_positions()
