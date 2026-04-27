from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user, get_db
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/transfer-market", tags=["transfer-market"])


@router.get("/health", response_model=MessageResponse)
async def transfer_market_health(_user=Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Transfer market routes ready")

@router.get("/player")
async def get_transfer_market_player(
    player_name: str,
    _user=Depends(get_current_user),
    db=Depends(get_db)
):
    if db is None:
        raise HTTPException(status_code=503, detail="DB not available")
        
    doc = await db.transfer_market_data.find_one({"player": {"$regex": f"^{player_name}$", "$options": "i"}}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Player not found in TM data")
        
    return doc
