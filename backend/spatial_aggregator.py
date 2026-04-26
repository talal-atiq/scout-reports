"""
spatial_aggregator.py
---------------------
Reads all WhoScored event parquets for a league+season, groups events
by player, computes all spatial fields, and upserts documents to the
`player_spatial_profiles` MongoDB collection.

Usage (run from backend/):
    python etl/events/spatial_aggregator.py --league "Premier League" --season "2025/2026"
    python etl/events/spatial_aggregator.py --league "Premier League" --dry-run
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from rapidfuzz import fuzz

# -------------------------------------------------- Path setup ----------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = BACKEND_DIR / "data" / "events"


# -- Position group classifier (mirrors ImpactService) --

def classify_pos_group(pos: str) -> str:
    p = (pos or "").upper().replace(" ", "")
    # Split by comma and strictly use the first position (the tactical anchor)
    primary_pos = p.split(",")[0] if p else ""
    
    if "GK" in primary_pos: return "GK"
    if "FW" in primary_pos: return "FW"
    if "MF" in primary_pos: return "MF"
    if "DF" in primary_pos: return "DEF"
    return "MF"  # Default fallback


# -- Zone mapping constants --
# Pitch: 5 rows (y-axis, top->bottom) × 6 cols (x-axis, defensive->attacking)
# WhoScored x: 0 = own goal, 100 = opponent goal (per-team normalized)
# WhoScored y: absolute touchline (0/100). Flip applied (100-y) to normalise
# so that "Left Wing" is consistently the same side (home-team perspective).

PITCH_ZONE_ROW = {
    "Left Wing": 0,
    "Left Half Space": 1,
    "Centre": 2,
    "Right Half Space": 3,
    "Right Wing": 4,
}

# Depth zone → representative grid column (center of each third)
DEPTH_TO_COL = {
    "Defensive Third":  0,
    "Middle Third":     2,
    "Attacking Third":  4,
}

# Pass intent classification constants
WIDE_ZONES  = {"Left Wing", "Right Wing"}
HALF_SPACES = {"Left Half Space", "Right Half Space"}
DEPTH_ORDER = {"Defensive Third": 0, "Middle Third": 1, "Attacking Third": 2}

TOUCH_EVENT_TYPES = {
    "Pass", "Carry", "BallTouch", "TakeOn", "Goal",
    "SavedShot", "BlockedShot", "MissedShot", "ShotOnPost",
    "Tackle", "Interception", "Clearance", "BallRecovery",
    "Aerial", "Dispossessed", "KeeperPickup",
}

SHOT_EVENT_TYPES = {"Goal", "SavedShot", "BlockedShot", "MissedShot", "ShotOnPost"}

DEFENSIVE_EVENT_TYPES = {"Tackle", "Interception", "Clearance", "BallRecovery", "Block"}


def _x_to_col(x) -> int:
    """Map x coordinate (0-100, per-team) to column index 0-5."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 2
    if x < 17:  return 0
    if x < 34:  return 1
    if x < 50:  return 2
    if x < 67:  return 3
    if x < 83:  return 4
    return 5


def _y_to_row(y) -> int:
    """Map raw y coordinate to row index 0-4 (same flip as event_scraper)."""
    try:
        y = float(y)
    except (TypeError, ValueError):
        return 2
    y = 100 - y  # Same flip applied in event_scraper._pitch_zone
    if y < 20:  return 0
    if y < 37:  return 1
    if y < 63:  return 2
    if y < 80:  return 3
    return 4


def _zone_str_to_row(pitch_zone: str) -> int:
    return PITCH_ZONE_ROW.get(str(pitch_zone), 2)


