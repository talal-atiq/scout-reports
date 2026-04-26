from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/pie", tags=["pie"])


@router.get("/health", response_model=MessageResponse)
async def pie_health(_user=Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="PIE routes ready")
