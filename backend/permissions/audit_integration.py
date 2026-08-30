"""Glue: turn a permission Decision into an audit_trail.AuditEvent.

Kept in its own module so `engine.py` (and `audit_trail/`) have no hard
import-time dependency on each other — a caller that does not want audit
logging never needs to import this file.
"""

from __future__ import annotations

from typing import Optional

from audit_trail.models import AuditEvent

from .models import Decision, DecisionRequest


def decision_to_audit_event(
    request: DecisionRequest,
    decision: Decision,
    *,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> AuditEvent:
    """Completes the chain the mission brief specifies:
    subject -> role -> scope -> resource -> action -> decision -> audit event.
    """
    return AuditEvent(
        actor_frek_id=request.subject.frek_id,
        request_id=request_id,
        correlation_id=correlation_id,
        action=request.action.value,
        resource_type=request.resource.resource_type,
        resource_id=request.resource.resource_id,
        result="allow" if decision.allowed else "deny",
        reason=decision.reason,
    )
