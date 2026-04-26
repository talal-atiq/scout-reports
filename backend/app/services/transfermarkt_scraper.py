"""
Player bio scraper — uses TheSportsDB free public API (no key required).

Fields returned:
  player_picture, club_crest, nation_flag, age, preferred_foot (None — not
  available), nation, height_cm, market_value
"""
import logging
import re
from datetime import date

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://www.thesportsdb.com/api/v1/json/3"

# flagcdn.com codes for every nationality string TheSportsDB returns.
# Format: lowercase ISO 3166-1 alpha-2, or ISO 3166-2 subdivision for home nations.
_NATIONALITY_TO_FLAG: dict[str, str] = {
    "england": "gb-eng",
    "scotland": "gb-sct",
    "wales": "gb-wls",
    "northern ireland": "gb-nir",
    "republic of ireland": "ie",
    "ireland": "ie",
    "france": "fr",
    "germany": "de",
    "spain": "es",
    "italy": "it",
    "portugal": "pt",
    "netherlands": "nl",
    "belgium": "be",
    "brazil": "br",
    "argentina": "ar",
    "colombia": "co",
    "uruguay": "uy",
    "chile": "cl",
    "mexico": "mx",
    "united states": "us",
    "usa": "us",
    "canada": "ca",
    "nigeria": "ng",
    "ghana": "gh",
    "senegal": "sn",
    "ivory coast": "ci",
    "côte d'ivoire": "ci",
    "cameroon": "cm",
    "morocco": "ma",
    "egypt": "eg",
    "south africa": "za",
    "algeria": "dz",
    "tunisia": "tn",
    "croatia": "hr",
    "serbia": "rs",
    "poland": "pl",
    "denmark": "dk",
    "sweden": "se",
    "norway": "no",
    "switzerland": "ch",
    "austria": "at",
    "czech republic": "cz",
    "czechia": "cz",
    "slovakia": "sk",
    "hungary": "hu",
    "romania": "ro",
    "greece": "gr",
    "turkey": "tr",
    "russia": "ru",
    "ukraine": "ua",
    "japan": "jp",
    "south korea": "kr",
    "china": "cn",
    "australia": "au",
    "new zealand": "nz",
    "saudi arabia": "sa",
    "iran": "ir",
    "qatar": "qa",
    "ecuador": "ec",
    "peru": "pe",
    "venezuela": "ve",
    "bolivia": "bo",
    "paraguay": "py",
    "costa rica": "cr",
    "jamaica": "jm",
    "trinidad and tobago": "tt",
    "mali": "ml",
    "guinea": "gn",
    "guinea-bissau": "gw",
    "cape verde": "cv",
    "gabon": "ga",
    "democratic republic of congo": "cd",
    "dr congo": "cd",
    "congo": "cg",
    "angola": "ao",
    "mozambique": "mz",
    "zimbabwe": "zw",
    "zambia": "zm",
    "kenya": "ke",
    "tanzania": "tz",
    "ethiopia": "et",
    "finland": "fi",
    "iceland": "is",
    "israel": "il",
    "north macedonia": "mk",
    "albania": "al",
    "bosnia and herzegovina": "ba",
    "bosnia": "ba",
    "montenegro": "me",
    "slovenia": "si",
    "bulgaria": "bg",
    "luxembourg": "lu",
    "georgia": "ge",
    "armenia": "am",
    "azerbaijan": "az",
}


def _flag_url(nationality: str) -> str | None:
    code = _NATIONALITY_TO_FLAG.get(nationality.lower().strip())
    if code:
        return f"https://flagcdn.com/w40/{code}.png"
    return None


def _parse_height(height_str: str) -> float | None:
    """Extract cm from TheSportsDB height strings like '5 ft 10 in / 1.79 m'."""
    m = re.search(r"([\d.]+)\s*m\b", height_str)
    if m:
        try:
            return float(m.group(1)) * 100
        except ValueError:
            pass
    return None


def _age_from_dob(dob: str) -> int | None:
    """Calculate current age from an ISO date string like '2002-11-06'."""
    try:
        born = date.fromisoformat(dob)
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    except (ValueError, TypeError):
        return None


async def scrape_transfermarkt_bio(player_name: str) -> dict | None:
    """
    Fetch player bio from TheSportsDB public API.
    Makes up to 3 lightweight JSON requests; no scraping, no bot protection.
    """
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:

        # 1. Search for player by name
        search_resp = await client.get(
            f"{_BASE}/searchplayers.php",
            params={"p": player_name},
        )
        logger.info("SportsDB search '%s' -> HTTP %d", player_name, search_resp.status_code)
        if search_resp.status_code != 200:
            logger.warning("SportsDB search failed (%d) for '%s'", search_resp.status_code, player_name)
            return None

        players = (search_resp.json().get("player") or [])
        if not players:
            logger.warning("SportsDB: no results for '%s'", player_name)
            return None

        best = players[0]
        player_id = best.get("idPlayer")
        team_id = best.get("idTeam")
        logger.info("SportsDB: matched '%s' (id=%s, team=%s)", best.get("strPlayer"), player_id, best.get("strTeam"))

        # 2. Full player detail (height, signing value, images)
        detail_resp = await client.get(f"{_BASE}/lookupplayer.php", params={"id": player_id})
        if detail_resp.status_code != 200:
            logger.warning("SportsDB detail failed (%d) for player id %s", detail_resp.status_code, player_id)
            return None

        p = ((detail_resp.json().get("players") or [{}])[0])

        # 3. Team badge
        club_crest: str | None = None
        if team_id:
            team_resp = await client.get(f"{_BASE}/lookupteam.php", params={"id": team_id})
            if team_resp.status_code == 200:
                team_doc = (team_resp.json().get("teams") or [{}])[0]
                club_crest = team_doc.get("strBadge") or team_doc.get("strLogo")

        nationality = p.get("strNationality") or best.get("strNationality")
        age = _age_from_dob(p.get("dateBorn") or best.get("dateBorn", ""))
        height_cm = _parse_height(p.get("strHeight") or "")
        nation_flag = _flag_url(nationality) if nationality else None
        player_picture = p.get("strCutout") or p.get("strThumb") or best.get("strCutout") or best.get("strThumb")
        market_value: str | None = p.get("strSigning") or None

        result = {
            "player_picture": player_picture,
            "club_crest": club_crest,
            "nation_flag": nation_flag,
            "age": age,
            "preferred_foot": None,   # not in SportsDB; spatial profile fallback handles this
            "nation": nationality,
            "height_cm": height_cm,
            "market_value": market_value,
        }
        logger.info(
            "SportsDB OK for '%s': picture=%s age=%s height=%s value=%s flag=%s",
            player_name, bool(player_picture), age, height_cm, market_value, bool(nation_flag),
        )
        return result
