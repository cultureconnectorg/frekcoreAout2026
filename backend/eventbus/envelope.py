"""EventEnvelope — the one shape every FREKCORE event must carry.

Mirrors the JSON Schema at backend/registry/events/event_registry.json
(`envelope_schema`), exposed publicly via `GET /api/v1/registry/events`.
Kept as a hand-written Pydantic model (not generated from the JSON Schema)
so it is directly usable/typed by producer code; `to_registry_schema_dict()`
below is checked against the JSON Schema in tests to keep both in sync
(Priority 14, contract tests).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


def _event_id() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventEnvelope(BaseModel):
    """A single FREKCORE domain event.

    Field set matches backend/registry/events/event_registry.json's
    envelope_schema exactly (kept in sync by
    backend/tests/test_eventbus.py::test_envelope_matches_registry_schema).
    """

    event_id: str = Field(default_factory=_event_id)
    event_type: str = Field(..., description="Canonical name, e.g. 'identity.created'.")
    event_version: str = Field(default="v1")
    occurred_at: str = Field(default_factory=_now_iso)
    producer: str = Field(
        ..., description="Module that emitted this event, e.g. 'identity_engine'."
    )
    subject: Optional[str] = Field(
        default=None, description="Primary FREK-ID this event concerns, if any."
    )
    correlation_id: Optional[str] = Field(
        default=None, description="Ties together multiple events from one request/flow."
    )
    causation_id: Optional[str] = Field(
        default=None,
        description="event_id of the event that directly caused this one, if any.",
    )
    payload: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(
        default="1.0.0", description="Version of the payload shape (not the envelope)."
    )
