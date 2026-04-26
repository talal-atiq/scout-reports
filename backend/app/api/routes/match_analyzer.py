from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/match-analyzer", tags=["match-analyzer"])


@router.get("/analyze")
async def analyze_match_placeholder() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={"detail": "Match analyzer module is not implemented yet"},
    )
