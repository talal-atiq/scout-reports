from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, Depends, HTTPException, Query, status
import math
import statistics

from app.api.dependencies import get_current_user, get_db
from app.schemas.common import MessageResponse
from app.services.scatter_service import get_scatter_data

router = APIRouter(prefix="/spatial", tags=["spatial"])

@router.get("/health", response_model=MessageResponse)
async def spatial_health(_user=Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Spatial routes ready")

@router.get("/profile")
async def get_spatial_profile(
    player_name: str = Query(..., min_length=2),
    season: str = Query(default="2025/2026"),
    _user=Depends(get_current_user),
    db: AsyncIOMotorDatabase | None = Depends(get_db),
):
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB connection unavailable",
        )

    # Use regex for case-insensitive exact match
    docs = await db.player_spatial_profiles.find({
        "player_name": {"$regex": f"^{player_name}$", "$options": "i"},
        "season": season
    }, {"_id": 0}).sort("matches_processed", -1).limit(1).to_list(1)

    if not docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spatial profile not found for {player_name}",
        )
    return docs[0]

@router.get("/scatter")
async def get_scatter_data_route(
    season: str = Query(default="2025/2026"),
    min_matches: int = Query(default=10),
    _user=Depends(get_current_user),
    db: AsyncIOMotorDatabase | None = Depends(get_db),
):
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB connection unavailable",
        )
    data = await get_scatter_data(db, season, min_matches)
    with open("scatter_debug.log", "a") as f:
        f.write(f"Scatter Request: season={season}, min_matches={min_matches}, returned_len={len(data)}\n")
    return data

# Base UEFA Country Coefficient points from 25/26 season (Top = England 117.408)
TOP_COEFF = 117.408
LEAGUE_WEIGHTS = {
    "Premier League": 117.408 / TOP_COEFF, # 1.000
    "Serie A": 99.946 / TOP_COEFF,         # 0.851
    "La Liga": 96.359 / TOP_COEFF,         # 0.821
    "Bundesliga": 92.331 / TOP_COEFF,      # 0.786
    "Ligue 1": 82.712 / TOP_COEFF,         # 0.705
    "Championship": 0.400,                 # Approximation for tier 2
    # Fallbacks just in case
    "ENG-Premier League": 117.408 / TOP_COEFF,
    "ITA-Serie A": 99.946 / TOP_COEFF,
    "ESP-La Liga": 96.359 / TOP_COEFF,
    "GER-Bundesliga": 92.331 / TOP_COEFF,
    "FRA-Ligue 1": 82.712 / TOP_COEFF,
    "ENG-Championship": 0.400
}

def calculate_weighted_impact(target_player, league_peers):
    pos_group = target_player.get('pos_group', 'MID')
    
    if pos_group in ('Forward', 'ST', 'Striker', 'Winger'):
        metrics = [('shots', 0.5), ('big_chances', 0.3), ('touches_in_box', 0.2)]
        composition = "Based on: Shots, Big Chances, Touches in Box"
    elif pos_group in ('Defender', 'DEF', 'Center-Back', 'Full-Back'):
        metrics = [('defensive_actions', 0.5), ('aerial_duels_won', 0.3), ('progressive_passes', 0.2)]
        composition = "Based on: Defensive Actions, Aerial Duels Won, Progressive Passes"
    else:
        # Default to MID / Creators
        metrics = [('xT_p90', 0.5), ('key_passes', 0.3), ('progressive_passes', 0.2)]
        composition = "Based on: xT, Key Passes, Progressive Passes"

    # Filter peers by matches_processed >= 10 (approx 900 mins)
    valid_peers = [p for p in league_peers if p.get('matches_processed', 0) >= 10]
    if not valid_peers:
        valid_peers = league_peers
        
    projected_impact = 0.0
    
    for metric, weight in metrics:
        vals = []
        for p in valid_peers:
            v = p.get('per_90', {}).get(metric)
            if v is not None:
                vals.append(v)
        
        target_val = target_player.get('per_90', {}).get(metric, 0)
        
        if len(vals) == 0:
            continue
            
        median_val = statistics.median(vals)
        deviations = [abs(x - median_val) for x in vals]
        mad = statistics.median(deviations) if deviations else 0.0
        
        if mad == 0:
            m_z = 0.0
        else:
            m_z = (0.6745 * (target_val - median_val)) / mad
            
        m_z = max(-4.0, min(4.0, m_z))
        projected_impact += m_z * weight
        
    return projected_impact, composition