def _x_to_depth(x) -> str:
    """Map x coordinate to depth zone label."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "Middle Third"
    if x < 34:  return "Defensive Third"
    if x < 67:  return "Middle Third"
    return "Attacking Third"


def _y_to_pitch_zone(y) -> str:
    """Map raw y coordinate to pitch zone label (same flip as event_scraper)."""
    try:
        y = float(y)
    except (TypeError, ValueError):
        return "Centre"
    y = 100 - y
    if y < 20:  return "Left Wing"
    if y < 37:  return "Left Half Space"
    if y < 63:  return "Centre"
    if y < 80:  return "Right Half Space"
    return "Right Wing"


# -------------------------------------------------- Pass intent classification ------------------------------------------------

def _classify_pass_intent(
    start_zone: str, start_depth: str,
    end_zone: str,   end_depth: str,
    xT_gain: float,  prog_dist: float,
) -> str:
    """Classify a single pass into one of 5 strategic archetypes."""
    delta_depth = DEPTH_ORDER.get(end_depth, 1) - DEPTH_ORDER.get(start_depth, 1)
    start_wide  = start_zone in WIDE_ZONES
    end_wide    = end_zone   in WIDE_ZONES

    if (start_wide != end_wide) and prog_dist > 20:
        return "Switch of Play"
    if end_depth == "Attacking Third" and xT_gain > 0.03:
        return "Final-Third Creator"
    if delta_depth >= 1 and prog_dist > 10 and xT_gain > 0.01:
        return "Progressive Line-Breaker"
    if end_zone in HALF_SPACES and xT_gain > 0.01:
        return "Half-Space Penetrator"
    return "Short Recycler"


def _build_pass_cluster_distribution(df: pd.DataFrame) -> dict:
    """
    Classify each successful pass into a strategic archetype and return
    the fractional distribution across the 5 clusters.
    """
    passes = df[(df["type"] == "Pass") & (df["outcomeType"] == "Successful")].copy()
    if len(passes) < 10:
        return {}

    passes["end_pitch_zone"] = passes["endY"].apply(_y_to_pitch_zone)
    passes["end_depth_zone"] = passes["endX"].apply(_x_to_depth)
    passes["xT_val"]   = pd.to_numeric(passes["xT"],        errors="coerce").fillna(0)
    passes["prog_val"] = pd.to_numeric(passes["prog_pass"],  errors="coerce").fillna(0)

    all_clusters = [
        "Short Recycler", "Half-Space Penetrator", "Switch of Play",
        "Progressive Line-Breaker", "Final-Third Creator",
    ]

    def _classify(r):
        return _classify_pass_intent(
            r["pitch_zone"], r["depth_zone"],
            r["end_pitch_zone"], r["end_depth_zone"],
            r["xT_val"], r["prog_val"],
        )

    passes["cluster"] = passes.apply(_classify, axis=1)
    counts = passes["cluster"].value_counts()
    total  = len(passes)
    return {c: round(float(counts.get(c, 0)) / total, 3) for c in all_clusters}


# -------------------------------------------------- Minutes played ------------------------------------------------------------

def _compute_minutes_played(player_name: str, player_df: pd.DataFrame,
                            all_df: pd.DataFrame) -> float:
    """
    Estimate total minutes played across all matches by checking
    SubstitutionOn/Off events. Returns float (e.g., 87.5 minutes per match).
    """
    total = 0.0
    for match_name in player_df["matchName"].unique():
        match_all = all_df[all_df["matchName"] == match_name]
        match_max = match_all["minute"].max()
        if pd.isna(match_max) or match_max <= 0:
            match_max = 90

        # SubstitutionOff for this player in this match
        sub_off = match_all[
            (match_all["type"] == "SubstitutionOff") &
            (match_all["playerName"] == player_name)
        ]["minute"]

        # SubstitutionOn for this player in this match
        sub_on = match_all[
            (match_all["type"] == "SubstitutionOn") &
            (match_all["playerName"] == player_name)
        ]["minute"]

        start_min = float(sub_on.min()) if len(sub_on) > 0 else 0.0
        end_min   = float(sub_off.min()) if len(sub_off) > 0 else float(match_max)

        total += max(0.0, end_min - start_min)

    return max(total, 1.0)  # Never divide by zero


# -- Grid computation --

def _empty_grid() -> list[list[float]]:
    return [[0.0] * 6 for _ in range(5)]


def _normalise_grid(grid: list[list[float]]) -> list[list[float]]:
    total = sum(v for row in grid for v in row)
    if total == 0:
        return grid
    return [[round(v / total, 6) for v in row] for row in grid]


def _build_heatmaps(df: pd.DataFrame) -> dict:
    """4 pre-computed 5×6 touch density grids."""
    grids = {
        "all":       _empty_grid(),
        "passes":    _empty_grid(),
        "carries":   _empty_grid(),
        "defensive": _empty_grid(),
    }

    for _, row in df.iterrows():
        event_type = row.get("type", "")
        pitch_zone = row.get("pitch_zone", "")
        r = _zone_str_to_row(pitch_zone)
        c = _x_to_col(row.get("x"))

        if event_type in TOUCH_EVENT_TYPES:
            grids["all"][r][c] += 1
        if event_type == "Pass":
            grids["passes"][r][c] += 1
        if event_type == "Carry":
            grids["carries"][r][c] += 1
        if event_type in DEFENSIVE_EVENT_TYPES:
            grids["defensive"][r][c] += 1

    return {k: _normalise_grid(v) for k, v in grids.items()}


# -------------------------------------------------- Pass vectors --------------------------------------------------------------

def _build_pass_vectors(df: pd.DataFrame, top_n: int = 10) -> list[dict]:
    """Top-N zone-to-zone pass vectors with integer grid coordinates for frontend rendering."""
    passes = df[df["type"] == "Pass"].copy()
    if len(passes) == 0:
        return []

    passes["end_pitch_zone"] = passes["endY"].apply(_y_to_pitch_zone)
    passes["end_depth_zone"] = passes["endX"].apply(_x_to_depth)
    passes["success"]  = passes["outcomeType"] == "Successful"
    passes["xT_val"]   = pd.to_numeric(passes["xT"],        errors="coerce").fillna(0)
    passes["prog_val"] = pd.to_numeric(passes["prog_pass"],  errors="coerce").fillna(0)

    groups = passes.groupby(
        ["pitch_zone", "depth_zone", "end_pitch_zone", "end_depth_zone"]
    )

    vectors = []
    for (sz, sd, ez, ed), grp in groups:
        successful = grp[grp["success"]]
        prog_successful = successful[successful["prog_val"] > 0]
        vectors.append({
            # Integer grid coords required by frontend components
            "from_row": PITCH_ZONE_ROW.get(str(sz), 2),
            "from_col": DEPTH_TO_COL.get(str(sd), 2),
            "to_row":   PITCH_ZONE_ROW.get(str(ez), 2),
            "to_col":   DEPTH_TO_COL.get(str(ed), 2),
            # String zone labels for pass intent classification
            "start_zone":  str(sz),
            "start_depth": str(sd),
            "end_zone":    str(ez),
            "end_depth":   str(ed),
            # Metrics
            "frequency":    int(len(grp)),
            "success_rate": round(float(grp["success"].mean()), 3),
            "avg_xT_gain":  round(float(successful["xT_val"].mean()), 4) if len(successful) > 0 else 0.0,
            "avg_prog_dist": round(float(prog_successful["prog_val"].mean()), 2) if len(prog_successful) > 0 else 0.0,
        })

    # Sort by Threat (xT) and Progression rather than just raw volume
    vectors.sort(key=lambda v: (v["avg_xT_gain"] * v["frequency"]) + (v["avg_prog_dist"] * 0.01 * v["frequency"]), reverse=True)
    return vectors[:top_n]


# -- Carry corridors --

def _build_carry_corridors(df: pd.DataFrame, top_n: int = 8) -> list[dict]:
    """Top-N progressive carry corridors with integer grid coordinates for frontend rendering."""
    carries = df[
        (df["type"] == "Carry") &
        (df["outcomeType"] == "Successful")
    ].copy()
    carries["prog_val"] = pd.to_numeric(carries["prog_carry"], errors="coerce").fillna(0)
    carries = carries[carries["prog_val"] > 3]
    if len(carries) == 0:
        return []

    carries["end_pitch_zone"] = carries["endY"].apply(_y_to_pitch_zone)
    carries["end_depth_zone"] = carries["endX"].apply(_x_to_depth)
    carries["xT_val"] = pd.to_numeric(carries["xT"], errors="coerce").fillna(0)

    groups = carries.groupby(
        ["pitch_zone", "depth_zone", "end_pitch_zone", "end_depth_zone"]
    )

    corridors = []
    for (sz, sd, ez, ed), grp in groups:
        corridors.append({
            # Integer grid coords required by frontend CarryCorridors component
            "from_row": PITCH_ZONE_ROW.get(str(sz), 2),
            "from_col": DEPTH_TO_COL.get(str(sd), 2),
            "to_row":   PITCH_ZONE_ROW.get(str(ez), 2),
            "to_col":   DEPTH_TO_COL.get(str(ed), 2),
            "start_zone":  str(sz),
            "start_depth": str(sd),
            "end_zone":    str(ez),
            "end_depth":   str(ed),
            "frequency":       int(len(grp)),
            "avg_prog_metres": round(float(grp["prog_val"].mean()), 2),
            "avg_xT_gain":     round(float(grp["xT_val"].mean()), 4),
        })

    corridors.sort(key=lambda c: c["frequency"], reverse=True)
    return corridors[:top_n]


# -- Defensive zones --

def _build_defensive_zones(df: pd.DataFrame) -> list[dict]:
    """
    Per-zone defensive action counts with pressing intensity and proactivity classification.
    Each zone now includes:
      - col / row: integer grid coordinates for frontend rendering
      - pressing_intensity_pct: pressures_won / pressures_attempted
      - action_class: "proactive" (Middle/Attacking Third) | "reactive" (Defensive Third)
    """
    def_events = df[df["type"].isin(DEFENSIVE_EVENT_TYPES)].copy()
    if len(def_events) == 0:
        return []

    challenges = df[df["type"] == "Challenge"].copy()
    if len(challenges) > 0:
        challenges = challenges[["pitch_zone", "depth_zone", "type", "outcomeType"]]
        def_events = pd.concat([def_events, challenges], ignore_index=True)

    zones: dict = {}
    for _, row in def_events.iterrows():
        pz  = str(row.get("pitch_zone", ""))
        dz  = str(row.get("depth_zone", ""))
        key = (pz, dz)
        if key not in zones:
            zones[key] = {
                "pitch_zone": pz,
                "depth_zone": dz,
                # Integer grid coords for frontend components
                "col": DEPTH_TO_COL.get(dz, 2),
                "row": PITCH_ZONE_ROW.get(pz, 2),
                "tackles":             0,
                "interceptions":       0,
                "clearances":          0,
                "ball_recoveries":     0,
                "blocks":              0,
                "pressures_attempted": 0,
                "pressures_won":       0,
            }
        t       = row.get("type", "")
        outcome = row.get("outcomeType", "")
        if t == "Tackle":
            zones[key]["tackles"] += 1
            zones[key]["pressures_attempted"] += 1
            if outcome == "Successful":
                zones[key]["pressures_won"] += 1
        elif t == "Interception":
            zones[key]["interceptions"] += 1
        elif t == "Clearance":
            zones[key]["clearances"] += 1
        elif t == "BallRecovery":
            zones[key]["ball_recoveries"] += 1
        elif t == "Block":
            zones[key]["blocks"] += 1
        elif t == "Challenge":
            zones[key]["pressures_attempted"] += 1

    # Compute derived fields per zone
    result = []
    for zone in zones.values():
        attempted = zone["pressures_attempted"]
        zone["pressing_intensity_pct"] = (
            round(zone["pressures_won"] / attempted, 3) if attempted > 0 else 0.0
        )
        # Proactive = won ball before danger arrived (middle/attacking third);
        # Reactive  = cleanup in own defensive third
        zone["action_class"] = (
            "proactive" if zone["depth_zone"] in ("Middle Third", "Attacking Third")
            else "reactive"
        )
        result.append(zone)

    return result


# -------------------------------------------------- Shot zones ----------------------------------------------------------------

def _build_shot_zones(df: pd.DataFrame) -> list[dict]:
    """Per-shot array for Shot Placement Chart."""
    shots = df[df["type"].isin(SHOT_EVENT_TYPES)].copy()
    result = []
    for _, row in shots.iterrows():
        gmy = pd.to_numeric(row.get("goal_mouth_y"), errors="coerce")
        gmz = pd.to_numeric(row.get("goal_mouth_z"), errors="coerce")
        xt  = pd.to_numeric(row.get("xT"), errors="coerce")
        result.append({
            "x": float(row.get("x", 0) or 0),
            "y": float(row.get("y", 0) or 0),
            "goal_mouth_y": round(float(gmy), 3) if not pd.isna(gmy) else None,
            "goal_mouth_z": round(float(gmz), 3) if not pd.isna(gmz) else None,
            "result": str(row.get("type", "")),
            "is_big_chance": bool(row.get("is_big_chance_shot", False)),
            "is_left_foot":  bool(row.get("is_left_foot", False)),
            "is_right_foot": bool(row.get("is_right_foot", False)),
            "is_header":     bool(row.get("is_header", False)),
            "xT": round(float(xt), 4) if not pd.isna(xt) else None,
            "minute": int(row.get("minute", 0) or 0),
        })
    return result


# -------------------------------------------------- xT zones -----------------------------------------------------------------

def _build_xt_zones(df: pd.DataFrame) -> dict:
    """
    5×6 grid of cumulative xT generated from each zone (pass+carry events).
    Also computes xT_per_touch_grid (efficiency mode): strips volume so scouts
    see *decision quality* independent of frequency.
    """
    grid        = _empty_grid()
    touch_counts: list[list[int]] = [[0] * 6 for _ in range(5)]

    # Touch counts per zone (all touch events)
    touches = df[df["type"].isin(TOUCH_EVENT_TYPES)].copy()
    if len(touches) > 0:
        touches["_r"] = touches["pitch_zone"].apply(_zone_str_to_row)
        touches["_c"] = touches["x"].apply(_x_to_col)
        for (r, c), grp in touches.groupby(["_r", "_c"]):
            touch_counts[int(r)][int(c)] = len(grp)

    # Cumulative xT per zone (successful pass + carry events)
    relevant = df[
        (df["type"].isin(["Pass", "Carry"])) &
        (df["outcomeType"] == "Successful")
    ].copy()
    relevant["xT_val"] = pd.to_numeric(relevant["xT"], errors="coerce").fillna(0)
    relevant = relevant[relevant["xT_val"] > 0]

    if len(relevant) > 0:
        relevant["_r"] = relevant["pitch_zone"].apply(_zone_str_to_row)
        relevant["_c"] = relevant["x"].apply(_x_to_col)
        for (r, c), grp in relevant.groupby(["_r", "_c"]):
            grid[int(r)][int(c)] = float(grp["xT_val"].sum())

    grid = [[round(v, 4) for v in row] for row in grid]

    # Efficiency grid: xT per touch — strips volume, shows decision quality
    efficiency_grid = [
        [round(grid[r][c] / max(1, touch_counts[r][c]), 5) for c in range(6)]
        for r in range(5)
    ]

    return {"grid": grid, "xT_per_touch_grid": efficiency_grid}


# -- Style fingerprint --

def _build_style_fingerprint(df: pd.DataFrame, minutes: float, padj_multiplier: float = 1.0) -> dict:
    """8 per-90 metrics that define the player's playing style."""
    per90 = minutes / 90.0

    carries_prog = df[
        (df["type"] == "Carry") & (df["outcomeType"] == "Successful") &
        (pd.to_numeric(df["prog_carry"], errors="coerce").fillna(0) > 3)
    ]

    def _p90(count):
        return round(count / per90, 3) if per90 > 0 else 0.0

    return {
        "key_passes_p90":          _p90(df["is_key_pass"].sum()),
        "crosses_p90":             _p90(df["is_cross"].sum()),
        "progressive_passes_p90":  _p90(
            ((df["type"] == "Pass") & (df["outcomeType"] == "Successful") &
             (pd.to_numeric(df["prog_pass"], errors="coerce").fillna(0) > 5)).sum()
        ),
        "progressive_carries_p90": _p90(len(carries_prog)),
        "long_balls_p90":          _p90(df["is_long_ball"].sum()),
        "through_balls_p90":       _p90(df["is_through_ball"].sum()),
        "defensive_actions_p90":   round(_p90(df["type"].isin(DEFENSIVE_EVENT_TYPES).sum()) * padj_multiplier, 3),
        "big_chances_p90":         _p90(df["is_big_chance"].sum()),
        "dispossessed_p90":        _p90((df["type"] == "Dispossessed").sum()),
        "turnovers_p90":           _p90((df["type"] == "Dispossessed").sum() + ((df["type"] == "Pass") & (df["outcomeType"] == "Unsuccessful")).sum()),
    }


