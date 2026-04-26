from pydantic import BaseModel


class PlayerOption(BaseModel):
    player_name: str
    club: str | None = None


class PlayerHeaderResponse(BaseModel):
    player_name: str
    season: str
    position: str | None = None
    nationality: str | None = None
    club: str | None = None
    player_picture: str | None = None
    club_crest: str | None = None
    nation_flag: str | None = None
    preferred_foot: str | None = None
    age: int | None = None
    height: int | None = None
    market_value: str | None = None
    goals_this_season: int | None = None
    assists_this_season: int | None = None
    xg_this_season: float | None = None
    xa_this_season: float | None = None
    yellow_cards: int | None = None
    red_cards: int | None = None
    matches_played: int
    confidence: str
    confidence_reason: str | None = None
    last_updated: str | None = None
