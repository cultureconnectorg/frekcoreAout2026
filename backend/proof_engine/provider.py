"""ProofProvider — the interface future proof backends implement.

Today's only real backend is FREK-Chain + OpenTimestamps (backend/notary/,
backend/passport/) — this Protocol exists so a future adapter (a different
timestamping service, a different chain) can be swapped in without any
caller needing to change, matching the mission brief's "preparer une
abstraction avec adapters futurs" instruction. No second implementation is
added in this phase (there is nothing real to adapt yet) — see
`notary_adapter.py` for the one adapter that DOES exist, wrapping the real
notary module's output shape.
"""

from __future__ import annotations

from typing import Protocol

from .models import ProofReceipt


class ProofProvider(Protocol):
    def fingerprint(self, subject_id: str, data: bytes) -> ProofReceipt:
        """Compute a hash-only receipt. No chain, no signature, no anchor."""
        ...

    def upgrade(self, receipt: ProofReceipt) -> ProofReceipt:
        """Attempt to move a receipt to the next available proof state.

        Implementations must never downgrade `state` and must never return a
        receipt claiming a state stronger than the evidence they actually
        hold (Evidence First applies to the code, not just to reports).
        """
        ...
