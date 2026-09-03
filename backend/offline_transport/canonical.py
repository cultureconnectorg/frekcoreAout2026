"""D4 -- deterministic canonical serialization + the envelope's signable
core.

CANONICAL_SERIALIZATION=TRUE, SIGNATURE_INPUT_DETERMINISTIC=TRUE,
UNORDERED_JSON_SIGNATURE_INPUT=FALSE: `canonical_json` is the exact same
formula already independently kept in `fk/packager.py:canonical_json`
and `notary/chain.py:_canonical_json` (`sort_keys=True,
separators=(",", ":")`) -- documented here as the same algorithm, a
third local copy following an established convention, not a new one.

The signable core is deliberately a STRICT SUBSET of `TransportEnvelope`:
everything the issuer commits to at CREATE/SIGN time (identity, refs,
claim/evidence, content hash, sequence, nonce, timing). Fields that are
receiver-side, mutable, and populated AFTER signing -- `signature`
itself, `transport_metadata` (attached at the TRANSPORT step),
`freshness`/`local_validation`/`sync_status`/`reconciled_at`/
`rejection_reason` (populated during RECEIVE/SYNC/RECONCILE) -- are
excluded on purpose: an envelope's signature must stay valid across its
entire offline journey even though those fields change underneath it.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from .models import TransportEnvelope

SIGNABLE_FIELDS = (
    "envelope_id",
    "schema_version",
    "issuer_id",
    "authority",
    "subject_ref",
    "subject_type",
    "object_ref",
    "object_type",
    "claim",
    "evidence",
    "content_binding_id",
    "creative_lifecycle_event_id",
    "relationship_id",
    "device_attestation",
    "sequence",
    "nonce",
    "previous_envelope_id",
    "issued_at",
    "expires_at",
)


def canonical_json(data: Any) -> str:
    """Same formula as fk/packager.py:canonical_json and
    notary/chain.py:_canonical_json -- sort_keys removes any dependency
    on Python dict/field insertion order, default=str handles any
    stray non-JSON-native value defensively."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def signable_core(envelope: TransportEnvelope) -> Dict[str, Any]:
    """The dict subset a signature actually covers -- see module
    docstring for exactly what is (and is deliberately not) included."""
    full = envelope.model_dump(mode="json")
    return {k: full[k] for k in SIGNABLE_FIELDS}


def signable_bytes(envelope: TransportEnvelope) -> bytes:
    return canonical_json(signable_core(envelope)).encode("utf-8")


def compute_content_hash(envelope: TransportEnvelope) -> str:
    """SHA-256 of the signable core -- the integrity axis, checkable by
    a receiver independently of whether they can also verify the
    signature (distinguishes payload content integrity from signature
    validity, per the mission's INTEGRITY section)."""
    return hashlib.sha256(signable_bytes(envelope)).hexdigest()