# -- Event totals + per 90 --

def _build_event_totals_and_per90(df: pd.DataFrame, minutes: float, padj_multiplier: float = 1.0) -> tuple[dict, dict]:
    """Season event totals and per-90 normalised values."""
    per90 = minutes / 90.0

    def _count(mask) -> int:
        return int(mask.sum()) if hasattr(mask, "sum") else int(mask)

    def _p90(n: int) -> float:
        return round(n / per90, 3) if per90 > 0 else 0.0

    passes = df[df["type"] == "Pass"]
    passes_ok = passes[passes["outcomeType"] == "Successful"]
    carries = df[df["type"] == "Carry"]
    carries_ok = carries[carries["outcomeType"] == "Successful"]
    prog_pass_mask = (
        (df["type"] == "Pass") & (df["outcomeType"] == "Successful") &
        (pd.to_numeric(df["prog_pass"], errors="coerce").fillna(0) > 5)
    )
    prog_carry_mask = (
        (df["type"] == "Carry") & (df["outcomeType"] == "Successful") &
        (pd.to_numeric(df["prog_carry"], errors="coerce").fillna(0) > 3)
    )

    total_passes     = _count(df["type"] == "Pass")
    key_passes       = _count(df["is_key_pass"])
    crosses          = _count(df["is_cross"])
    prog_passes      = _count(prog_pass_mask)
    through_balls    = _count(df["is_through_ball"])
    box_entries_pass = _count(df["is_box_entry_pass"])
    total_carries    = _count(df["type"] == "Carry")
    prog_carries     = _count(prog_carry_mask)
    box_entries_carry = _count(df["is_box_entry_carry"])
    xT_total         = round(float(
        pd.to_numeric(df[df["type"].isin(["Pass","Carry"])]["xT"], errors="coerce").fillna(0).clip(lower=0).sum()
    ), 4)
    shots = _count(df["type"].isin(SHOT_EVENT_TYPES))
    big_chances      = _count(df["is_big_chance_shot"])
    def_actions      = _count(df["type"].isin(DEFENSIVE_EVENT_TYPES))
    switches         = _count(df["is_switch_of_play"])
    aerial_won       = _count((df["type"] == "Aerial") & (df["outcomeType"] == "Successful"))
    dribbles         = _count((df["type"] == "TakeOn") & (df["outcomeType"] == "Successful"))
    recoveries       = _count(df["type"] == "BallRecovery")
    wide_touches     = _count(df["pitch_zone"].isin(["Left Wing", "Right Wing"]))
    touches_in_box   = _count(df["is_touch_in_box"])
    tackles          = _count(df["type"] == "Tackle")
    interceptions    = _count(df["type"] == "Interception")
    clearances       = _count(df["type"] == "Clearance")
    
    # High Regains (Defensive actions in Attacking Third)
    high_regains     = _count((df["type"].isin(["BallRecovery", "Tackle", "Interception"])) & (df["depth_zone"] == "Attacking Third"))
    
    # True Tackle Win Rate
    tackles_attempted = _count(df["type"].isin(["Tackle", "Challenge"]))
    tackles_won = _count((df["type"].isin(["Tackle", "Challenge"])) & (df["outcomeType"] == "Successful"))
    tackle_win_pct = round(tackles_won / tackles_attempted * 100, 1) if tackles_attempted > 0 else 0.0

    # Pass accuracy
    pass_cmp_pct = round(len(passes_ok) / len(passes) * 100, 1) if len(passes) > 0 else 0.0

    totals = {
        "total_passes": total_passes,
        "key_passes": key_passes,
        "crosses": crosses,
        "progressive_passes": prog_passes,
        "through_balls": through_balls,
        "box_entries_pass": box_entries_pass,
        "total_carries": total_carries,
        "progressive_carries": prog_carries,
        "box_entries_carry": box_entries_carry,
        "xT_total": xT_total,
        "shots": shots,
        "big_chances": big_chances,
        "defensive_actions": def_actions,
        "switches_of_play": switches,
        "aerial_duels_won": aerial_won,
        "dribbles_completed": dribbles,
        "ball_recoveries": recoveries,
        "wide_zone_touches": wide_touches,
        "touches_in_box": touches_in_box,
        "tackles": tackles,
        "interceptions": interceptions,
        "clearances": clearances,
        "high_regains": high_regains,
        "tackle_win_pct": tackle_win_pct,
        "pass_completion_pct": pass_cmp_pct,
        "minutes_played": round(minutes, 1),
    }

    per90_metrics = {
        "key_passes":           _p90(key_passes),
        "crosses":              _p90(crosses),
        "progressive_passes":   _p90(prog_passes),
        "progressive_carries":  _p90(prog_carries),
        "through_balls":        _p90(through_balls),
        "box_entries":          _p90(box_entries_pass + box_entries_carry),
        "big_chances":          _p90(big_chances),
        "defensive_actions":    round(_p90(def_actions) * padj_multiplier, 3),
        "switches_of_play":     _p90(switches),
        "aerial_duels_won":     _p90(aerial_won),
        "dribbles":             _p90(dribbles),
        "ball_recoveries":      _p90(recoveries),
        "wide_zone_touches":    _p90(wide_touches),
        "touches_in_box":       _p90(touches_in_box),
        "tackles":              round(_p90(tackles) * padj_multiplier, 3),
        "interceptions":        round(_p90(interceptions) * padj_multiplier, 3),
        "clearances":           _p90(clearances),
        "high_regains":         _p90(high_regains),
        "tackle_win_pct":       tackle_win_pct,
        "shots":                _p90(shots),
        "xT_p90":               _p90(int(xT_total * 100)) / 100,
        "pass_completion_pct":  pass_cmp_pct,
    }

    return totals, per90_metrics


