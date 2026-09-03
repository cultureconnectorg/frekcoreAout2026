"""Identity Engine — routes API.

Endpoints publics :
- POST /identity/init                    -> bootstrap FREKIdentity (attache moments session_id)
- POST /identity/{frek_id}/register/begin      -> aussi le point d'entree RECOVERY (X-Admin-Key) [P2]
- POST /identity/{frek_id}/register/complete   -> idem — emet identity.recovered si recovery [P2]
- POST /identity/authenticate/begin       -> auth username-less (discovery)
- POST /identity/authenticate/complete    -> retourne session token
- GET  /identity/{frek_id}                -> vue publique safe
- GET  /identity/me                       -> identite courante via header X-FREK-Session
- POST /identity/link-object              -> associe un FK ou moment a l'identite
- GET  /identity/{frek_id}/objects        -> liste des objets attaches
- POST /identity/{frek_id}/revocation     -> revocation (titulaire ou admin) [P1]
- PATCH /identity/{frek_id}               -> mise a jour display_name/metadata [P1]
- POST /identity/{frek_id}/archive        -> archivage soft (titulaire ou admin) [P1]
- GET  /identity/search                   -> recherche/liste, admin uniquement [P1]
- POST /identity/{frek_id}/reconcile          -> MERGE non-destructif [P2]
- GET  /identity/{frek_id}/reconciliations    -> historique de reconciliation, public [P2]

P2 (2026-08-31): RECOVERY (docs/decisions/0003-identity-lifecycle-founder-
decisions-implemented.md §3) added an admin-key override to
register_begin/register_complete's existing "holder session required to
add a Passkey" check, closing the real gap that a holder who lost every
credential had no path back into their own identity. MERGE (same ADR §1)
added /reconcile — never a true merge, an append-only relationship record
between two frek_ids, neither of which is ever deleted or overwritten.

Priorite 1 items (revoke/update/archive) close the "MISSING since Phase 1"
finding in reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md's Identity
section — see docs/architecture/FREK_ID_RECONCILIATION.md for why these
are holder-initiated-by-default (matching this module's own /me,
/link-object pattern) rather than a literal port of frek_v1's
client-initiated revoke, which has no holder-session concept to port.

Note on the path: `frek_v1` already owns `POST /{frek_id}/revoke` at this
exact prefix (backend/frek_v1/identity.py, mounted before this router in
server.py — first-match-wins, silently, since FastAPI raises nothing on a
path+verb collision across routers). This module's endpoint is therefore
`POST /{frek_id}/revocation` (a noun, not a verb) to stay a live, distinct
route rather than dead code shadowed by frek_v1's. See Contradiction C1 in
reports/FREKCORE_CONTRADICTIONS.md and
docs/architecture/FREK_ID_RECONCILIATION.md for the full writeup — this
collision is concrete proof of C1's real-world impact, found while building
this feature.
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from .models import (
    IDENTITY_TYPES,
    Credential,
    FREKIdentity,
    InitIdentityRequest,
    RegisterBeginRequest,
    RegisterCompleteRequest,
    AuthBeginRequest,
    AuthCompleteRequest,
    RevokeIdentityRequest,
    UpdateIdentityRequest,
    ArchiveIdentityRequest,
    ReconcileRequest,
    IdentityPublicResponse,
)
from . import service

try:
    # Phase 2 Priorite 6 (Event Producers) — additive, best-effort. A publish
    # failure must never break identity creation itself, matching the
    # existing defensive import pattern in backend/frek_v1/stages.py:10-14.
    from eventbus.bus import default_bus as _event_bus
    from eventbus.producers import (
        build_identity_created_event as _build_identity_created_event,
        build_identity_revoked_event as _build_identity_revoked_event,
        build_identity_updated_event as _build_identity_updated_event,
        build_identity_recovered_event as _build_identity_recovered_event,
        build_identity_reconciled_event as _build_identity_reconciled_event,
    )
except Exception:  # pragma: no cover - defensive, see comment above
    _event_bus = None
    _build_identity_created_event = None
    _build_identity_revoked_event = None
    _build_identity_updated_event = None
    _build_identity_recovered_event = None
    _build_identity_reconciled_event = None

try:
    # Same defensive pattern: notarization failing must never break the
    # revoke/update/archive response itself. notarize_event() itself never
    # raises (backend/notary/service.py:30), but the import can fail if the
    # notary module isn't wired in a given deployment.
    from notary.service import notarize_event as _notarize_event
except Exception:  # pragma: no cover - defensive, see comment above
    _notarize_event = None

logger = logging.getLogger("frek.identity_engine.routes")

identity_router = APIRouter(prefix="/identity", tags=["Identity Engine"])

db = None


def set_db(mongo_db):
    global db
    db = mongo_db


CHALLENGE_TTL_SECONDS = 300  # 5 min


async def ensure_indexes():
    if db is None:
        return
    await db.frek_persons.create_index("frek_id", unique=True)
    await db.frek_persons.create_index("credentials.credential_id")
    await db.frek_persons.create_index("linked_sessions")
    await db.frek_persons_challenges.create_index(
        "created_at", expireAfterSeconds=CHALLENGE_TTL_SECONDS
    )
    await db.frek_persons_challenges.create_index("frek_id")
    await db.frek_persons_challenges.create_index("challenge", unique=True)
    # MERGE (docs/decisions/0003-...md §1) — append-only, never deleted or
    # updated. The compound unique index enforces idempotency (one record
    # per ordered pair) at the DB level too, not just in the route's own
    # duplicate check.
    await db.frek_reconciliations.create_index(
        [("canonical_frek_id", 1), ("reconciled_frek_id", 1)], unique=True
    )
    await db.frek_reconciliations.create_index("reconciled_frek_id")


async def _store_challenge(challenge_b64: str, frek_id: Optional[str], kind: str):
    await db.frek_persons_challenges.insert_one(
        {
            "challenge": challenge_b64,
            "frek_id": frek_id,
            "kind": kind,  # "register" | "authenticate"
            "created_at": datetime.now(timezone.utc),
        }
    )


async def _pop_challenge(challenge_b64: str) -> Optional[dict]:
    doc = await db.frek_persons_challenges.find_one_and_delete(
        {"challenge": challenge_b64}
    )
    return doc


def _holder_or_admin(
    frek_id: str, x_frek_session: Optional[str], x_admin_key: str
) -> str:
    """Returns "holder" if x_frek_session verifies as frek_id, "admin" if
    x_admin_key matches SECRET_KEY, else raises 403.

    Holder-initiated is the primary path — matches this module's existing
    /me and /link-object pattern (a real per-subject session, which is what
    makes identity_engine a different case from frek_v1's client-scoped
    model, see docs/architecture/FREK_ID_RECONCILIATION.md). The admin
    override exists for cases the holder cannot self-serve (every
    credential lost, legal takedown, support case) — same interim pattern
    as the P0 closure's admin-key gates (reports/22_P0_SECURITY_CLOSURE.md).
    """
    if x_frek_session and service.verify_session_token(x_frek_session) == frek_id:
        return "holder"
    expected = os.environ.get("SECRET_KEY")
    if expected and x_admin_key == expected:
        return "admin"
    raise HTTPException(403, "Autorisation requise (session du titulaire ou cle admin)")


def _admin_or_403(x_admin_key: str) -> None:
    """Admin-only, no holder path — see search_identities()'s docstring
    for why (a bulk-listing surface has no per-holder analog, unlike every
    other gated route in this module)."""
    expected = os.environ.get("SECRET_KEY")
    if not expected or x_admin_key != expected:
        raise HTTPException(403, "invalid_admin_key")


def _to_public(identity: dict) -> dict:
    return {
        "frek_id": identity["frek_id"],
        "identity_type": identity.get("identity_type", "individual"),
        "display_name": identity.get("display_name"),
        "status": identity.get("status", "anonymous"),
        "created_at": identity.get("created_at"),
        "credentials_count": len(identity.get("credentials", [])),
        "linked_objects_count": len(identity.get("linked_objects", [])),
        "protected": identity.get("status") == "protected",
    }


# ---------------- INIT ----------------


@identity_router.post("/init")
async def init_identity(req: InitIdentityRequest):
    """Cree une FREKIdentity (anonyme au depart, sans credential).
    Si session_id fourni, attache les moments existants a cette identite.
    """
    # Note: identity_type is validated by Pydantic Literal; invalid -> 422 auto.

    frek_id = service.generate_identity_id()
    now = service.now_iso()

    identity = {
        "frek_id": frek_id,
        "identity_type": req.identity_type,
        "display_name": req.display_name,
        "created_at": now,
        "status": "anonymous",
        "credentials": [],
        "linked_objects": [],
        "linked_sessions": [req.session_id] if req.session_id else [],
        "permissions": [],
        "metadata": {},
    }
    await db.frek_persons.insert_one(identity)

    # Phase 2 Priorite 6 (Event Producers) — publish identity.created.
    # Best-effort: never allowed to fail the identity-creation response.
    if _event_bus is not None and _build_identity_created_event is not None:
        try:
            _event_bus.publish(_build_identity_created_event(identity))
        except Exception:
            logger.warning(
                "identity.created event publish failed (non-blocking)", exc_info=True
            )

    # Compte les moments deja signes sous cette session (pour affichage UI)
    linked_moments_count = 0
    if req.session_id:
        linked_moments_count = await db.frek_identities.count_documents(
            {
                "client_id": "public-window-1",
                "metadata.session_id": req.session_id,
            }
        )

    return {
        **_to_public(identity),
        "linked_moments_count": linked_moments_count,
    }


# ---------------- REGISTER ----------------


@identity_router.post("/{frek_id}/register/begin")
async def register_begin(
    frek_id: str,
    req: RegisterBeginRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Genere les options WebAuthn pour enregistrer une Passkey.

    Security fix (found auditing revoke, docs/decisions/0001-...): claiming a
    fresh anonymous identity (0 credentials) stays open — that is this
    route's real bootstrap purpose, matching /init's own "anonymous by
    default" design. Adding a credential to an identity that ALREADY has one
    now requires the holder's own session (ordinary credential rotation,
    docs/decisions/0003-...md §2) — previously anyone who knew a frek_id
    (never meant to be secret; it is the thing GET /{frek_id} and QR codes
    resolve) could register a competing Passkey and take the identity over,
    which would also have made the /revoke endpoint trivially bypassable
    (revoke, then just re-register).

    RECOVERY (docs/decisions/0003-...md §3, added 2026-08-31): an X-Admin-Key
    override is now accepted here too, mirroring the same
    `_holder_or_admin` pattern already used by revoke/update/archive/search.
    Before this, a holder who lost every registered Passkey had NO path back
    into their own identity, not even via support — this closed that gap.
    The admin path never deletes or replaces existing credentials, never
    regenerates frek_id, and register_complete (below) is what actually
    tells apart "ordinary rotation" from "this was a recovery" for auditing.
    """
    identity = await db.frek_persons.find_one({"frek_id": frek_id})
    if not identity:
        raise HTTPException(404, "FREK identity introuvable")
    if identity.get("credentials"):
        _holder_or_admin(frek_id, x_frek_session, x_admin_key)

    options_json, challenge_b64 = service.registration_options(
        frek_id=frek_id,
        display_name=identity.get("display_name") or frek_id,
        existing_credentials=identity.get("credentials", []),
    )
    await _store_challenge(challenge_b64, frek_id, "register")

    return json.loads(options_json)


