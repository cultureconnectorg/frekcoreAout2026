"""D4 -- pure logic: local validation, replay/ordering/conflict
decisions. Kept free of FastAPI/Mongo/notary (same discipline as every
other D-state's own service.py) so this state's sharpest invariants are
unit-testable in isolation:

    CRYPTOGRAPHICALLY_VALID_EQUALS_FULLY_VERIFIED = FALSE
    OFFLINE_VERIFIED_EQUALS_ONLINE_STATUS_FRESH = FALSE
    ACCEPTED_OFFLINE_EQUALS_FINAL_RECONCILIATION = FALSE
"""

from __future__ import annotations

from typing import Optional, Sequence

from .models import FreshnessInfo, LocalValidationStatus, SyncStatus

# LEGACY_ALIAS mapping: the historical node07_transmission.py's own
# sync_status vocabulary ("pending"/"synced"/"failed") is a strict
# subset of this module's SyncStatus -- preserved, never silently
# dropped (HISTORICAL_TAXONOMY preservation, same discipline as D3's).
LEGACY_SYNC_STATUS_ALIASES = {
    "pending": SyncStatus.PENDING,
    "synced": SyncStatus.SYNCED,
    "failed": SyncStatus.REJECTED,
}


def compute_local_validation(
    *, signature_valid: bool, freshness: FreshnessInfo
) -> LocalValidationStatus:
    """The mission's own LOCAL_VALIDATION branch, computed structurally:

    - signature invalid                       -> INVALID
    - signature valid but authority not fresh  -> CRYPTO_VALID_BUT_STATUS_STALE
    - signature valid AND authority fresh      -> LOCALLY_ACCEPTABLE (the
      ceiling reachable offline -- never promoted further by this
      function alone; only SYNC/FINAL_RECONCILIATION can do that)."""
    if not signature_valid:
        return LocalValidationStatus.INVALID
    if freshness.is_expired() or freshness.status.value != "current":
        return LocalValidationStatus.CRYPTO_VALID_BUT_STATUS_STALE
    return LocalValidationStatus.LOCALLY_ACCEPTABLE


def is_replay(*, sequence: int, last_known_sequence: Optional[int]) -> bool:
    """A cryptographically valid OLD envelope must not be accepted as a
    new action (mission's REPLAY PROTECTION section)."""
    if last_known_sequence is None:
        return False
    return sequence <= last_known_sequence


def is_out_of_order(*, sequence: int, last_reconciled_sequence: Optional[int]) -> bool:
    """EVENT_3 arriving before EVENT_2: true whenever there is a gap
    between what has actually been reconciled and this envelope's own
    sequence -- the caller queues it (NEEDS_REVALIDATION-shaped wait,
    not silent reconciliation) rather than assuming network-order
    delivery."""
    if last_reconciled_sequence is None:
        return sequence != 1
    return sequence != last_reconciled_sequence + 1


def detect_conflict(
    *,
    existing_content_hash: Optional[str],
    incoming_content_hash: str,
) -> bool:
    """Same (issuer, sequence) slot, different payload -- a real
    conflict, never silently overwritten (mission's CONFLICTS section:
    "Do NOT automatically overwrite one side. Preserve evidence/
    history."). An identical resubmission (same hash) is idempotent,
    not a conflict."""
    if existing_content_hash is None:
        return False
    return existing_content_hash != incoming_content_hash


def legacy_sync_status(value: str) -> SyncStatus:
    """Maps the historical 3-value vocabulary onto this module's fuller
    one -- an unrecognized value fails loudly rather than silently
    defaulting, since a silent default here could misreport a
    conflict/rejection as pending."""
    if value in LEGACY_SYNC_STATUS_ALIASES:
        return LEGACY_SYNC_STATUS_ALIASES[value]
    return SyncStatus(value)


def dedupe_envelope_ids(envelope_ids: Sequence[str]) -> list:
    """Receiving/syncing the same envelope id multiple times must be
    safe -- order-preserving de-duplication for batch sync calls."""
    seen: set = set()
    out = []
    for eid in envelope_ids:
        if eid not in seen:
            seen.add(eid)
            out.append(eid)
    return out
