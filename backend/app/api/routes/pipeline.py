from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/health", response_model=MessageResponse)
async def pipeline_health(_user=Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Pipeline routes ready")
