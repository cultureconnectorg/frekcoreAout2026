"""MongoAuditRecorder — append-only, MongoDB-backed AuditRecorder (Phase 3, Priority 5).

Same append-only guarantee as InMemoryAuditRecorder (Phase 2): the class
exposes only `record` (insert) and `all_events`/`recent_events` (read).
There is no `update`/`delete` method — a caller (including a future admin
route) has nothing to call to alter or remove a past entry short of a
direct database operation outside this class.

Requires a Motor database handle, set via `set_db()` — same pattern as
every other backend/*/routes.py module in this codebase
(backend/identity_engine/routes.py:set_db, etc.), so this can be wired into
server.py's existing `<module>_set_db(db)` startup sequence unchanged.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .models import AuditEvent

COLLECTION = "audit_trail_events"


class MongoAuditRecorder:
    def __init__(self, database: Any) -> None:
        self._db = database

    async def ensure_indexes(self) -> None:
        await self._db[COLLECTION].create_index("event_id", unique=True)
        await self._db[COLLECTION].create_index("actor_frek_id", sparse=True)
        await self._db[COLLECTION].create_index("resource_id", sparse=True)
        await self._db[COLLECTION].create_index([("timestamp", -1)])
        await self._db[COLLECTION].create_index("correlation_id", sparse=True)

    async def record(self, event: AuditEvent) -> AuditEvent:
        doc: Dict[str, Any] = event.model_dump()
        await self._db[COLLECTION].insert_one(doc)
        return event

    async def recent_events(
        self, limit: int = 100, actor_frek_id: Optional[str] = None
    ) -> Tuple[AuditEvent, ...]:
        query: Dict[str, Any] = {}
        if actor_frek_id:
            query["actor_frek_id"] = actor_frek_id
        cursor = (
            self._db[COLLECTION]
            .find(query, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
        docs: List[Dict[str, Any]] = await cursor.to_list(limit)
        return tuple(AuditEvent(**d) for d in docs)
