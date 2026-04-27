"""
style_clusterer.py
------------------
Reads all player_spatial_profiles for a league+season, runs KMeans (k=4)
on style_fingerprint vectors per position group, computes PCA coordinates,
calculates per-metric rankings within league+pos_group, adds percentiles_2526
to each profile, and writes season_distributions to MongoDB.

Usage (run from backend/):
    python etl/events/style_clusterer.py --league "Premier League" --season "2025/2026"
    python etl/events/style_clusterer.py --league "Premier League" --dry-run
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from scipy.stats import percentileofscore
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# -------------------------------------------------- Path setup ----------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

# -- Position-Specific K-Means Features --
POS_GROUP_CLUSTER_METRICS = {
    "FW": ["shots", "big_chances", "touches_in_box", "progressive_carries", "dribbles", "aerial_duels_won"],
    "MF": ["progressive_passes", "key_passes", "through_balls", "xT_p90", "turnovers_p90", "high_regains"],
    "DEF": ["tackles", "interceptions", "clearances", "aerial_duels_won", "progressive_passes", "progressive_carries"],
}

# Metrics to rank and compute distributions for (from per_90 + fingerprint)
RANKING_METRICS = [
    "key_passes",
    "crosses",
    "progressive_passes",
    "progressive_carries",
    "through_balls",
    "box_entries",
    "big_chances",
    "defensive_actions",
    "aerial_duels_won",
    "dribbles",
    "ball_recoveries",
    "touches_in_box",
    "tackles",
    "interceptions",
    "clearances",
    "shots",
    "xT_p90",
    "high_regains",
    "tackle_win_pct",
    "turnovers_p90",
    "dispossessed_p90",
    "pass_completion_pct",
]

# Metrics to compute percentiles for (expanded to 14+ elite metrics for Pizza Charts)
POS_GROUP_PERCENTILE_METRICS = {
    "Striker":   ["shots", "big_chances", "touches_in_box", "xT_p90", "key_passes", "progressive_carries", "dribbles", "box_entries", "turnovers_p90", "pass_completion_pct", "aerial_duels_won", "tackles", "high_regains", "defensive_actions"],
    "Winger":    ["dribbles", "progressive_carries", "crosses", "key_passes", "xT_p90", "shots", "touches_in_box", "box_entries", "turnovers_p90", "pass_completion_pct", "tackles", "interceptions", "high_regains", "defensive_actions"],
    "MF":        ["progressive_passes", "progressive_carries", "key_passes", "through_balls", "box_entries", "xT_p90", "turnovers_p90", "pass_completion_pct", "tackles", "interceptions", "high_regains", "tackle_win_pct", "aerial_duels_won", "defensive_actions"],
    "CenterBack": ["tackles", "interceptions", "clearances", "tackle_win_pct", "aerial_duels_won", "defensive_actions", "high_regains", "progressive_passes", "progressive_carries", "pass_completion_pct", "turnovers_p90", "xT_p90"],
    "Fullback":   ["crosses", "progressive_carries", "progressive_passes", "key_passes", "xT_p90", "dribbles", "tackles", "interceptions", "clearances", "tackle_win_pct", "pass_completion_pct", "defensive_actions"],
}

# -- Cluster label auto-generation --
DIMENSION_LABEL_MAP = {
    "key_passes":          "Creative",
    "crosses":             "Wide",
    "progressive_passes":  "Progressive",
    "progressive_carries": "Ball Carrier",
    "through_balls":       "Playmaker",
    "defensive_actions":   "Defensive",
    "big_chances":         "Goal Threat",
    "shots":               "Shooter",
    "touches_in_box":      "Poacher",
    "dribbles":            "Dribbler",
    "aerial_duels_won":    "Aerial Dominator",
    "xT_p90":              "Threat Creator",
    "turnovers_p90":       "High Risk",
    "high_regains":        "Pressing Trigger",
    "tackles":             "Ball Winner",
    "interceptions":       "Reader",
    "clearances":          "No-Nonsense",
}


def _auto_label(centroid: np.ndarray, metrics: list[str]) -> str:
    """Generate cluster label from top-2 fingerprint dimensions by centroid value."""
    sorted_dims = sorted(
        enumerate(centroid),
        key=lambda x: x[1],
        reverse=True,
    )
    # If the metric is negative like turnovers, lower is better, but here centroid is standardized
    # A high standard value means high volume. For labels, we just map it.
    top_labels = [DIMENSION_LABEL_MAP.get(metrics[i], metrics[i]) for i, _ in sorted_dims[:2]]
    return f"{top_labels[0]} / {top_labels[1]}"


# -- MongoDB connection --

def _get_db():
    url     = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DB_NAME", "statscout_db")
    client  = MongoClient(url, serverSelectionTimeoutMS=15000)
    return client[db_name]


# -- Per-position clustering --

def _cluster_pos_group(profiles: list[dict], pos_group: str) -> list[dict]:
    """
    Run KMeans (k=4) + PCA on style fingerprints for one position group.
    Returns updated profile dicts with style_cluster added.
    """
    if len(profiles) < 4:
        # Not enough players for 4 clusters -- assign all to cluster 0
        for p in profiles:
            p["style_cluster"] = {"cluster_id": 0, "cluster_label": "Mixed", "pca_x": 0.0, "pca_y": 0.0}
        return profiles

    metrics = POS_GROUP_CLUSTER_METRICS.get(pos_group, ["progressive_passes", "defensive_actions"])

    # Build feature matrix
    vectors = []
    for p in profiles:
        per90 = p.get("per_90", {})
        row = [float(per90.get(f, 0.0) or 0.0) for f in metrics]
        vectors.append(row)

    X = np.array(vectors, dtype=float)

    # Replace NaN with 0
    X = np.nan_to_num(X, nan=0.0)

    # Standardise before clustering
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # KMeans (k=4, multiple restarts for stability)
    n_clusters = min(4, len(profiles))
    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = kmeans.fit_predict(X_scaled)

    # PCA to 2D
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X_scaled)

    # Auto-generate cluster labels from centroids (in original space)
    # Inverse transform centroids to interpret them
    centroids_original = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_labels = [_auto_label(c, metrics) for c in centroids_original]

    for i, p in enumerate(profiles):
        cid = int(labels[i])
        p["style_cluster"] = {
            "cluster_id": cid,
            "cluster_label": cluster_labels[cid],
            "pca_x": round(float(coords[i, 0]), 4),
            "pca_y": round(float(coords[i, 1]), 4),
        }

    return profiles


def _classify_sub_role(p: dict, pos_group: str) -> str:
    """Classify players into tactical sub-roles (Striker/Winger, CenterBack/Fullback)."""
    per90 = p.get("per_90", {})
    
    if pos_group == "FW":
        # Strikers have higher box/shot presence; Wingers have higher carry/cross volume
        striker_score = float(per90.get("touches_in_box", 0)) + float(per90.get("shots", 0))
        winger_score = float(per90.get("progressive_carries", 0)) + float(per90.get("dribbles", 0)) + float(per90.get("crosses", 0))
        return "Striker" if striker_score >= winger_score else "Winger"
        
    if pos_group == "DEF":
        # Fullbacks have much higher wide zone presence and crosses
        wide_score = float(per90.get("wide_zone_touches", 0)) + float(per90.get("crosses", 0)) * 2
        # CenterBacks are focused on defensive purity
        return "Fullback" if wide_score > 8.0 else "CenterBack"
        
    return pos_group


# -------------------------------------------------- Rankings ------------------------------------------------------------------

def _compute_rankings(profiles: list[dict]) -> list[dict]:
    """
    For each metric in RANKING_METRICS, rank all profiles within the group.
    Adds {metric}_rank and {metric}_total to each profile's 'rankings' dict.
    """
    total = len(profiles)

    # Build metric arrays
    metric_values: dict[str, list] = {m: [] for m in RANKING_METRICS}
    for p in profiles:
        per90 = p.get("per_90", {})
        for m in RANKING_METRICS:
            v = per90.get(m)
            metric_values[m].append(float(v) if v is not None else 0.0)

    for p_idx, p in enumerate(profiles):
        rankings = {}
        per90 = p.get("per_90", {})
        for m in RANKING_METRICS:
            player_val = float(per90.get(m) or 0.0)
            all_vals   = metric_values[m]
            # Rank: 1 = best (highest value)
            rank = sum(1 for v in all_vals if v > player_val) + 1
            rankings[f"{m}_rank"]  = int(rank)
            rankings[f"{m}_total"] = int(total)
        p["rankings"] = rankings

    return profiles


# -- Percentile computation --

def _compute_percentiles(profiles: list[dict], pos_group: str) -> list[dict]:
    """
    Compute per-player percentile_2526 values against all peers in same pos_group.
    Uses Bayesian Gravity: Pulls percentiles toward 50% if minutes are low.
    """
    metrics = POS_GROUP_PERCENTILE_METRICS.get(pos_group, RANKING_METRICS)

    # Build value arrays
    metric_values: dict[str, list] = {}
    for m in metrics:
        vals = []
        for p in profiles:
            v = p.get("per_90", {}).get(m)
            vals.append(float(v) if v is not None else 0.0)
        metric_values[m] = vals

    # Bayesian Gravity Settings
    CONFIDENCE_TARGET = 1800 # 20 matches (approx half season) for full confidence

    for p_idx, p in enumerate(profiles):
        percentiles = {}
        per90 = p.get("per_90", {})
        
        # Calculate Confidence Score based on minutes played
        mins = p.get("season_event_totals", {}).get("minutes_played", 0)
        confidence = min(1.0, mins / CONFIDENCE_TARGET)
        
        for m in metrics:
            player_val = float(per90.get(m) or 0.0)
            all_vals   = metric_values[m]
            
            # For turnovers and dispossessed, lower is better
            if m in ["turnovers_p90", "dispossessed_p90"]:
                pct = 100.0 - percentileofscore(all_vals, player_val, kind="rank")
            else:
                pct = percentileofscore(all_vals, player_val, kind="rank")
            
            # Apply Bayesian Adjustment (Gravity towards 50)
            adjusted_pct = (pct * confidence) + (50.0 * (1.0 - confidence))
            percentiles[m] = float(round(adjusted_pct, 1))
            
        p["percentiles_2526"] = percentiles
        # Store metadata for frontend
        p["confidence_score"] = round(confidence, 2)

    return profiles


# -- Season distributions --

def _build_season_distribution(
    profiles: list[dict],
    pos_group: str,
    league: str,
    season: str,
) -> dict:
    """
    Compute position-group metric distributions for percentile lookup
    in the report snapshot service.
    Stores 10 percentile breakpoints (p10…p100) per metric.
    """
    metrics = POS_GROUP_PERCENTILE_METRICS.get(pos_group, RANKING_METRICS)
    distributions = {}

    for m in metrics:
        vals = []
        for p in profiles:
            v = p.get("per_90", {}).get(m)
            vals.append(float(v) if v is not None else 0.0)

        if not vals:
            continue

        arr = np.array(vals, dtype=float)
        distributions[m] = {
            "mean": round(float(arr.mean()), 4),
            "std":  round(float(arr.std()), 4),
            "min":  round(float(arr.min()), 4),
            "max":  round(float(arr.max()), 4),
            # 10 percentile breakpoints: 10th, 20th, … 100th
            "percentiles": [
                round(float(np.percentile(arr, p)), 4)
                for p in range(10, 101, 10)
            ],
        }

    return {
        "season": season,
        "league": league,
        "pos_group": pos_group,
        "player_count": len(profiles),
        "last_updated": datetime.now(timezone.utc),
        "distributions": distributions,
    }


# -- Main entry point --

def run(
    league: str = "Top 5",
    season: str = "2025/2026",
    dry_run: bool = False,
    verbose: bool = True,
) -> dict:
    """
    Run KMeans clustering + rankings + percentiles on all spatial profiles
    for the given league+season. Writes results back to MongoDB.

    Returns summary dict.
    """
    print(f"\n'-' * 60")
    print(f"  Style Clusterer")
    print(f"  League : {league}")
    print(f"  Season : {season}")
    if dry_run:
        print(f"  Mode   : DRY RUN")
    print(f"'-' * 60\n")

    print("[1/4] Connecting to MongoDB...")
    db = _get_db()

    # Load all profiles for this season
    query = {"season": season}
    if league and league.lower() not in ["all", "top 5", "top5"]:
        query["league"] = league

    print(f"[2/4] Loading spatial profiles (Query: {query})...")
    all_profiles = list(db.player_spatial_profiles.find(
        query,
        {"_id": 1, "player_name": 1, "pos_group": 1,
         "style_fingerprint": 1, "per_90": 1, "season_event_totals.minutes_played": 1},
    ))
    print(f"      Loaded {len(all_profiles)} profiles")

    if not all_profiles:
        print("  No profiles found -- run spatial_aggregator first.")
        return {"profiles_updated": 0, "distributions_written": 0}

    # Group by pos_group and filter by minutes played
    by_pos: dict[str, list] = {}
    MIN_MINUTES = 900 # Standard vetting threshold
    vetted_count = 0

    for p in all_profiles:
        # Check minutes played
        mins = p.get("season_event_totals", {}).get("minutes_played", 0)
        if mins < MIN_MINUTES:
            continue
            
        vetted_count += 1
        pg = p.get("pos_group", "CM")
        if pg not in by_pos:
            by_pos[pg] = []
        by_pos[pg].append(p)
    
    print(f"      Vetted {vetted_count} profiles (>{MIN_MINUTES} mins) for ranking pool")

    # Sub-Bucket classification (Splitting FWs into Strikers/Wingers, DEFs into CB/FB for fair comparisons)
    final_groups: dict[str, list] = {}
    for pos_group, group_profiles in by_pos.items():
        if pos_group in ["FW", "DEF"]:
            role_groups: dict[str, list] = {}
            for p in group_profiles:
                role = _classify_sub_role(p, pos_group)
                p["sub_role"] = role
                if role not in role_groups:
                    role_groups[role] = []
                role_groups[role].append(p)
            final_groups.update(role_groups)
        else:
            for p in group_profiles:
                p["sub_role"] = pos_group
            final_groups[pos_group] = group_profiles

    print(f"      Final Pools: {', '.join(f'{k}({len(v)})' for k, v in final_groups.items())}")

    # Process each pool
    print("\n[3/4] Clustering + ranking + percentiles per position pool...")
    all_ops: list[UpdateOne] = []
    dist_ops: list = []

    for pool_name, profiles in final_groups.items():
        if pool_name == "GK":
            continue

        if verbose:
            print(f"\n  [{pool_name}] {len(profiles)} players")

        # KMeans + PCA (use original group logic for sub-pools)
        if pool_name in ["Striker", "Winger"]: 
            pos_group_logic = "FW"
        elif pool_name in ["CenterBack", "Fullback"]:
            pos_group_logic = "DEF"
        else:
            pos_group_logic = pool_name
            
        profiles = _cluster_pos_group(profiles, pos_group_logic)
        
        # Rankings (within pool)
        profiles = _compute_rankings(profiles)
        
        # Percentiles (within pool + Bayesian Gravity)
        profiles = _compute_percentiles(profiles, pool_name)
        if verbose:
            print(f"    Percentiles computed for "
                  f"{len(POS_GROUP_PERCENTILE_METRICS.get(pool_name, RANKING_METRICS))} metrics")

        # Build update operations for profiles
        for p in profiles:
            from datetime import datetime, timezone
            all_ops.append(UpdateOne(
                {"_id": p["_id"]},
                {"$set": {
                    "style_cluster":      p.get("style_cluster"),
                    "rankings":           p.get("rankings", {}),
                    "percentiles_2526":   p.get("percentiles_2526", {}),
                    "sub_role":           p.get("sub_role"),
                    "confidence_score":   p.get("confidence_score", 1.0),
                    "last_clustered_at":  datetime.now(timezone.utc),
                }},
            ))

        # Build season distribution
        dist = _build_season_distribution(profiles, pool_name, league, season)
        dist_ops.append(dist)

    # Write to MongoDB
    profiles_updated = distributions_written = 0
    if not dry_run:
        print("\n[4/4] Writing results to MongoDB...")
        if all_ops:
            CHUNK_SIZE = 200
            total_modified = 0
            num_chunks = (len(all_ops) - 1) // CHUNK_SIZE + 1
            for i in range(0, len(all_ops), CHUNK_SIZE):
                chunk = all_ops[i: i + CHUNK_SIZE]
                result = db.player_spatial_profiles.bulk_write(chunk, ordered=False)
                total_modified += result.modified_count
                print(f"      Chunk {i // CHUNK_SIZE + 1}/{num_chunks}: {result.modified_count} updated")
            profiles_updated = total_modified
            print(f"      Total: {profiles_updated} profiles updated (cluster, rankings, percentiles)")

        for dist in dist_ops:
            db.season_distributions.update_one(
                {"season": dist["season"], "league": dist["league"], "pos_group": dist["pos_group"]},
                {"$set": dist},
                upsert=True,
            )
            distributions_written += 1
        print(f"      {distributions_written} season_distributions documents upserted")
    else:
        profiles_updated = len(all_ops)
        distributions_written = len(dist_ops)
        print(f"\n[4/4] DRY RUN -- would update {profiles_updated} profiles, "
              f"{distributions_written} distributions")

    summary = {
        "profiles_updated": profiles_updated,
        "distributions_written": distributions_written,
    }

    print(f"\n'-' * 60")
    print(f"  CLUSTERING COMPLETE")
    print(f"  Profiles updated    : {profiles_updated}")
    print(f"  Distributions written: {distributions_written}")
    print(f"'-' * 60\n")

    return summary


# -------------------------------------------------- CLI -----------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="KMeans clustering + rankings for player spatial profiles",
    )
    parser.add_argument("--league", default="Top 5", help='League e.g. "Premier League" or "Top 5"')
    parser.add_argument("--season", default="2025/2026", help='Season e.g. "2025/2026"')
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    run(
        league=args.league,
        season=args.season,
        dry_run=args.dry_run,
        verbose=not args.quiet,
    )