# -------------------------------------------------- Derived foot --------------------------------------------------------------

def _derive_foot(df: pd.DataFrame) -> tuple[str, float]:
    """Dominant foot from shot + pass foot qualifiers."""
    right = int(df["is_right_foot"].sum())
    left  = int(df["is_left_foot"].sum())
    total = right + left
    if total < 3:
        return "unknown", 0.0
    if right >= left:
        return "right", round(right / total, 2)
    return "left", round(left / total, 2)


# -- Player ID lookup & Fuzzy Matching --

def _build_player_lookup(db) -> dict[str, dict]:
    """
    Build {player_name_lower: {name, pos_group, team, player_id}} from players_outfield_v2.
    Uses the most recent season available for each player.
    """
    pipeline = [
        {"$sort": {"season": -1}},
        {"$group": {
            "_id": "$player",
            "pos": {"$first": "$pos"},
            "team": {"$first": "$team"},
            "player_id": {"$first": {"$toString": "$_id"}},
        }},
    ]
    lookup = {}
    for doc in db.players_outfield_v2.aggregate(pipeline):
        name = doc["_id"]
        if name:
            lookup[name.lower()] = {
                "name": name,
                "pos_group": classify_pos_group(doc.get("pos", "")),
                "team": doc.get("team", ""),
                "player_id": doc.get("player_id"),
            }
    return lookup


