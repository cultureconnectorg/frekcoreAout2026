"""Identity Engine — WebAuthn service + session tokens.

Utilise `webauthn` (py_webauthn v3) pour la ceremonie standard.
Session tokens : HMAC-signes courts (secret = SECRET_KEY), stateless.
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
    AuthenticatorTransport,
)
from webauthn.helpers import base64url_to_bytes

logger = logging.getLogger("frek.identity_engine.service")

RP_NAME = "FREKCORE"
SESSION_TTL_DAYS = 90


class WebAuthnConfigError(RuntimeError):
    """FREK_RP_ORIGIN doit etre defini explicitement en production.

    On refuse le fallback silencieux vers `localhost` : sinon les Passkeys
    seraient enregistrees contre un rpId irrelevant et jamais reutilisables
    sur le vrai domaine.
    """


def _rp_id_from_url(backend_url: str) -> str:
    """Extrait le domaine (host) sans le schema ni port."""
    try:
        host = urlparse(backend_url).hostname
    except Exception:
        host = None
    return host or ""


def _configured_url() -> str:
    """Origin canonique de l'app. Doit correspondre au domaine reel servi."""
    return (
        os.environ.get("FREK_RP_ORIGIN")
        or os.environ.get("REACT_APP_BACKEND_URL", "")
    ).rstrip("/")


def get_rp_id() -> str:
    """RP ID = hostname exact du domaine ou tourne l'app.

    Aucune valeur par defaut : si mal configure, WebAuthn refusera la ceremony
    plutot que d'enregistrer une Passkey contre `localhost` inutilisable.
    """
    url = _configured_url()
    host = _rp_id_from_url(url) if url else ""
    if not host:
        raise WebAuthnConfigError(
            "FREK_RP_ORIGIN manquant. Configurez le domaine public exact "
            "(ex: https://frekcore.com) avant d'utiliser les Passkeys."
        )
    return host


def get_origin() -> str:
    """Origin complet (schema + host [+ port])."""
    url = _configured_url()
    if not url:
        raise WebAuthnConfigError(
            "FREK_RP_ORIGIN manquant. Configurez le domaine public exact "
            "(ex: https://frekcore.com) avant d'utiliser les Passkeys."
        )
    return url


def rp_config_status() -> dict:
    """Sert au /health/deep pour verifier que la config Passkey est prete."""
    try:
        return {"configured": True, "rp_id": get_rp_id(), "origin": get_origin()}
    except WebAuthnConfigError as e:
        return {"configured": False, "reason": str(e)}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_identity_id() -> str:
    return f"id-{secrets.token_hex(6)}-{secrets.token_hex(2)}"


# ---------- WebAuthn ceremonies ----------

def registration_options(
    frek_id: str,
    display_name: Optional[str],
    existing_credentials: list,
) -> Tuple[str, str]:
    """
    Retourne (options_json_str, challenge_b64).
    L'appelant doit stocker le challenge cote serveur (avec le frek_id).
    """
    user_name = display_name or frek_id
    exclude = [
        PublicKeyCredentialDescriptor(
            id=base64url_to_bytes(c["credential_id"]),
        )
        for c in existing_credentials
    ]
    opts = generate_registration_options(
        rp_id=get_rp_id(),
        rp_name=RP_NAME,
        user_id=frek_id.encode("utf-8"),
        user_name=user_name,
        user_display_name=user_name,
        exclude_credentials=exclude,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    options_json = options_to_json(opts)
    # webauthn v3 stocke le challenge dans opts.challenge (bytes)
    challenge_b64 = base64.urlsafe_b64encode(opts.challenge).rstrip(b"=").decode("ascii")
    return options_json, challenge_b64


def verify_registration(
    credential: Dict[str, Any],
    expected_challenge_b64: str,
) -> Dict[str, Any]:
    """
    Verifie la reponse WebAuthn. Retourne les infos a stocker (credential_id, public_key, sign_count, transports).
    """
    challenge_bytes = base64url_to_bytes(expected_challenge_b64)
    verification = verify_registration_response(
        credential=credential,
        expected_challenge=challenge_bytes,
        expected_rp_id=get_rp_id(),
        expected_origin=get_origin(),
    )
    cred_id_b64 = base64.urlsafe_b64encode(verification.credential_id).rstrip(b"=").decode("ascii")
    pub_key_b64 = base64.urlsafe_b64encode(verification.credential_public_key).rstrip(b"=").decode("ascii")
    aaguid = str(verification.aaguid) if getattr(verification, "aaguid", None) else None
    return {
        "credential_id": cred_id_b64,
        "public_key": pub_key_b64,
        "sign_count": verification.sign_count,
        "aaguid": aaguid,
        "transports": credential.get("response", {}).get("transports", []) or [],
    }


def authentication_options(allowed_credentials: Optional[list] = None) -> Tuple[str, str]:
    """
    Genere les options d'auth. Si allowed_credentials est None -> username-less discovery.
    """
    allow = None
    if allowed_credentials:
        allow = [
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c["credential_id"]))
            for c in allowed_credentials
        ]
    opts = generate_authentication_options(
        rp_id=get_rp_id(),
        allow_credentials=allow,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    options_json = options_to_json(opts)
    challenge_b64 = base64.urlsafe_b64encode(opts.challenge).rstrip(b"=").decode("ascii")
    return options_json, challenge_b64


def verify_authentication(
    credential: Dict[str, Any],
    expected_challenge_b64: str,
    credential_public_key_b64: str,
    current_sign_count: int,
) -> int:
    """
    Verifie l'assertion. Retourne le nouveau sign_count.
    Leve InvalidAuthenticationResponse si echec.
    """
    challenge_bytes = base64url_to_bytes(expected_challenge_b64)
    pub_key_bytes = base64url_to_bytes(credential_public_key_b64)
    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=challenge_bytes,
        expected_rp_id=get_rp_id(),
        expected_origin=get_origin(),
        credential_public_key=pub_key_bytes,
        credential_current_sign_count=current_sign_count,
    )
    return verification.new_sign_count


# ---------- Session tokens ----------

def _secret() -> bytes:
    key = os.environ.get("SECRET_KEY", "")
    if not key:
        raise RuntimeError("SECRET_KEY missing")
    return key.encode("utf-8")


def issue_session_token(frek_id: str, ttl_days: int = SESSION_TTL_DAYS) -> str:
    """Session token stateless : base64(payload).base64(signature)."""
    payload = {
        "frek_id": frek_id,
        "exp": int(time.time()) + ttl_days * 86400,
        "nonce": secrets.token_hex(4),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(_secret(), payload_bytes, hashlib.sha256).digest()
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode("ascii")
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode("ascii")
    return f"{payload_b64}.{sig_b64}"


def verify_session_token(token: str) -> Optional[str]:
    """Retourne frek_id si valide + non expire, sinon None."""
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        payload_bytes = base64url_to_bytes(payload_b64)
        sig = base64url_to_bytes(sig_b64)
        expected = hmac.new(_secret(), payload_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, sig):
            return None
        payload = json.loads(payload_bytes.decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return None
        return payload.get("frek_id")
    except Exception:
        return None
