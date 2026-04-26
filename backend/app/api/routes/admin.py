from fastapi import APIRouter, Depends

from app.api.dependencies import require_admin_key
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health", response_model=MessageResponse, dependencies=[Depends(require_admin_key)])
async def admin_health() -> MessageResponse:
    return MessageResponse(message="Admin routes ready")
