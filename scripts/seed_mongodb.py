"""Seed/sync local portal student datasets to MongoDB collection portal_datasets.

Seeds:
  - 24951A05B3 (MYSARLA HARSHITH)
  - 24951A05C3 (K. VISHNU VARDHAN)
  - 24951A05C5 (P. RITHVIK REDDY)
  - 24951A05B8 (V. ANANYA SHARMA)
"""
import os
import sys
import json

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _repo_root)
sys.path.insert(0, os.path.join(_repo_root, "backend"))

from app.core.config import settings
from app.core.mongodb import get_mongo_client, get_portal_datasets_collection
from app.data.students import PORTAL_DATASETS


def seed_mongodb():
    print(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
    client = get_mongo_client()
    if client is None:
        print("ERROR: Could not connect to MongoDB. Is MongoDB service running?")
        print(f"Connection URI tested: {settings.MONGODB_URI}")
        return False

    col = get_portal_datasets_collection()
    if col is None:
        print("ERROR: Could not get portal_datasets collection.")
        return False

    seeded_count = 0
    for ds in PORTAL_DATASETS:
        sid = ds.get("rollNumber") or ds.get("studentId") or ds.get("username")
        if not sid:
            continue
        res = col.update_one(
            {"studentId": sid},
            {"$set": ds},
            upsert=True,
        )
        name = (ds.get("profile") or {}).get("name") or ds.get("name") or sid
        print(f"  Synced student dataset to MongoDB -> {sid} ({name})")
        seeded_count += 1

    total_in_db = col.count_documents({})
    print(f"\nMongoDB Seed Complete! Synced {seeded_count} student datasets.")
    print(f"Total documents in '{settings.MONGODB_DB_NAME}.portal_datasets': {total_in_db}")
    return True


if __name__ == "__main__":
    seed_mongodb()
