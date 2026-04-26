import pandas as pd
import sys
from pathlib import Path

# Add backend to path to import spatial_aggregator
BACKEND_DIR = Path("d:/scout-reports/backend")
sys.path.insert(0, str(BACKEND_DIR))

# Import specific functions from spatial_aggregator
from spatial_aggregator import (
    _build_heatmaps,
    _build_pass_vectors,
    _build_carry_corridors,
    _build_defensive_zones,
    _build_shot_zones,
    _build_xt_zones,
    _build_style_fingerprint,
    _build_event_totals_and_per90,
    _derive_foot,
    _build_pass_cluster_distribution,
    _compute_minutes_played
)

def analyze():
    # 1. Load Parquet files
    df1 = pd.read_parquet(BACKEND_DIR / "data" / "1911273.parquet")
    df2 = pd.read_parquet(BACKEND_DIR / "data" / "1911274.parquet")
    all_df = pd.concat([df1, df2], ignore_index=True)
    
    # 2. Pick a prominent player who played in these matches
    # Let's find the top player by event count
    player_counts = all_df["playerName"].value_counts()
    print("Top 5 players by event count in these two matches:")
    print(player_counts.head(5))
    
    # Pick the most active player
    target_player = player_counts.index[0]
    player_df = all_df[all_df["playerName"] == target_player].copy()
    
    print(f"\n--- Analyzing {target_player} ({len(player_df)} events) ---")
    
    # 3. Calculate Minutes Played (required for some functions)
    minutes = _compute_minutes_played(target_player, player_df, all_df)
    print(f"\n1. Minutes Played Calculation: {minutes} minutes")
    
    # 4. Heatmaps
    print(f"\n2. _build_heatmaps: Touch Density")
    heatmaps = _build_heatmaps(player_df)
    # Just show a small sample (the 'all' touches grid, first 2 rows)
    print("   'all' touch grid (first 2 rows of 5x6 matrix):")
    for row in heatmaps['all'][:2]:
        print("  ", row)
        
    # 5. Pass Vectors
    print(f"\n3. _build_pass_vectors: Zone-to-Zone Connections")
    vectors = _build_pass_vectors(player_df, top_n=3)
    for v in vectors:
        print(f"   {v['start_zone']} ({v['start_depth']}) -> {v['end_zone']} ({v['end_depth']}): {v['frequency']} passes (Success: {v['success_rate']*100}%)")
        
    # 6. Carry Corridors
    print(f"\n4. _build_carry_corridors: Progressive Runs")
    corridors = _build_carry_corridors(player_df, top_n=3)
    if not corridors:
        print("   No progressive carries > 3 meters found.")
    else:
        for c in corridors:
            print(f"   {c['start_zone']} -> {c['end_zone']}: {c['frequency']} carries (Avg: {c['avg_prog_metres']}m)")
            
    # 7. Defensive Zones
    print(f"\n5. _build_defensive_zones: Tackles & Pressing")
    def_zones = _build_defensive_zones(player_df)
    if not def_zones:
        print("   No defensive actions found.")
    else:
        print(f"   Found {len(def_zones)} active defensive zones.")
        # Show top zone by tackles
        top_def = sorted(def_zones, key=lambda x: x['tackles'], reverse=True)[0]
        print(f"   Top zone: {top_def['pitch_zone']} ({top_def['depth_zone']}) - {top_def['tackles']} tackles, Press intensity: {top_def['pressing_intensity_pct']}")

    # 8. Shot Zones
    print(f"\n6. _build_shot_zones: Shot Locations")
    shots = _build_shot_zones(player_df)
    print(f"   {len(shots)} shots found.")
    for s in shots:
        print(f"   Minute {s['minute']}: {s['result']} (xG: {s['xT']})")
        
    # 9. Style Fingerprint & Per-90
    print(f"\n7. _build_style_fingerprint & Totals")
    fingerprint = _build_style_fingerprint(player_df, minutes)
    print("   Fingerprint (p90):", fingerprint)
    
    totals, per90 = _build_event_totals_and_per90(player_df, minutes)
    print("   Pass Completion:", totals['pass_completion_pct'], "%")
    print("   Total xT Generated:", totals['xT_total'])
    
    # 10. Pass Cluster Distribution
    print(f"\n8. _build_pass_cluster_distribution: Passing Playstyle")
    pass_dist = _build_pass_cluster_distribution(player_df)
    print("   Distribution:", pass_dist)

if __name__ == "__main__":
    analyze()
