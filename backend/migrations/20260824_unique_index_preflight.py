"""Report duplicate values before a reviewed unique-index migration.

Usage:
    MONGO_URL=... DB_NAME=... python backend/migrations/20260824_unique_index_preflight.py

This command is read-only. It never drops indexes, modifies documents, or creates indexes.
It reports the exact collections used by Staff Scanner idempotency constraints.
"""
import os
import sys

from pymongo import MongoClient


TARGETS = (("scans", "client_uuid"), ("transactions", "client_uuid"))


def main() -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("MONGO_URL and DB_NAME are required", file=sys.stderr)
        return 2

    client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    try:
        db = client[db_name]
        has_duplicates = False
        for collection_name, field in TARGETS:
            duplicates = list(db[collection_name].aggregate([
                {"$match": {field: {"$type": "string"}}},
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
                {"$match": {"count": {"$gt": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 100},
            ]))
            print(f"{collection_name}.{field}: {len(duplicates)} duplicate group(s)")
            for duplicate in duplicates:
                print(f"  value={duplicate['_id']!r} count={duplicate['count']} ids={duplicate['ids']}")
            has_duplicates = has_duplicates or bool(duplicates)
        return 1 if has_duplicates else 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
