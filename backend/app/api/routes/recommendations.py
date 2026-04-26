from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/health", response_model=MessageResponse)
async def recommendations_health(_user=Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Recommendations routes ready")