def _get_player_pos_group(ws_name: str, ws_team: str, lookup: dict, heatmaps: dict) -> str:
    """
    1. Exact string match (case insensitive)
    2. RapidFuzz fuzzy match with team-match boosting
    3. Spatial Fallback (derive from touch heatmap)
    """
    ws_name_lower = ws_name.lower()
    
    # 1. Exact Match
    if ws_name_lower in lookup:
        return lookup[ws_name_lower]["pos_group"]
        
    # 2. Fuzzy Match
    best_match = None
    best_score = 0
    for fb_name_lower, data in lookup.items():
        score = fuzz.token_sort_ratio(ws_name_lower, fb_name_lower)
        if score > 70:
            # Team bonus
            fb_team = data.get("team", "").lower()
            ws_t = ws_team.lower() if ws_team else ""
            if ws_t and fb_team and (ws_t in fb_team or fb_team in ws_t):
                score += 20
                
        if score > best_score:
            best_score = score
            best_match = data
            
    if best_match and best_score >= 85:
        return best_match["pos_group"]
        
    # 3. Spatial Fallback
    all_touches = heatmaps.get("all", [])
    if not all_touches or len(all_touches) != 5:
        return "MF"
        
    defensive_touches = sum(all_touches[r][c] for r in range(5) for c in range(2))
    midfield_touches = sum(all_touches[r][c] for r in range(5) for c in range(2, 4))
    attacking_touches = sum(all_touches[r][c] for r in range(5) for c in range(4, 6))
    
    if defensive_touches > midfield_touches and defensive_touches > attacking_touches:
        return "DEF"
    elif attacking_touches > midfield_touches and attacking_touches > defensive_touches:
        return "FW"
    else:
        return "MF"


