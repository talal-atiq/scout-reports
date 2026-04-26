import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("d:/scout-reports/backend/.env")

url = os.getenv("MONGODB_URL")
client = MongoClient(url)
db = client["statscout_db"]
count = db.player_spatial_profiles.count_documents({})
print(f"Total profiles inserted so far: {count}")
