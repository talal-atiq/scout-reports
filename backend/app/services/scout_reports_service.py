from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.transfermarkt_scraper import scrape_transfermarkt_bio


KNOWN_SCOUT_COLLECTIONS: tuple[str, ...] = (
    "reports",
    "training_analyses",
    "coaching_drills",
    "players_outfield_v2",
    "players_gk_v2",
    "season_distributions",
    "player_spatial_profiles",
    "player_current_season",
    "player_bio",
    "club_logos",
    "player_shot_data",
    "matches",
    "match_events",
    "match_player_stats",
)


def _to_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_json_safe(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_to_json_safe(item) for item in value]
    return value


def _strip_accents(text: str) -> str:
    """Removes accents from a string (e.g. Jérémy -> Jeremy)."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


async def get_collection_summaries(
    db: AsyncIOMotorDatabase,
    known_only: bool = True,
) -> list[dict[str, Any]]:
    available = await db.list_collection_names()
    target_names = sorted(set(available) & set(KNOWN_SCOUT_COLLECTIONS)) if known_only else sorted(available)

    summaries: list[dict[str, Any]] = []
    for name in target_names:
        estimated_count = await db[name].estimated_document_count()
        summaries.append({"name": name, "estimated_count": int(estimated_count)})
    return summaries


async def preview_collection_documents(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    limit: int,
) -> list[dict[str, Any]]:
    cursor = db[collection_name].find({}, limit=limit)
    docs = await cursor.to_list(length=limit)
    return [_to_json_safe(doc) for doc in docs]


def _season_aliases(season: str) -> list[str]:
    cleaned = season.strip()
    known_alias_map = {
        "25-26": ["25-26", "2025-26", "2025/26", "2025-2026", "2025/2026", "2025/2026"],
        "2025-26": ["25-26", "2025-26", "2025/26", "2025-2026", "2025/2026", "2025/2026"],
        "2025/26": ["25-26", "2025-26", "2025/26", "2025-2026", "2025/2026", "2025/2026"],
        "2025-2026": ["25-26", "2025-26", "2025/26", "2025-2026", "2025/2026", "2025/2026"],
        "2025/2026": ["25-26", "2025-26", "2025/26", "2025-2026", "2025/2026", "2025/2026"],
    }

    aliases = known_alias_map.get(cleaned, [cleaned])
    # Keep deterministic order while removing duplicates.
    return list(dict.fromkeys(aliases))


async def get_player_options(
    db: AsyncIOMotorDatabase,
    season: str,
    limit: int,
    search: str | None = None,
) -> list[dict[str, Any]]:
    season_values = _season_aliases(season)
    match_stage: dict[str, Any] = {"season": {"$in": season_values}}

    if search:
        match_stage["player_name"] = {"$regex": re.escape(search.strip()), "$options": "i"}

    pipeline: list[dict[str, Any]] = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {
                    "player_name": "$player_name",
                    "club": "$team"
                },
                "appearances": {"$sum": 1},
            }
        },
        {"$sort": {"appearances": -1, "_id.player_name": 1}},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "player_name": "$_id.player_name",
                "club": "$_id.club",
            }
        },
    ]

    return await db["match_player_stats"].aggregate(pipeline).to_list(length=limit)


async def get_player_header(
    db: AsyncIOMotorDatabase,
    player_name: str,
    season: str,
    club: str | None = None,
) -> dict[str, Any] | None:
    season_values = _season_aliases(season)
    player_regex = {"$regex": f"^{re.escape(player_name.strip())}$", "$options": "i"}

    # 1. Determine primary club FIRST to handle duplicate names (e.g. Idrissa Gueye)
    club_match: dict[str, Any] = {
        "player_name": player_regex,
        "season": {"$in": season_values},
    }
    if club:
        club_match["team"] = {"$regex": f"^{re.escape(club.strip())}$", "$options": "i"}

    club_pipeline: list[dict[str, Any]] = [
        {
            "$match": club_match
        },
        {
            "$group": {
                "_id": "$team",
                "appearances": {"$sum": 1},
                "actual_name": {"$first": "$player_name"}
            }
        },
        {"$sort": {"appearances": -1}},
        {"$limit": 1},
    ]
    club_rows = await db["match_player_stats"].aggregate(club_pipeline).to_list(length=1)
    
    primary_club = None
    actual_player_name = player_name
    matches_played = 0

    if not club_rows:
        # Fallback to spatial profiles if match data is missing
        spatial_doc = await db["player_spatial_profiles"].find_one({
            "player_name": player_regex,
            "season": {"$in": season_values}
        })
        if not spatial_doc:
            return None
        primary_club = spatial_doc.get("team") or spatial_doc.get("league")
        actual_player_name = spatial_doc.get("player_name", player_name)
    else:
        primary_club = club_rows[0]["_id"]
        actual_player_name = club_rows[0].get("actual_name", player_name)

        # 2. Get matches played ONLY for the primary club to avoid mixing stats
        summary_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "player_name": player_regex,
                    "team": primary_club,
                    "season": {"$in": season_values},
                }
            },
            {
                "$group": {
                    "_id": None,
                    "match_keys": {
                        "$addToSet": {
                            "$ifNull": ["$match_id", "$_id"],
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "matches_played": {"$size": "$match_keys"},
                }
            },
        ]
        summary_docs = await db["match_player_stats"].aggregate(summary_pipeline).to_list(length=1)
        matches_played = int(summary_docs[0]["matches_played"]) if summary_docs else 0

    player_bio = await db["player_bio"].find_one({"player_name": player_regex})
    
    if not player_bio or not player_bio.get("player_picture"):
        # Scrape on-demand
        scraped_data = await scrape_transfermarkt_bio(actual_player_name)
        if scraped_data:
            update_data = {
                "player_name": actual_player_name,
                "team": primary_club,
            }
            # Only override with non-null values from scraper
            for k, v in scraped_data.items():
                if v is not None:
                    update_data[k] = v
            
            await db["player_bio"].update_one(
                {"player_name": player_regex},
                {"$set": update_data},
                upsert=True
            )
            # Re-fetch after update
            player_bio = await db["player_bio"].find_one({"player_name": player_regex})

    player_bio = player_bio or {}

    nationality = player_bio.get("nation")
    preferred_foot = player_bio.get("preferred_foot")
    age_value = player_bio.get("age")
    height_value = player_bio.get("height_cm")
    player_picture = player_bio.get("player_picture")
    club_crest = player_bio.get("club_crest")
    nation_flag = player_bio.get("nation_flag")
    market_value = player_bio.get("market_value")

    spatial_profile = await db["player_spatial_profiles"].find_one({
        "player_name": player_regex,
        "season": {"$in": season_values}
    })
    spatial_profile = spatial_profile or {}
    
    position = spatial_profile.get("pos_group")
    if not preferred_foot:
        preferred_foot = spatial_profile.get("derived_foot")

    age: int | None
    if age_value is None:
        age = None
    else:
        age = int(round(float(age_value)))
        
    height: int | None
    if height_value is None:
        height = None
    else:
        height = int(round(float(height_value)))

    club = club if club is not None else primary_club or player_bio.get("team")
    club_filter = club

    # Known mismatches between our DB names and Understat names
    understat_aliases = {
        "Kylian Mbappé": "Kylian Mbappe-Lottin",
        "Kylian Mbappe": "Kylian Mbappe-Lottin",
        "Igor Thiago": "Thiago",
        "Vinícius Júnior": "Vinícius Júnior", 
        "Gabriel Magalhães": "Gabriel",
        "Gabriel Magalhaes": "Gabriel",
        "Jérémy Doku": "Jéremy Doku",
        "Martin Ødegaard": "Martin Odegaard",
    }
    
    # Use the alias if it exists, otherwise use the original name
    search_name = actual_player_name
    understat_search_name = understat_aliases.get(search_name, search_name)
    understat_regex = {"$regex": f"^{re.escape(understat_search_name.strip())}$", "$options": "i"}
    
    # Fallback to accent-stripped name
    stripped_name = _strip_accents(understat_search_name).strip()
    stripped_regex = {"$regex": f"^{re.escape(stripped_name)}$", "$options": "i"}

    # 3. Find Understat data, sorting by games descending to pick the prominent player if duplicate names exist
    understat_rows = await db["understat_league_cache"].aggregate(
        [
            {
                "$match": {
                    "season": {"$in": ["2025", "2025-26", "2025/26", "2025/2026"]},
                }
            },
            {"$unwind": "$players"},
            {
                "$match": {
                    "$or": [
                        {"players.player_name": understat_regex},
                        {"players.player_name": stripped_regex}
                    ]
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "league": "$league",
                    "season": "$season",
                    "fetched_at": "$fetched_at",
                    "goals": "$players.goals",
                    "assists": "$players.assists",
                    "xg": "$players.xG",
                    "xa": "$players.xA",
                    "yellow_cards": "$players.yellow_cards",
                    "red_cards": "$players.red_cards",
                    "games": {"$toInt": "$players.games"},
                    "team_title": "$players.team_title",
                }
            },
            {"$sort": {"games": -1}},
            {"$limit": 1},
        ]
    ).to_list(length=1)

    understat_doc = understat_rows[0] if understat_rows else {}
    goals_this_season = _to_int(understat_doc.get("goals"))
    assists_this_season = _to_int(understat_doc.get("assists"))
    xg_this_season = _to_float(understat_doc.get("xg"))
    xa_this_season = _to_float(understat_doc.get("xa"))
    yellow_cards = _to_int(understat_doc.get("yellow_cards"))
    red_cards = _to_int(understat_doc.get("red_cards"))
    understat_games = _to_int(understat_doc.get("games"))

    if club is None:
        club = understat_doc.get("team_title")

    confidence_sample = understat_games if understat_games is not None else matches_played

    if confidence_sample >= 20:
        confidence = "high"
        confidence_reason = "High sample size for 25-26 data"
    elif confidence_sample >= 8:
        confidence = "medium"
        confidence_reason = "Usable sample size for 25-26 data"
    else:
        confidence = "low"
        confidence_reason = "Small sample size for 25-26 data"

    return {
        "player_name": actual_player_name,
        "season": "25-26",
        "position": position,
        "nationality": nationality,
        "club": club,
        "preferred_foot": preferred_foot,
        "age": age,
        "height": height,
        "player_picture": player_picture,
        "club_crest": club_crest,
        "nation_flag": nation_flag,
        "market_value": market_value,
        "goals_this_season": goals_this_season,
        "assists_this_season": assists_this_season,
        "xg_this_season": xg_this_season,
        "xa_this_season": xa_this_season,
        "yellow_cards": yellow_cards,
        "red_cards": red_cards,
        "matches_played": matches_played,
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "last_updated": _to_json_safe(understat_doc.get("fetched_at")) if understat_doc else None,
    }