@router.get("/league-projection")
async def get_league_projection(
    player_name: str = Query(..., min_length=2),
    season: str = Query(default="2025/2026"),
    metric: str = Query(default="xT_p90"),
    peer_filter: bool = Query(default=False),
    _user=Depends(get_current_user),
    db: AsyncIOMotorDatabase | None = Depends(get_db),
):
    if db is None:
        raise HTTPException(status_code=503, detail="DB unavailable")

    # 1. Fetch Target Player
    target_docs = await db.player_spatial_profiles.find({
        "player_name": {"$regex": f"^{player_name}$", "$options": "i"},
        "season": season
    }, {"player_name": 1, "pos_group": 1, "league": 1, "style_cluster": 1, "per_90": 1, "matches_processed": 1}).sort("matches_processed", -1).limit(1).to_list(1)

    if not target_docs:
        raise HTTPException(status_code=404, detail="Target player not found")
        
    target_doc = target_docs[0]

    target_val = target_doc.get("per_90", {}).get(metric)
    # Support combined metric "progressive_actions"
    if metric == "progressive_actions":
        target_val = target_doc.get("per_90", {}).get("progressive_passes", 0) + target_doc.get("per_90", {}).get("progressive_carries", 0)

    if target_val is None:
        raise HTTPException(status_code=400, detail=f"Metric {metric} not found for player")

    pos_group = target_doc.get("pos_group")
    cluster_label = None
    if peer_filter and "style_cluster" in target_doc:
        cluster_label = target_doc["style_cluster"].get("cluster_label")

    # 2. Build Query for comparison pool
    query = {
        "season": season,
        "pos_group": pos_group,
        "league": {"$in": list(LEAGUE_WEIGHTS.keys())}
    }
    if peer_filter and cluster_label:
        query["style_cluster.cluster_label"] = cluster_label

    # 3. Fetch all peers
    cursor = db.player_spatial_profiles.find(query, {"player_name": 1, "league": 1, "per_90": 1, "matches_processed": 1})
    peers = await cursor.to_list(length=5000)

    # 4. Group by league
    league_data = {}
    for p in peers:
        l = p.get("league")
        
        # Standardize league name
        if l.startswith("ENG-"): l = l.replace("ENG-", "")
        elif l.startswith("ITA-"): l = l.replace("ITA-", "")
        elif l.startswith("ESP-"): l = l.replace("ESP-", "")
        elif l.startswith("GER-"): l = l.replace("GER-", "")
        elif l.startswith("FRA-"): l = l.replace("FRA-", "")

        if l not in LEAGUE_WEIGHTS:
            continue
            
        if l not in league_data:
            league_data[l] = []
        league_data[l].append(p)

    # 5. Calculate Distributions
    results = []
    target_clean_name = target_doc.get("player_name")
    global_composition = "Based on: Default"

    # Ensure leagues are returned in order of weight
    sorted_leagues = sorted(list(league_data.keys()), key=lambda x: LEAGUE_WEIGHTS.get(x, 0), reverse=True)

    LEAGUE_POINTS = {
        "Premier League": 117.408,
        "Serie A": 99.946,
        "La Liga": 96.359,
        "Bundesliga": 92.331,
        "Ligue 1": 82.712,
        "Championship": 46.963, 
        "ENG-Premier League": 117.408,
        "ITA-Serie A": 99.946,
        "ESP-La Liga": 96.359,
        "GER-Bundesliga": 92.331,
        "FRA-Ligue 1": 82.712,
        "ENG-Championship": 46.963
    }

    for l in sorted_leagues:
        data = league_data[l]
        if len(data) < 2:
            continue
            
        vals = []
        for d in data:
            val = d.get("per_90", {}).get(metric)
            if metric == "progressive_actions":
                val = d.get("per_90", {}).get("progressive_passes", 0) + d.get("per_90", {}).get("progressive_carries", 0)
            if val is not None:
                vals.append((d.get("player_name"), val))
                
        if len(vals) < 2:
            continue
            
        v_only = [v[1] for v in vals]
        median_val = statistics.median(v_only)
        deviations = [abs(x - median_val) for x in v_only]
        mad = statistics.median(deviations) if deviations else 0.0
        
        weight = LEAGUE_WEIGHTS[l]
        
        players = []
        for name, val in vals:
            if name.lower() == target_clean_name.lower():
                continue
                
            if mad == 0:
                raw_z = 0.0
            else:
                raw_z = (0.6745 * (val - median_val)) / mad
                
            raw_z = max(-4.0, min(4.0, raw_z))
            trans_z = raw_z * weight
            players.append({
                "player_name": name,
                "raw_value": val,
                "z_score": raw_z,
                "translated_z_score": trans_z,
                "is_target": False
            })
            
        if mad == 0:
            target_raw_z = 0.0
        else:
            target_raw_z = (0.6745 * (target_val - median_val)) / mad
            
        target_raw_z = max(-4.0, min(4.0, target_raw_z))
        target_trans_z = target_raw_z * weight
        players.append({
            "player_name": target_clean_name,
            "raw_value": target_val,
            "z_score": target_raw_z,
            "translated_z_score": target_trans_z,
            "is_target": True
        })
        
        projected_impact, comp = calculate_weighted_impact(target_doc, data)
        global_composition = comp
        
        results.append({
            "league": l,
            "league_weight": weight,
            "league_points": LEAGUE_POINTS.get(l, 0),
            "projected_impact": projected_impact,
            "mean": median_val,
            "std": mad,
            "players": players
        })

    return {
        "metric": metric,
        "target_player": target_clean_name,
        "target_raw_value": target_val,
        "pos_group": pos_group,
        "peer_filter_active": peer_filter,
        "cluster_label": cluster_label,
        "impact_composition": global_composition,
        "leagues": results
    }


