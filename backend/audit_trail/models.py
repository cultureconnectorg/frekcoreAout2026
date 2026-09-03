"""AuditEvent — one entry in the append-only audit trail.

Field set matches the mission brief's minimum list exactly: actor, FREK-ID
si disponible, timestamp, request ID, correlation ID, action, resource,
result, reason si applicable.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

AuditResult = Literal["allow", "deny", "success", "failure"]


def _event_id() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=_event_id)
    actor_frek_id: Optional[str] = Field(
        default=None, description="FREK-ID of who performed the action, if known."
    )
    timestamp: str = Field(default_factory=_now_iso)
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    action: str = Field(
        ..., description="e.g. a permissions.Action value, or any other action name."
    )
    resource_type: str = Field(...)
    resource_id: Optional[str] = None
    result: AuditResult
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
