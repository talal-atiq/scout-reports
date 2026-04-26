from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user, get_db
from app.schemas.common import MessageResponse
from app.schemas.scout_reports import PlayerHeaderResponse, PlayerOption
from app.services.scout_reports_service import (
    get_collection_summaries,
    get_player_header,
    get_player_options,
    preview_collection_documents,
)

router = APIRouter(prefix="/scout-reports", tags=["scout-reports"])


@router.get("/health", response_model=MessageResponse)
async def scout_reports_health(
    _user=Depends(get_current_user),
    db: AsyncIOMotorDatabase | None = Depends(get_db),
) -> MessageResponse:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB connection unavailable",
        )
    return MessageResponse(message=f"Scout reports routes ready on DB: {db.name}")


@router.get("/collections")
async def list_scout_collections(
    known_only: bool = Query(default=True, description="Limit output to known StatScout collections"),
    _user=Depends(get_current_user),
    db: AsyncIOMotorDatabase | None = Depends(get_db),
) -> dict:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB connection unavailable",
        )

    collections = await get_collection_summaries(db=db, known_only=known_only)
    return {
        "database": db.name,
        "known_only": known_only,
        "count": len(collections),
        "collections": collections,
    }


@router.get("/collections/{collection_name}/preview")
async def preview_scout_collection(
    collection_name: str,
    limit: int = Query(default=10, ge=1, le=100),
    _user=Depends(get_current_user),
    db: AsyncIOMotorDatabase | None = Depends(get_db),
) -> dict:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB connection unavailable",
        )

    collection_names = await db.list_collection_names()
    if collection_name not in collection_names:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_name}' not found in database '{db.name}'",
        )

    documents = await preview_collection_documents(db=db, collection_name=collection_name, limit=limit)
    return {
        "database": db.name,
        "collection": collection_name,
        "limit": limit,
        "returned": len(documents),
        "documents": documents,
    }


@router.get("/players/options", response_model=list[PlayerOption])
async def list_player_options(
    season: str = Query(default="25-26"),
    limit: int = Query(default=200, ge=1, le=1000),
    search: str | None = Query(default=None),
    _user=Depends(get_current_user),
    db: AsyncIOMotorDatabase | None = Depends(get_db),
) -> list[PlayerOption]:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB connection unavailable",
        )

    return await get_player_options(db=db, season=season, limit=limit, search=search)


@router.get("/player-header", response_model=PlayerHeaderResponse)
async def get_scout_player_header(
    player_name: str = Query(..., min_length=2),
    season: str = Query(default="25-26"),
    club: str | None = Query(default=None),
    _user=Depends(get_current_user),
    db: AsyncIOMotorDatabase | None = Depends(get_db),
) -> PlayerHeaderResponse:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB connection unavailable",
        )

    header = await get_player_header(db=db, player_name=player_name, season=season, club=club)
    if header is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No 25-26 data found for player '{player_name}'",
        )

    return PlayerHeaderResponse(**header)