@identity_router.post("/{frek_id}/register/complete")
async def register_complete(
    frek_id: str,
    req: RegisterCompleteRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Verifie la Passkey et l'attache a l'identite. Retourne un session token.

    Same ownership check as register_begin, re-checked here (not just at
    begin) so a credential set added between begin and complete can't be
    used to bypass it.

    RECOVERY (docs/decisions/0003-...md §3): when this identity already had
    credentials and the caller authenticated via X-Admin-Key rather than a
    holder session, this add-a-credential call IS the recovery act — the
    holder regains a working Passkey on their existing frek_id. That
    distinction (recovery vs. ordinary holder-initiated rotation) is what
    decides whether `identity.recovered` fires below.
    """
    identity = await db.frek_persons.find_one({"frek_id": frek_id})
    if not identity:
        raise HTTPException(404, "FREK identity introuvable")
    had_credentials_before = bool(identity.get("credentials"))
    authorized_via = "holder"  # default for the bootstrap case (0 credentials yet)
    if had_credentials_before:
        authorized_via = _holder_or_admin(frek_id, x_frek_session, x_admin_key)
    if identity.get("status") in ("revoked", "archived"):
        raise HTTPException(
            403, f"Identite {identity.get('status')} — ajout de Passkey refuse"
        )

    cred = req.credential or {}
    # Le challenge attendu est retrouve via la derniere entree register pour ce frek_id
    challenge_doc = await db.frek_persons_challenges.find_one(
        {"frek_id": frek_id, "kind": "register"},
        sort=[("created_at", -1)],
    )
    if not challenge_doc:
        raise HTTPException(
            400, "Challenge introuvable ou expire — recommence l'enregistrement"
        )

    try:
        cred_info = service.verify_registration(cred, challenge_doc["challenge"])
    except Exception as e:
        logger.warning(f"WebAuthn registration verification failed: {e}")
        raise HTTPException(400, f"Verification Passkey echouee: {e}")

    # Cleanup
    await db.frek_persons_challenges.delete_one({"_id": challenge_doc["_id"]})

    new_credential = {
        "credential_id": cred_info["credential_id"],
        "public_key": cred_info["public_key"],
        "sign_count": cred_info["sign_count"],
        "aaguid": cred_info["aaguid"],
        "transports": cred_info["transports"],
        "label": req.label,
        "created_at": service.now_iso(),
        "last_used_at": None,
    }

    await db.frek_persons.update_one(
        {"frek_id": frek_id},
        {
            "$push": {"credentials": new_credential},
            "$set": {"status": "protected"},
        },
    )

    if had_credentials_before and authorized_via == "admin":
        # RECOVERY (docs/decisions/0003-...md §3) — the holder had no
        # working session and regained access via the admin-key override.
        # frek_id is never touched; existing credentials are left in place
        # (the founder text permits revoking compromised ones separately,
        # via the existing /revocation route, but does not require it
        # here). Own event type, distinct from identity.updated, and
        # notarized like every other sensitive identity_engine action.
        now = service.now_iso()
        if _notarize_event is not None:
            await _notarize_event(
                payload_type="identity_recovery",
                payload_id=frek_id,
                payload_data={
                    "frek_id": frek_id,
                    "recovered_at": now,
                    "new_credential_label": req.label,
                },
                metadata={"producer": "identity_engine"},
            )
        if _event_bus is not None and _build_identity_recovered_event is not None:
            try:
                _event_bus.publish(
                    _build_identity_recovered_event(frek_id, now, req.label)
                )
            except Exception:
                logger.warning(
                    "identity.recovered event publish failed (non-blocking)",
                    exc_info=True,
                )
        logger.info(f"FREK identity {frek_id} recuperee via admin-key override")

    session_token = service.issue_session_token(frek_id)
    updated = await db.frek_persons.find_one({"frek_id": frek_id})
    return {
        "session_token": session_token,
        "identity": _to_public(updated),
    }


# ---------------- AUTHENTICATE ----------------


@identity_router.post("/authenticate/begin")
async def authenticate_begin(req: AuthBeginRequest):
    """Auth WebAuthn username-less. Retourne un challenge public."""
    options_json, challenge_b64 = service.authentication_options(
        allowed_credentials=None
    )
    await _store_challenge(challenge_b64, None, "authenticate")
    return json.loads(options_json)


@identity_router.post("/authenticate/complete")
async def authenticate_complete(req: AuthCompleteRequest):
    """Verifie l'assertion Passkey. Retourne session token + identity publique."""
    cred = req.credential or {}
    credential_id = cred.get("id")
    if not credential_id:
        raise HTTPException(400, "credential.id manquant")

    challenge_doc = await db.frek_persons_challenges.find_one(
        {"kind": "authenticate", "frek_id": None},
        sort=[("created_at", -1)],
    )
    if not challenge_doc:
        raise HTTPException(400, "Challenge auth introuvable ou expire")

    # Retrouver l'identite qui possede ce credential
    identity = await db.frek_persons.find_one(
        {"credentials.credential_id": credential_id}
    )
    if not identity:
        raise HTTPException(404, "Passkey inconnue")
    if identity.get("status") in ("revoked", "archived"):
        # Real enforcement for revoke/archive (P1) — a revoked/archived
        # identity's Passkey must not be able to mint a new session, or
        # revoke would be a label, not a security control.
        raise HTTPException(
            403, f"Identite {identity.get('status')} — authentification refusee"
        )

    target_cred = next(
        (c for c in identity["credentials"] if c["credential_id"] == credential_id),
        None,
    )
    if not target_cred:
        raise HTTPException(500, "credential referencee introuvable")

    try:
        new_sign_count = service.verify_authentication(
            credential=cred,
            expected_challenge_b64=challenge_doc["challenge"],
            credential_public_key_b64=target_cred["public_key"],
            current_sign_count=target_cred.get("sign_count", 0),
        )
    except Exception as e:
        logger.warning(f"WebAuthn authentication verification failed: {e}")
        raise HTTPException(401, f"Authentification Passkey echouee: {e}")

    # Cleanup + update sign_count + last_used_at
    await db.frek_persons_challenges.delete_one({"_id": challenge_doc["_id"]})
    await db.frek_persons.update_one(
        {"frek_id": identity["frek_id"], "credentials.credential_id": credential_id},
        {
            "$set": {
                "credentials.$.sign_count": new_sign_count,
                "credentials.$.last_used_at": service.now_iso(),
            }
        },
    )

    session_token = service.issue_session_token(identity["frek_id"])
    return {
        "session_token": session_token,
        "identity": _to_public(identity),
    }


# ---------------- QUERIES ----------------


@identity_router.get("/me")
async def get_me(x_frek_session: Optional[str] = Header(None)):
    """Retourne l'identite courante via le session token."""
    if not x_frek_session:
        raise HTTPException(401, "Session absente")
    frek_id = service.verify_session_token(x_frek_session)
    if not frek_id:
        raise HTTPException(401, "Session invalide ou expiree")
    identity = await db.frek_persons.find_one({"frek_id": frek_id})
    if not identity:
        raise HTTPException(404, "Identity introuvable")
    return _to_public(identity)


@identity_router.get("/search")
async def search_identities(
    display_name: Optional[str] = None,
    status: Optional[str] = None,
    identity_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    x_admin_key: str = Header(default=""),
):
    """P1 backlog (closes the "Search" entry in docs/PHASE2_STATUS.md's
    Identity Engine table, `MISSING` since Phase 2): a directory-listing
    query surface over `frek_persons`.

    ADMIN-key only — no holder path, unlike revoke/update/archive/export
    above. Those are all single-subject operations a holder legitimately
    performs on their OWN record; search is structurally different, a
    bulk-listing/enumeration surface across MANY identities, which has no
    per-holder analog (a holder searching for OTHER people's identities
    isn't a holder-scoped action at all — it's an operator/support tool).
    This is the "architecture explicitly requires it" admin-key case, not
    an interim shortcut: there is no existing per-holder mechanism this
    could use even in principle, unlike fingerprint/geo's consent routes
    (see docs/architecture/FREK_ID_RECONCILIATION.md).

    `display_name` matches as a case-insensitive substring; `status`/
    `identity_type` match exactly against the enums in
    `identity_engine/models.py`.
    """
    _admin_or_403(x_admin_key)

    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    query: dict = {}
    if display_name:
        query["display_name"] = {"$regex": re.escape(display_name), "$options": "i"}
    if status:
        query["status"] = status
    if identity_type:
        query["identity_type"] = identity_type

    cursor = (
        db.frek_persons.find(query).sort("created_at", -1).skip(offset).limit(limit)
    )
    docs = await cursor.to_list(limit)
    total = await db.frek_persons.count_documents(query)
    return {
        "count": len(docs),
        "total": total,
        "identities": [_to_public(d) for d in docs],
    }


@identity_router.get("/{frek_id}")
async def get_identity(frek_id: str):
    """Vue publique safe (jamais de credentials en clair)."""
    identity = await db.frek_persons.find_one({"frek_id": frek_id})
    if not identity:
        raise HTTPException(404, "Identity introuvable")
    return _to_public(identity)


@identity_router.get("/{frek_id}/objects")
async def get_linked_objects(
    frek_id: str, x_frek_session: Optional[str] = Header(None)
):
    """Liste des objets attaches. Requiert session valide pour le frek_id demande."""
    if not x_frek_session or service.verify_session_token(x_frek_session) != frek_id:
        raise HTTPException(401, "Session invalide pour cet identity")

    identity = await db.frek_persons.find_one(
        {"frek_id": frek_id}, {"_id": 0, "credentials": 0}
    )
    if not identity:
        raise HTTPException(404, "Identity introuvable")

    # Rassemble moments + fk lies + moments des linked_sessions
    linked_ids = set(identity.get("linked_objects", []))
    sessions = identity.get("linked_sessions", [])

    moments = []
    if sessions:
        cursor = (
            db.frek_identities.find(
                {
                    "client_id": "public-window-1",
                    "metadata.session_id": {"$in": sessions},
                },
                {"_id": 0, "email_hash": 0, "metadata.ip_key": 0},
            )
            .sort("created_at", -1)
            .limit(200)
        )
        moments = await cursor.to_list(200)

    fks = []
    if linked_ids:
        cursor = db.fk_objects.find(
            {"frek_id": {"$in": list(linked_ids)}}, {"_id": 0, "storage_path": 0}
        )
        fks = await cursor.to_list(200)

    return {
        "frek_id": frek_id,
        "moments": moments,
        "fk_objects": fks,
        "linked_sessions_count": len(sessions),
    }


@identity_router.post("/link-object")
async def link_object(payload: dict, x_frek_session: Optional[str] = Header(None)):
    """Attache un frek_id d'objet (moment ou FK) a l'identite courante."""
    if not x_frek_session:
        raise HTTPException(401, "Session requise")
    frek_id = service.verify_session_token(x_frek_session)
    if not frek_id:
        raise HTTPException(401, "Session invalide")

    object_id = payload.get("object_id")
    if not object_id:
        raise HTTPException(400, "object_id requis")

    await db.frek_persons.update_one(
        {"frek_id": frek_id},
        {"$addToSet": {"linked_objects": object_id}},
    )
    return {"ok": True, "object_id": object_id}


# ---------------- LIFECYCLE (P1: revoke / update / archive) ----------------
# docs/architecture/FREK_ID_RECONCILIATION.md — holder-initiated-by-default,
# admin-key override, modeled on (not copied from) frek_v1's
# client-initiated revoke (backend/frek_v1/identity.py:201).


@identity_router.post("/{frek_id}/revocation")
async def revoke_identity(
    frek_id: str,
    req: RevokeIdentityRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Revocation — immutable, idempotente. La preuve historique reste lisible
    (jamais de delete). Bloque toute authentification/enregistrement futurs
    pour ce frek_id (voir authenticate_complete, register_begin/complete)."""
    identity = await db.frek_persons.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(404, "Identity introuvable")

    revoked_by = _holder_or_admin(frek_id, x_frek_session, x_admin_key)

    if identity.get("status") == "revoked":
        return {
            "frek_id": frek_id,
            "status": "revoked",
            "revoked_at": identity.get("revoked_at"),
            "message": "Deja revoque (idempotent)",
        }

    now = service.now_iso()
    await db.frek_persons.update_one(
        {"frek_id": frek_id},
        {
            "$set": {
                "status": "revoked",
                "revoked_at": now,
                "revoked_by": revoked_by,
                "revoke_reason": req.reason,
            }
        },
    )

    if _notarize_event is not None:
        await _notarize_event(
            payload_type="identity_revocation",
            payload_id=frek_id,
            payload_data={
                "frek_id": frek_id,
                "revoked_at": now,
                "revoked_by": revoked_by,
                "reason": req.reason,
            },
            metadata={"producer": "identity_engine"},
        )

    if _event_bus is not None and _build_identity_revoked_event is not None:
        try:
            _event_bus.publish(
                _build_identity_revoked_event(frek_id, now, revoked_by, req.reason)
            )
        except Exception:
            logger.warning(
                "identity.revoked event publish failed (non-blocking)", exc_info=True
            )

    logger.info(f"FREK identity {frek_id} revoquee par {revoked_by}")
    return {
        "frek_id": frek_id,
        "status": "revoked",
        "revoked_at": now,
        "reason": req.reason,
        "message": "Identite revoquee. Preuve historique conservee.",
    }


@identity_router.patch("/{frek_id}")
async def update_identity(
    frek_id: str,
    req: UpdateIdentityRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Met a jour display_name et/ou metadata. Refuse sur identite revoquee
    (immuable une fois revoquee — coherent avec revoke_identity)."""
    identity = await db.frek_persons.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(404, "Identity introuvable")

    _holder_or_admin(frek_id, x_frek_session, x_admin_key)

    if identity.get("status") == "revoked":
        raise HTTPException(409, "Identite revoquee — immuable")

    update_set: dict = {}
    changed_fields: list = []
    if req.display_name is not None:
        update_set["display_name"] = req.display_name
        changed_fields.append("display_name")
    if req.metadata is not None:
        update_set["metadata"] = req.metadata
        changed_fields.append("metadata")

    if not update_set:
        return _to_public(identity)

    now = service.now_iso()
    update_set["updated_at"] = now
    await db.frek_persons.update_one({"frek_id": frek_id}, {"$set": update_set})

    if _event_bus is not None and _build_identity_updated_event is not None:
        try:
            _event_bus.publish(
                _build_identity_updated_event(frek_id, now, changed_fields)
            )
        except Exception:
            logger.warning(
                "identity.updated event publish failed (non-blocking)", exc_info=True
            )

    updated = await db.frek_persons.find_one({"frek_id": frek_id})
    return _to_public(updated)


@identity_router.post("/{frek_id}/archive")
async def archive_identity(
    frek_id: str,
    req: ArchiveIdentityRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Archivage souple — distinct de revoke : pas un evenement de securite
    (pas de notarisation), simplement "identite non active". Bloque aussi
    l'authentification (voir authenticate_complete) mais n'est pas immuable
    de la meme facon que revoke : pas encore de flux "unarchive" (nouvelle
    capacite, non modelee sur un existant — voir
    docs/architecture/FREK_ID_RECONCILIATION.md)."""
    identity = await db.frek_persons.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(404, "Identity introuvable")

    archived_by = _holder_or_admin(frek_id, x_frek_session, x_admin_key)

    if identity.get("status") == "revoked":
        raise HTTPException(409, "Identite revoquee — archivage sans objet")
    if identity.get("status") == "archived":
        return {
            "frek_id": frek_id,
            "status": "archived",
            "archived_at": identity.get("archived_at"),
            "message": "Deja archivee (idempotent)",
        }

    now = service.now_iso()
    await db.frek_persons.update_one(
        {"frek_id": frek_id},
        {
            "$set": {
                "status": "archived",
                "archived_at": now,
                "archived_by": archived_by,
                "archive_reason": req.reason,
            }
        },
    )

    logger.info(f"FREK identity {frek_id} archivee par {archived_by}")
    return {
        "frek_id": frek_id,
        "status": "archived",
        "archived_at": now,
        "reason": req.reason,
        "message": "Identite archivee.",
    }


# ---------------- MERGE (reconciliation) ----------------
# docs/decisions/0003-identity-lifecycle-founder-decisions-implemented.md
# §1. Deliberately named "reconcile", not "merge" — the approved semantics
# are strictly non-destructive: neither frek_id involved is ever deleted,
# overwritten, or stops resolving. This only ever appends one record to
# frek_reconciliations, establishing a canonical relationship. See
# docs/architecture/FREK_ID_ENTITY_TAXONOMY.md for why this is scoped to
# identity_engine's own frek_persons collection.


@identity_router.post("/{frek_id}/reconcile")
async def reconcile_identity(
    frek_id: str,
    req: ReconcileRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Establishes a non-destructive canonical relationship between
    `frek_id` and `req.target_frek_id`. Never merges, deletes, or
    overwrites either identity — GET /{frek_id} keeps resolving exactly as
    before for both, satisfying the founder's "existing references must
    remain resolvable" requirement literally.

    Authorization (prevents cross-holder takeover, per the ADR):
    - The caller must prove authority over the SOURCE `frek_id` — a valid
      holder session or the admin key (`_holder_or_admin`, same pattern as
      revoke/update/archive).
    - Reconciling with ANOTHER `identity_engine` identity additionally
      requires `target_session_token` to verify holder consent for that
      target too, UNLESS the caller is admin — a holder can only reconcile
      identities they can prove control of on both sides.
    - Reconciling with a `frek_v1` identity (`target_system="frek_v1"`) is
      admin-only: frek_v1 has no holder-session concept a plain holder
      could use to self-serve prove consent there (see
      docs/architecture/FREK_ID_RECONCILIATION.md) — an honest,
      pre-existing architectural constraint, not a shortcut introduced
      here.
    """
    identity = await db.frek_persons.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(404, "Identity introuvable")
    if frek_id == req.target_frek_id:
        raise HTTPException(
            400, "Impossible de reconcilier une identite avec elle-meme"
        )

    authorized_via = _holder_or_admin(frek_id, x_frek_session, x_admin_key)

    if req.target_system == "identity_engine":
        target = await db.frek_persons.find_one({"frek_id": req.target_frek_id})
        if not target:
            raise HTTPException(404, "Identite cible introuvable")
        if authorized_via == "holder":
            target_ok = (
                req.target_session_token
                and service.verify_session_token(req.target_session_token)
                == req.target_frek_id
            )
            if not target_ok:
                raise HTTPException(
                    403,
                    "Consentement du titulaire de l'identite cible requis "
                    "(target_session_token)",
                )
    else:
        # Cross-system (frek_v1): no holder-session concept to verify
        # consent against — admin-key only.
        if authorized_via != "admin":
            raise HTTPException(
                403,
                "Reconciliation cross-systeme (frek_v1) reservee a la cle admin",
            )

    # Idempotent: a prior reconciliation of this exact ordered pair returns
    # the existing record rather than erroring or duplicating it.
    existing = await db.frek_reconciliations.find_one(
        {"canonical_frek_id": frek_id, "reconciled_frek_id": req.target_frek_id},
        {"_id": 0},
    )
    if existing:
        return {**existing, "message": "Deja reconcilie (idempotent)"}

    now = service.now_iso()
    record = {
        "canonical_frek_id": frek_id,
        "reconciled_frek_id": req.target_frek_id,
        "reconciled_system": req.target_system,
        "reconciled_at": now,
        "authorized_by": authorized_via,
        "reason": req.reason,
    }
    await db.frek_reconciliations.insert_one(dict(record))

    if _notarize_event is not None:
        await _notarize_event(
            payload_type="identity_reconciliation",
            payload_id=frek_id,
            payload_data=record,
            metadata={"producer": "identity_engine"},
        )
    if _event_bus is not None and _build_identity_reconciled_event is not None:
        try:
            _event_bus.publish(
                _build_identity_reconciled_event(
                    canonical_frek_id=frek_id,
                    reconciled_frek_id=req.target_frek_id,
                    reconciled_system=req.target_system,
                    reconciled_at=now,
                    authorized_by=authorized_via,
                    reason=req.reason,
                )
            )
        except Exception:
            logger.warning(
                "identity.reconciled event publish failed (non-blocking)",
                exc_info=True,
            )

    logger.info(
        f"FREK identity {frek_id} reconciliee avec {req.target_frek_id} "
        f"({req.target_system}) par {authorized_via}"
    )
    return {**record, "message": "Reconciliation enregistree."}


@identity_router.get("/{frek_id}/reconciliations")
async def get_reconciliations(frek_id: str):
    """Every reconciliation record naming `frek_id` on EITHER side — public,
    no auth, matching GET /{frek_id}'s own public-view design. The founder's
    "existing references must remain resolvable" requirement means this is
    a read anyone who can already resolve `frek_id` should be able to see,
    not a holder-only surface."""
    records = (
        await db.frek_reconciliations.find(
            {
                "$or": [
                    {"canonical_frek_id": frek_id},
                    {"reconciled_frek_id": frek_id},
                ]
            },
            {"_id": 0},
        )
        .sort("reconciled_at", 1)
        .to_list(200)
    )
    return {"frek_id": frek_id, "count": len(records), "reconciliations": records}
