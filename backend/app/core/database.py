import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.settings import get_settings

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    global client, database

    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=3000)
    database = client[settings.mongodb_db_name]

    try:
        await client.admin.command("ping")
        logger.info("MongoDB connected")
    except Exception as exc:
        # Keep app booting for module development even if DB is temporarily unavailable.
        logger.warning("MongoDB ping failed: %s", exc)


async def disconnect_from_mongo() -> None:
    global client, database
    if client is not None:
        client.close()
    client = None
    database = None


def get_database() -> AsyncIOMotorDatabase | None:
    return database
