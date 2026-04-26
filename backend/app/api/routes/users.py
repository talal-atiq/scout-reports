from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=MessageResponse)
async def get_me(_user=Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="User profile route ready")
