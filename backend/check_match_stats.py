import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
import pprint

BACKEND_DIR = Path("d:/scout-reports/backend")
load_dotenv(BACKEND_DIR / ".env")

def check_match_stats():
    url = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DB_NAME", "statscout_db")
    client = MongoClient(url, serverSelectionTimeoutMS=15000)
    db = client[db_name]

    print("Checking match_player_stats schema...")
    doc = db.match_player_stats.find_one()
    pprint.pprint(doc)

if __name__ == "__main__":
    check_match_stats()
