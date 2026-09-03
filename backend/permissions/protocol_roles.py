"""Protocol Role vocabulary (Issuer/Holder/Verifier) — P2, 2026-08-31.

Closes the gap `reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`'s
Credentials section names: "Issuer / Holder / Verifier roles ... IMPLEMENTED
conceptually, not as first-class permission roles" — `backend/did/`,
`backend/eudi/`'s DID/VC/EUDI code implements the W3C Verifiable
Credentials Data Model's three protocol roles, but `backend/permissions/
models.py`'s `Role` enum (the mission brief's own closed CVLN-role
vocabulary) never named them, and the two systems were never connected.

Deliberately NOT added as extra `Role` enum members: `Role` is documented
in `models.py` as "CVLN-wide roles, per the mission brief's table" — a
closed vocabulary. Inventing new entries for it without a route that
actually needs them would be exactly the "inventer des capacites" this
mission's own rule forbids (the same constraint `sdk/python/frekcore_sdk/
__init__.py`'s docstring applies to SDK scope). A fresh grep of every
DID/EUDI route confirms none of them call `permissions.engine.decide()`
today (`permissions/__init__.py`'s own docstring: "deliberately NOT wired
into any existing route in this phase") — Issuer/Holder/Verifier gate
nothing yet, so adding enforceable `Role` values for them now would add
scope with no route behind it.

What this DOES do instead: give the three protocol roles a real typed
vocabulary (`ProtocolRole`) plus an explicit, documented mapping to how
each is actually realized in this codebase today — so a future route that
needs to gate on one of these has a single reviewed reference point
instead of re-deriving the answer from scratch, and this gap is recorded
as *connected*, not left as tribal knowledge repeated in every report that
mentions it.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from .models import Role


class ProtocolRole(str, Enum):
    """The W3C Verifiable Credentials Data Model's three roles. See
    `backend/did/vc.py` (issuance) and `backend/eudi/routes.py` (OID4VCI
    issuance + SD-JWT verification) for where each is actually
    implemented in this codebase."""

    ISSUER = "issuer"
    HOLDER = "holder"
    VERIFIER = "verifier"


# Maps each protocol role to the CVLN `Role` that plays it today, where one
# exists. `None` means "not a per-subject Role grant in this codebase" —
# the role is realized structurally instead (see the per-entry comment).
# This is the documented answer for all three today, not a placeholder
# left to fill in later.
PROTOCOL_ROLE_TO_CVLN_ROLE: dict[ProtocolRole, Optional[Role]] = {
    # backend/did/vc.py's issue_credential() hardcodes issuer_did to
    # "did:frek:frekcore" — the platform itself issues every VC today, not
    # any per-subject actor, so no existing Role represents "the issuer".
    # If VC issuance is ever delegated to a per-subject actor (e.g. an
    # Academy teacher issuing certificates), the closest existing capability
    # match is Role.TEACHER or Role.EXECUTIVE (both already grant
    # Action.ISSUE, see permissions/engine.py's ROLE_CAPABILITIES) — but
    # that is a real design decision for whoever builds that feature, not
    # decided here.
    ProtocolRole.ISSUER: None,
    # The Holder is whichever FREK identity a VC/DID document names as its
    # subject — every identity is a potential Holder by default, so this
    # isn't a role grant at all, it's the base case ("no special role is
    # needed to hold a credential"), consistent with Role.ARTIST/STUDENT/
    # etc. all being *additive* capabilities layered on top of just having
    # a FREK-ID, not prerequisites for holding one.
    ProtocolRole.HOLDER: None,
    # backend/eudi/routes.py's verify-sdjwt endpoint and backend/did/
    # routes.py's resolution endpoints are public, unauthenticated reads —
    # anyone can verify a credential by design (that is the entire point of
    # a *verifiable* credential), so Verifier maps to no Role either.
    ProtocolRole.VERIFIER: None,
}


def cvln_role_for_protocol_role(protocol_role: ProtocolRole) -> Optional[Role]:
    """Returns the CVLN `Role` that currently plays this protocol role, or
    `None` if none does — see `PROTOCOL_ROLE_TO_CVLN_ROLE`'s own per-entry
    reasoning; `None` is the correct, documented answer for all three
    today, not an unfinished mapping."""
    return PROTOCOL_ROLE_TO_CVLN_ROLE[protocol_role]
