from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from jose import jwt

from app.schemas.common import MessageResponse
from app.core.settings import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/health", response_model=MessageResponse)
async def auth_health() -> MessageResponse:
    return MessageResponse(message="Auth routes ready")


@router.post("/dev-login")
async def dev_login() -> dict[str, str]:
    settings = get_settings()
    if not settings.dev_login_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login is disabled",
        )

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": "dev@statscout.local",
        "role": "scout",
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return {
        "access_token": token,
        "token_type": "bearer",
    }
