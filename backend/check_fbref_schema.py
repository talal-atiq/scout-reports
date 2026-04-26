import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND_DIR = Path("d:/scout-reports/backend")
load_dotenv(BACKEND_DIR / ".env")

def check_fbref():
    url = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DB_NAME", "statscout_db")
    client = MongoClient(url, serverSelectionTimeoutMS=15000)
    db = client[db_name]

    print("Checking players_outfield_v2 schema...")
    doc = db.players_outfield_v2.find_one()
    import pprint
    pprint.pprint(doc)

if __name__ == "__main__":
    check_fbref()
