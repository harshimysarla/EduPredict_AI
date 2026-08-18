"""MongoDB connection module for EduPredict AI.

Provides MongoDB client, database connection, and collection handles for
portal datasets and student records. Includes automatic health check and fallback handling.
"""
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import settings

logger = logging.getLogger("edupredict.mongodb")

_mongo_client: Optional[MongoClient] = None
_mongo_db: Optional[Database] = None


def get_mongo_client() -> Optional[MongoClient]:
    """Return an active PyMongo client or None if connection fails."""
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client
    try:
        client = MongoClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
        )
        # Verify connection
        client.admin.command("ping")
        _mongo_client = client
        logger.info("Connected to MongoDB at %s", settings.MONGODB_URI)
        return _mongo_client
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as exc:
        logger.warning("MongoDB connection unavailable (%s). Falling back to SQL/local storage.", exc)
        return None


def get_mongo_db() -> Optional[Database]:
    """Return the MongoDB database instance or None."""
    global _mongo_db
    if _mongo_db is not None:
        return _mongo_db
    client = get_mongo_client()
    if client is None:
        return None
    _mongo_db = client[settings.MONGODB_DB_NAME]
    return _mongo_db


def get_portal_datasets_collection() -> Optional[Collection]:
    """Return handle for portal_datasets collection."""
    db = get_mongo_db()
    if db is None:
        return None
    return db["portal_datasets"]


def check_mongo_status() -> dict:
    """Return MongoDB status dict for health/meta endpoints."""
    try:
        client = get_mongo_client()
        if client is None:
            return {"status": "DISCONNECTED", "uri": settings.MONGODB_URI, "database": settings.MONGODB_DB_NAME, "records": 0}
        db = client[settings.MONGODB_DB_NAME]
        count = db["portal_datasets"].count_documents({})
        return {
            "status": "CONNECTED",
            "uri": settings.MONGODB_URI,
            "database": settings.MONGODB_DB_NAME,
            "records": count,
        }
    except Exception as exc:
        return {"status": "ERROR", "detail": str(exc), "uri": settings.MONGODB_URI}
