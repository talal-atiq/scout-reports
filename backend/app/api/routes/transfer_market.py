from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/transfer-market", tags=["transfer-market"])


@router.get("/health", response_model=MessageResponse)
async def transfer_market_health(_user=Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Transfer market routes ready")