# -- Main aggregation --

def _slugify(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def _load_parquets(league: str, season: str) -> Optional[pd.DataFrame]:
    """Load and concatenate all parquets for a league+season."""
    parquet_dir = DATA_DIR / _slugify(league) / _slugify(season)
    if not parquet_dir.exists():
        print(f"  [ERROR] Directory not found: {parquet_dir}")
        return None

    files = list(parquet_dir.glob("*.parquet"))
    if not files:
        print(f"  [ERROR] No parquet files in: {parquet_dir}")
        return None

    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_parquet(f))
        except Exception as e:
            print(f"  [WARN] Could not read {f.name}: {e}")

    if not dfs:
        return None

    combined = pd.concat(dfs, ignore_index=True)
    # Ensure boolean columns are bool dtype (sometimes read as object)
    bool_cols = [c for c in combined.columns if c.startswith("is_")]
    for col in bool_cols:
        combined[col] = combined[col].astype(bool, errors="ignore")

    print(f"  Loaded {len(files)} parquet(s) -- {len(combined):,} total events")
    return combined


def _build_player_profile(
    player_name: str,
    player_df: pd.DataFrame,
    all_df: pd.DataFrame,
    league: str,
    season: str,
    player_lookup: dict,
) -> Optional[dict]:
    """Build the full spatial profile document for one player."""
    if len(player_df) < 10:  # Skip players with almost no events (e.g. substitutes who played 2 mins)
        return None

    # Determine team (use most frequent team in events)
    team_counts = player_df["team"].value_counts()
    team = str(team_counts.index[0]) if len(team_counts) > 0 else ""

    # Determine matches played and last match date
    match_names = player_df["matchName"].unique()
    matches_processed = len(match_names)

    # Last match date: parse from matchName if possible, else use max minute
    last_match_date = None
    if "homeTeam" in player_df.columns:
        # Not directly available -- use match names count as proxy
        last_match_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Spatial computations
    heatmaps              = _build_heatmaps(player_df)
    
    # Position logic (Exact -> Fuzzy -> Spatial Fallback)
    pos_group = _get_player_pos_group(player_name, team, player_lookup, heatmaps)
    
    # Try to grab FBref player_id if exact match exists
    player_id = None
    if player_name.lower() in player_lookup:
        player_id = player_lookup[player_name.lower()].get("player_id")

    # Minutes played
    minutes = _compute_minutes_played(player_name, player_df, all_df)

    # Calculate Possession (Pass Ratio) for PAdj logic
    total_team_passes = 0
    total_opp_passes = 0
    for m in match_names:
        m_df = all_df[all_df["matchName"] == m]
        m_team_passes = len(m_df[(m_df["type"] == "Pass") & (m_df["team"] == team)])
        m_opp_passes = len(m_df[(m_df["type"] == "Pass") & (m_df["team"] != team)])
        total_team_passes += m_team_passes
        total_opp_passes += m_opp_passes
        
    team_possession = 50.0
    if (total_team_passes + total_opp_passes) > 0:
        team_possession = (total_team_passes / (total_team_passes + total_opp_passes)) * 100
        
    # PAdj Multiplier (StatsBomb style sigmoid adjustment)
    import math
    padj_multiplier = 2 / (1 + math.exp(-0.1 * (team_possession - 50))) if team_possession != 50.0 else 1.0

    # Remaining spatial computations
    pass_vectors          = _build_pass_vectors(player_df)
    carry_corridors       = _build_carry_corridors(player_df)
    defensive_zones       = _build_defensive_zones(player_df)
    shot_zones            = _build_shot_zones(player_df)
    xt_zones              = _build_xt_zones(player_df)
    fingerprint           = _build_style_fingerprint(player_df, minutes, padj_multiplier)
    totals, per90         = _build_event_totals_and_per90(player_df, minutes, padj_multiplier)
    derived_foot, foot_confidence = _derive_foot(player_df)
    pass_cluster_dist     = _build_pass_cluster_distribution(player_df)

    return {
        "player_name": player_name,
        "player_id": player_id,
        "team": team,
        "league": league,
        "season": season,
        "pos_group": pos_group,
        "matches_processed": matches_processed,
        "last_match_date": last_match_date,
        "last_updated": datetime.now(timezone.utc),

        "touch_heatmap":           heatmaps,
        "pass_vectors":            pass_vectors,
        "pass_cluster_distribution": pass_cluster_dist,
        "carry_corridors":         carry_corridors,
        "defensive_zones":         defensive_zones,
        "shot_zones":              shot_zones,
        "xT_zones":                xt_zones,
        "style_fingerprint":       fingerprint,

        # Filled by style_clusterer.py after KMeans
        "style_cluster": None,
        "rankings": {},
        "percentiles_2526": {},

        "derived_foot": derived_foot,
        "derived_foot_confidence": foot_confidence,
        "season_event_totals": totals,
        "per_90": per90,
    }


