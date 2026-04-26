import pandas as pd
import sys
from pathlib import Path

# Add backend to path to import spatial_aggregator
BACKEND_DIR = Path("d:/scout-reports/backend")
sys.path.insert(0, str(BACKEND_DIR))

from spatial_aggregator import (
    _build_defensive_zones,
    _build_shot_zones,
    _build_carry_corridors,
    _compute_minutes_played
)

def test_roles():
    print("Loading Parquet data...")
    df1 = pd.read_parquet(BACKEND_DIR / "data" / "1911273.parquet")
    df2 = pd.read_parquet(BACKEND_DIR / "data" / "1911274.parquet")
    all_df = pd.concat([df1, df2], ignore_index=True)

    players = ["Leonardo Balerdi", "Mason Greenwood"]
    
    for player_name in players:
        player_df = all_df[all_df["playerName"] == player_name].copy()
        print(f"\n{'='*50}")
        print(f"ANALYZING: {player_name.upper()} ({len(player_df)} touches)")
        print(f"{'='*50}")
        
        minutes = _compute_minutes_played(player_name, player_df, all_df)
        
        # 1. Defensive Zones
        def_zones = _build_defensive_zones(player_df)
        total_tackles = sum(z['tackles'] for z in def_zones)
        total_interceptions = sum(z['interceptions'] for z in def_zones)
        total_clearances = sum(z['clearances'] for z in def_zones)
        
        print(f"\n[ DEFENSIVE PROFILE ]")
        print(f"Active Defensive Zones: {len(def_zones)}")
        print(f"Total Tackles: {total_tackles}")
        print(f"Total Interceptions: {total_interceptions}")
        print(f"Total Clearances: {total_clearances}")
        if def_zones:
            top_def = sorted(def_zones, key=lambda x: x['tackles'] + x['interceptions'] + x['clearances'], reverse=True)[0]
            print(f"Most Active Defensive Zone: {top_def['pitch_zone']} ({top_def['depth_zone']})")
        
        # 2. Attacking / Shot Zones
        shots = _build_shot_zones(player_df)
        print(f"\n[ ATTACKING PROFILE ]")
        print(f"Total Shots Taken: {len(shots)}")
        if shots:
            for s in shots:
                print(f"  -> Minute {s['minute']}: {s['result']} (Big Chance: {s['is_big_chance']})")
                
        # 3. Carry Corridors
        corridors = _build_carry_corridors(player_df, top_n=3)
        print(f"\n[ PROGRESSIVE CARRIES ]")
        if corridors:
            for c in corridors:
                print(f"  -> {c['start_zone']} to {c['end_zone']} | {c['frequency']} times (Avg {c['avg_prog_metres']}m)")
        else:
            print("  -> No progressive carries over 3m.")

if __name__ == "__main__":
    test_roles()
