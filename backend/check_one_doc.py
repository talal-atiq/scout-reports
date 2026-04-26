import os
from dotenv import load_dotenv
from pymongo import MongoClient
import pprint

load_dotenv("d:/scout-reports/backend/.env")

url = os.getenv("MONGODB_URL")
client = MongoClient(url)
db = client["statscout_db"]

print("--- player_spatial_profiles Doku ---")
doc = db.player_spatial_profiles.find_one({"player_name": {"$regex": "Doku", "$options": "i"}})
if doc:
    if "touch_heatmap" in doc:
        print("Touch Heatmap keys:", doc["touch_heatmap"].keys())
        print("Touch Heatmap 'all' shape:", len(doc["touch_heatmap"]["all"]), "x", len(doc["touch_heatmap"]["all"][0]))

