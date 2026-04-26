import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

def clear_db():
    url = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DB_NAME", "statscout_db")
    client = MongoClient(url, serverSelectionTimeoutMS=15000)
    db = client[db_name]

    print("Dropping legacy player_spatial_profiles collection...")
    db.player_spatial_profiles.drop()
    
    print("Dropping legacy season_distributions collection...")
    db.season_distributions.drop()
    
    print("Database is clean and ready for the 25/26 Parquet ETL.")

if __name__ == "__main__":
    clear_db()
