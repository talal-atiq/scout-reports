import unicodedata
import difflib
from motor.motor_asyncio import AsyncIOMotorDatabase

def normalize_name(name: str) -> str:
    """Normalize name by removing accents, special chars, and lowercasing."""
    if not name:
        return ""
    name = str(name).lower().strip()
    # Remove accents
    name = ''.join(c for c in unicodedata.normalize('NFD', name)
                  if unicodedata.category(c) != 'Mn')
    return name



async def get_scatter_data(db: AsyncIOMotorDatabase, season: str = "2025/2026", min_matches: int = 10):
    # 1. Fetch Spatial Profiles
    # Note: Spatial profiles might use "25-26" or "2025/2026". We'll query both to be safe or use what's passed.
    spatial_cursor = db.player_spatial_profiles.find(
        {"matches_processed": {"$gte": min_matches}},
        {"player_name": 1, "league": 1, "pos_group": 1, "style_cluster": 1, "per_90": 1, "matches_processed": 1}
    )
    spatial_players = await spatial_cursor.to_list(length=None)

    # 2. Fetch Understat Data
    understat_cursor = db.understat_league_cache.find({})
    understat_docs = await understat_cursor.to_list(length=None)
    
    # Flatten understat players
    u_players = []
    for doc in understat_docs:
        if "players" in doc:
            u_players.extend(doc["players"])

    # 3. Build lookup maps for Understat
    u_norm_map = {}
    u_parts_map = {}
    for up in u_players:
        norm_name = normalize_name(up.get("player_name", ""))
        u_norm_map[norm_name] = up
        if len(norm_name) >= 4:
            u_parts_map[norm_name] = set(norm_name.split())

    merged_data = []

    # 4. Merge Logic
    for sp in spatial_players:
        sp_name = sp.get("player_name", "")
        sp_norm = normalize_name(sp_name)
        
        matched_up = None
        
        # Tier 1: Exact Normalized Match
        if sp_norm in u_norm_map:
            matched_up = u_norm_map[sp_norm]
        else:
            # Tier 2: Subset Match
            if len(sp_norm) >= 4:
                sp_parts = set(sp_norm.split())
                sp_len = len(sp_parts)
                for u_norm, u_parts in u_parts_map.items():
                    if sp_len <= len(u_parts):
                        if sp_parts.issubset(u_parts):
                            matched_up = u_norm_map[u_norm]
                            break
                    else:
                        if u_parts.issubset(sp_parts):
                            matched_up = u_norm_map[u_norm]
                            break
        
        # Compile final player object
        p_data = {
            "player_id": str(sp["_id"]),
            "player_name": sp_name,
            "league": sp.get("league"),
            "pos_group": sp.get("pos_group"),
            "style_cluster": sp.get("style_cluster", {}).get("cluster_label", "Unknown") if isinstance(sp.get("style_cluster"), dict) else "Unknown",
            "matches_processed": sp.get("matches_processed", 0),
            "stats": sp.get("per_90", {})
        }
        
        # Merge Understat stats if found
        if matched_up:
            try:
                time_mins = float(matched_up.get("time", 1))
                if time_mins > 0:
                    p_data["stats"]["goals_p90"] = (float(matched_up.get("goals", 0)) / time_mins) * 90
                    p_data["stats"]["xG_p90"] = (float(matched_up.get("xG", 0)) / time_mins) * 90
                    p_data["stats"]["npg_p90"] = (float(matched_up.get("npg", 0)) / time_mins) * 90
                    p_data["stats"]["npxG_p90"] = (float(matched_up.get("npxG", 0)) / time_mins) * 90
                    p_data["stats"]["assists_p90"] = (float(matched_up.get("assists", 0)) / time_mins) * 90
                    p_data["stats"]["xA_p90"] = (float(matched_up.get("xA", 0)) / time_mins) * 90
                    p_data["stats"]["xGChain_p90"] = (float(matched_up.get("xGChain", 0)) / time_mins) * 90
                    p_data["stats"]["xGBuildup_p90"] = (float(matched_up.get("xGBuildup", 0)) / time_mins) * 90
                    p_data["minutes_played"] = time_mins
            except (ValueError, TypeError):
                p_data["minutes_played"] = sp.get("matches_processed", 0) * 90
        else:
            p_data["minutes_played"] = sp.get("matches_processed", 0) * 90
            
        merged_data.append(p_data)

    return merged_data
