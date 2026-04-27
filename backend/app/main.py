from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    admin,
    ai,
    auth,
    comparison,
    impact,
    match_analyzer,
    pie,
    pipeline,
    recommendations,
    scout_reports,
    spatial,
    transfer_market,
    users,
    watchlist,
)
from app.core.database import connect_to_mongo, disconnect_from_mongo
from app.core.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    # Hook for startup warmups such as percentile caches.
    yield
    await disconnect_from_mongo()


settings = get_settings()

app = FastAPI(
    title="StatScout API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = settings.api_v1_prefix

app.include_router(auth.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(recommendations.router, prefix=api_prefix)
app.include_router(comparison.router, prefix=api_prefix)
app.include_router(watchlist.router, prefix=api_prefix)
app.include_router(impact.router, prefix=api_prefix)
app.include_router(transfer_market.router, prefix=api_prefix)
app.include_router(pie.router, prefix=api_prefix)
app.include_router(pipeline.router, prefix=api_prefix)
app.include_router(spatial.router, prefix=api_prefix)
app.include_router(admin.router, prefix=api_prefix)
app.include_router(scout_reports.router, prefix=api_prefix)
app.include_router(match_analyzer.router, prefix=api_prefix)
app.include_router(ai.router, prefix=api_prefix)


@app.get("/")
async def root():
    return {"message": "StatScout backend is running"}
