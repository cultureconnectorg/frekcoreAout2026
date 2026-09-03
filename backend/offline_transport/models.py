"""D4 — Offline Proof Transport / Synchronization: data shapes.

Founder decision D4 (`docs/decisions/0007-d4-offline-proof-transport-
founder-decisions-implemented.md`; reconciliation record:
`reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` §D "D4 —
Offline Proof Transport"): PRESERVE_ADAPTER the historical FREK
multi-channel transmission vision (`backend/frek/nodes/
node07_transmission.py`) as a transport-independent, cryptographically
verifiable evidence-envelope and synchronization capability. FREKCORE
defines the trust semantics; transport technologies stay adapters:

    OFFLINE_TRUST_EQUALS_TRANSPORT_TECHNOLOGY = FALSE
    NFC/BLE/WIFI/QR/AUDIO/ULTRASOUND_IS_KERNEL_DEPENDENCY = FALSE
    CRYPTOGRAPHICALLY_VALID_EQUALS_CURRENTLY_AUTHORIZED = FALSE
    CRYPTOGRAPHICALLY_VALID_EQUALS_FULLY_VERIFIED = FALSE
    SIGNED_EQUALS_TRUSTED = FALSE
    RECEIVED_EQUALS_ACCEPTED = FALSE
    ACCEPTED_OFFLINE_EQUALS_FINAL_RECONCILIATION = FALSE
    WATERMARK_EQUALS_PROOF = FALSE

HISTORICAL DISCOVERY (this pass, read directly from
`backend/frek/nodes/node07_transmission.py` and the transmission section
of `backend/frek/routes_advanced.py` — not trusted from any prior
summary):

- **5 transport protocols declared**: BLE, NFC, WIFI_LOCAL, ULTRASONIC,
  CELLULAR (`TransmissionProtocol` enum, confirmed). QR is named in this
  state's own mission brief as a possible adapter but was **never** part
  of the historical vocabulary — added here as a genuinely new adapter,
  not a preserved one.
- **`TransmissionPacket` carries NO real cryptographic signature.**
  `signature_short` is `sha256_signal[:8]` — an 8-character prefix of a
  hash the caller supplies unverified, not a signature over the packet's
  own bytes, and nothing in the file ever verifies it against anything.
  There is no signing key, no verify function, no device identity check
  anywhere in this module. This is the single most important finding
  this state's own reading produced: the historical "packet" is an
  **unsigned envelope with a truncated hash reference**, not a
  cryptographically verifiable artifact — CRYPTOGRAPHICALLY_VALID never
  applied to it in the first place, so nothing about the historical code
  needed hardening so much as an entirely new trust layer added on top.
- **No nonce, no sequence number, no replay protection at all.**
  `timestamp_ms` is device/caller-declared and used for nothing but
  display.
- **`sync_status` has 3 values**: `"pending"`, `"synced"`, `"failed"` —
  no conflict, no rejection-with-reason, no revalidation-needed state.
- **`sync_pending()`'s own comment admits it is a simulation**
  (`"# Simulation de sync (en prod: appel API)"`) — it always succeeds
  unconditionally (the `except` branch is unreachable in practice), does
  no real network call, no authority re-check, no conflict detection, no
  idempotency-by-content dedup across distinct enqueued copies of the
  same packet.
- **Storage is pure Python-process memory** (`_pending_sync`,
  `_synced_packets` lists), wiped on every restart — identical to every
  other `backend/frek/` node's storage story this session has found
  (D1–D3).
- **The ultrasonic watermark is write-only.** `UltrasonicWatermark`
  FSK-modulates a truncated SHA-256 hash of the `frek_id` into an
  18kHz+ carrier at amplitude 0.01, and `to_dict()` asserts
  `"inaudible": frequency_hz >= 17000` — an unmeasured claim. **No
  decode/extraction function exists anywhere in this file.** A
  write-only watermark with no corresponding reader cannot function as
  a locator, identifier, or content binding in practice, regardless of
  what it claims — confirmed by reading the whole file, not assumed.
- **Zero authentication** on all 6 historical routes (`GET
  /transmission`, `/transmission/protocols`, `/transmission/protocol/
  {protocol}`, `POST /transmission/packet`, `POST /transmission/
  watermark`, `POST /transmission/sync}`) — confirmed by grep, consistent
  with D1–D3's own historical-route findings.

FAP REUSE (this pass): `frek_v3/reference_verifier/` is a real, complete,
independently tested (`test_frek_verifier.py`, run via
`python -m pytest`) reference implementation of the FREK Attestation
Protocol — binary parser/serializer, real ECDSA-P256 signing/
verification over a deterministic canonical message, a device registry
with `ACTIVE`/`REVOKED`/`SUSPENDED` status, and a full verification
pipeline (structural validation → device identity check → registry
lookup → signature verification → counter/replay check → nonce check →
firmware check). Per `docs/architecture/FAP_PROOF_ENGINE_RECONCILIATION.
md`, FAP is real and complete but **isolated** — no `backend/` endpoint
ever called it. This module is that first caller
(`offline_transport/fap_adapter.py`): it reuses FAP's real parser and
verifier directly (`REUSE_FAP=TRUE, DUPLICATE_FAP=FALSE`) for the
optional `device_attestation` layer, never reimplementing ECDSA,
counter/nonce/replay logic, or the canonical message encoding — those
stay exactly as FAP's own reference code defines them. `frek_v3/
reference_verifier/` is not a normal importable package (its own modules
use bare, non-relative imports, and its own test suite consumes it the
same way) — `fap_adapter.py` follows that same established consumption
pattern rather than inventing a new one.

MODERN REUSE AUDIT: `passport/keys.py`'s Ed25519 keypair
(`sign()`/`verify()`, already the real signer behind `.fk`'s own
`ProofLayer.signature` in `fk/packager.py`) is reused directly for the
envelope's own issuer-level signature — the same institutional key,
same convention, not a second signer. Canonical JSON serialization
(`sort_keys=True, separators=(",", ":")`) is already an established,
independently-kept convention in both `fk/packager.py:canonical_json`
and `notary/chain.py:_canonical_json` — this module's own
`canonical.py` follows the identical formula (documented as the same
algorithm, not a third invention). `proof_engine.evidence_semantics.
AuthorityStatus` (CURRENT/STALE/REVOKED/UNKNOWN) is reused directly for
offline status freshness — it already names exactly what the mission's
own "STATUS FRESHNESS" section asks for (its own STALE value's
docstring — "checked against a cached/offline state, may be outdated" —
is a verbatim match for the mission's illustrative "CACHED" state, so no
second enum was created for it).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from proof_engine.evidence_semantics import AuthorityStatus, Claim, Evidence


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TransportProtocol(str, Enum):
    """The historical 5, verbatim, plus 4 new ones this state's own
    mission names. None of these are a kernel dependency — see
    `adapters.py`."""

    # Historical (node07_transmission.py:TransmissionProtocol), preserved.
    BLE = "bluetooth_ble"
    NFC = "nfc"
    WIFI_LOCAL = "wifi_local"
    ULTRASONIC = "ultrasonic"
    CELLULAR = "cellular"
    # New this state, per the mission's TRANSPORT_ADAPTERS_MAY_INCLUDE.
    QR = "qr"
    LOCAL_FILE = "local_file"
    LOCAL_NETWORK = "local_network"
    DEVICE_TO_DEVICE = "device_to_device"


class LocalValidationStatus(str, Enum):
    """The mission's own named LOCAL_VALIDATION branch outcomes.
    CRYPTOGRAPHICALLY_VALID_EQUALS_FULLY_VERIFIED=FALSE: LOCALLY_
    ACCEPTABLE is the ceiling reachable offline -- it is never promoted
    to a final/verified state by this step alone."""

    INVALID = "invalid"
    CRYPTO_VALID_BUT_STATUS_STALE = "crypto_valid_but_status_stale"
    LOCALLY_ACCEPTABLE = "locally_acceptable"


class SyncStatus(str, Enum):
    """The mission's own named sync vocabulary. Historical `sync_status`
    ("pending"/"synced"/"failed") is a strict subset -- "failed" is a
    LEGACY_ALIAS of REJECTED, preserved in `adapters.py`'s compatibility
    mapping, never silently dropped."""

    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    REJECTED = "rejected"
    CONFLICT = "conflict"
    NEEDS_REVALIDATION = "needs_revalidation"


class DeviceAttestationScheme(str, Enum):
    NONE = "none"
    FAP_L2 = "fap_l2"


class DeviceAttestation(BaseModel):
    """Optional device-level attestation layer, structurally separate
    from the envelope's own issuer-level signature (two independent,
    stackable proof layers, per `FAP_PROOF_ENGINE_RECONCILIATION.md`'s
    own headline finding -- not two answers to the same question)."""

    scheme: DeviceAttestationScheme = DeviceAttestationScheme.NONE
    proof_hex: Optional[str] = Field(
        None,
        description="Raw FAP L2 proof, hex-encoded (283 bytes), when scheme=fap_l2.",
    )
    device_id_hex: Optional[str] = None


class FreshnessInfo(BaseModel):
    """Explicit status-freshness record -- an offline verifier must be
    able to answer WHEN status was last refreshed, from WHAT source,
    under WHAT TTL, and whether online revalidation is required.
    STALE authority state is never treated as fresh (service.py enforces
    this in `compute_local_validation`)."""

    status: AuthorityStatus = AuthorityStatus.UNKNOWN
    checked_at: Optional[str] = None
    source: Optional[str] = None
    ttl_seconds: Optional[int] = None

    def is_expired(self, *, now: Optional[datetime] = None) -> bool:
        if self.checked_at is None or self.ttl_seconds is None:
            return True
        now = now or datetime.now(timezone.utc)
        checked = datetime.fromisoformat(self.checked_at)
        return (now - checked).total_seconds() > self.ttl_seconds


class TransportEnvelope(BaseModel):
    """The canonical, transport-independent evidence envelope.
    Transport adapters may change framing (`transport_metadata`); they
    never change trust semantics -- everything above `transport_metadata`
    is part of the signed core (see `canonical.py:signable_payload`) and
    is therefore identical no matter which adapter carried the bytes.

    Composed of D6's real `Claim`/`Evidence` directly. May reference an
    existing D1 content binding, D2 lifecycle event, or D3 relationship
    (never re-executing any of their own logic -- D4_CONSUMES_D1/D2/D3=
    TRUE, D4_REIMPLEMENTS_D1/D2/D3=FALSE)."""

    envelope_id: str
    schema_version: str = "1.0.0"
    issuer_id: Optional[str] = Field(
        None,
        description="identity_engine holder frek_id, if issued by a holder session.",
    )
    authority: str = Field(..., description="'holder' or 'admin'.")

    subject_ref: str
    subject_type: Optional[str] = None
    object_ref: Optional[str] = None
    object_type: Optional[str] = None

    claim: Claim
    evidence: List[Evidence] = Field(default_factory=list)

    content_binding_id: Optional[str] = Field(
        None, description="D1 content_binding this envelope transports a reference to."
    )
    creative_lifecycle_event_id: Optional[str] = Field(
        None, description="D2 lifecycle event this envelope transports a reference to."
    )
    relationship_id: Optional[str] = Field(
        None, description="D3 relationship this envelope transports a reference to."
    )

    device_attestation: DeviceAttestation = Field(
        default_factory=lambda: DeviceAttestation()
    )

    content_hash: str = Field(..., description="SHA-256 of the signable core, hex.")
    signature: Optional[str] = Field(
        None, description="base64 Ed25519 signature, via passport.keys."
    )
    signature_algo: str = "ed25519"
    key_id: str = "frek-passport-v1"

    sequence: int = Field(..., description="Monotonic per issuer_id (or 'admin').")
    nonce: str = Field(
        ..., description="Hex nonce, unique per envelope -- replay control."
    )
    previous_envelope_id: Optional[str] = None

    issued_at: str = Field(default_factory=_now_iso)
    expires_at: Optional[str] = None

    transport_metadata: Dict[str, Any] = Field(default_factory=dict)

    freshness: FreshnessInfo = Field(default_factory=FreshnessInfo)
    local_validation: Optional[LocalValidationStatus] = None
    sync_status: SyncStatus = SyncStatus.PENDING
    reconciled_at: Optional[str] = None
    rejection_reason: Optional[str] = None

    created_at: str = Field(default_factory=_now_iso)

    def to_public_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")
