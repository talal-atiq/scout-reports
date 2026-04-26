from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user, get_db
from app.schemas.common import MessageResponse

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
    doc = await db.player_spatial_profiles.find_one({
        "player_name": {"$regex": f"^{player_name}$", "$options": "i"},
        "season": season
    }, {"_id": 0})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spatial profile not found for {player_name}",
        )
    return doc