# -------------------------------------------------- Public API ----------------------------------------------------------------

def aggregate(
    league: str,
    season: str = "2025/2026",
    dry_run: bool = False,
    verbose: bool = True,
) -> dict:
    """
    Load parquets for league+season -> compute spatial profiles -> upsert to MongoDB.

    Returns summary dict: {total_players, upserted, skipped, errors}
    """
    print(f"\n'-' * 60")
    print(f"  Spatial Aggregator")
    print(f"  League : {league}")
    print(f"  Season : {season}")
    if dry_run:
        print(f"  Mode   : DRY RUN (no MongoDB writes)")
    print(f"'-' * 60\n")

    # Load all parquets
    print("[1/4] Loading parquets...")
    all_df = _load_parquets(league, season)
    if all_df is None:
        return {"total_players": 0, "upserted": 0, "skipped": 0, "errors": 0}

    # Remove empty player names and system events
    all_df = all_df[all_df["playerName"].notna() & (all_df["playerName"] != "")]

    # Connect to MongoDB (skip in dry run)
    db = None
    player_lookup = {}
    if not dry_run:
        print("[2/4] Connecting to MongoDB...")
        mongo_url = os.getenv("MONGODB_URL")
        db_name   = os.getenv("MONGODB_DB_NAME", "statscout_db")
        client    = MongoClient(mongo_url, serverSelectionTimeoutMS=15000)
        db        = client[db_name]
        print("      Connected. Building player position lookup...")
        player_lookup = _build_player_lookup(db)
        print(f"      {len(player_lookup):,} players in lookup")
    else:
        print("[2/4] Skipping MongoDB (dry run)")

    # Group by player
    print("[3/4] Computing spatial profiles...")
    players = all_df.groupby("playerName")
    total_players = len(players)
    print(f"      Found {total_players} unique players across all matches\n")

    ops = []
    skipped = errors = 0

    for player_name, player_df in players:
        if verbose:
            print(f"  [{len(ops)+skipped+errors+1:>3}/{total_players}] {player_name} "
                  f"({len(player_df)} events)")
        try:
            profile = _build_player_profile(
                player_name, player_df, all_df, league, season, player_lookup
            )
            if profile is None:
                skipped += 1
                continue

            ops.append(UpdateOne(
                {"player_name": player_name, "league": league, "season": season},
                {"$set": profile},
                upsert=True,
            ))
        except Exception as e:
            print(f"    [ERROR] {player_name}: {e}")
            errors += 1

    # Bulk write
    upserted = 0
    if not dry_run and ops:
        print(f"\n[4/4] Upserting {len(ops)} profiles to player_spatial_profiles...")
        result = db.player_spatial_profiles.bulk_write(ops, ordered=False)
        upserted = result.upserted_count + result.modified_count
        print(f"      Done: {result.upserted_count} inserted, {result.modified_count} updated")
    elif dry_run:
        upserted = len(ops)
        print(f"\n[4/4] DRY RUN -- would upsert {upserted} profiles")

    summary = {
        "total_players": total_players,
        "upserted": upserted,
        "skipped": skipped,
        "errors": errors,
    }

    print(f"\n'-' * 60")
    print(f"  AGGREGATION COMPLETE")
    print(f"  Players found    : {total_players}")
    print(f"  Profiles upserted: {upserted}")
    print(f"  Skipped (low ev.): {skipped}")
    print(f"  Errors           : {errors}")
    print(f"'-' * 60\n")

    return summary


# -------------------------------------------------- CLI -----------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aggregate WhoScored events into player spatial profiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python etl/events/spatial_aggregator.py --league "Premier League" --season "2025/2026"
  python etl/events/spatial_aggregator.py --league "La Liga" --dry-run
        """,
    )
    parser.add_argument("--league", required=True, help='League e.g. "Premier League"')
    parser.add_argument("--season", default="2025/2026", help='Season e.g. "2025/2026"')
    parser.add_argument("--dry-run", action="store_true", help="Compute without writing to MongoDB")
    parser.add_argument("--quiet", action="store_true", help="Less verbose output")
    args = parser.parse_args()

    summary = aggregate(
        league=args.league,
        season=args.season,
        dry_run=args.dry_run,
        verbose=not args.quiet,
    )
    sys.exit(1 if summary["errors"] > 0 else 0)