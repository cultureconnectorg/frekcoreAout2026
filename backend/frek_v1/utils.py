"""
FREK v1 — Utilitaires
"""
import hashlib
import os
import uuid
import secrets
from datetime import datetime, timezone, timedelta

import jwt


def get_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise RuntimeError(f"Variable d'environnement manquante: {key}")
    return val


def hash_email(email: str) -> str:
    salt = get_env("FREK_EMAIL_SALT")
    return hashlib.sha256(f"{salt}{email.lower().strip()}".encode()).hexdigest()


def generate_frek_id() -> str:
    return str(uuid.uuid4())


def generate_qr_token(frek_id: str) -> str:
    return hashlib.sha256(f"{frek_id}{secrets.token_hex(8)}".encode()).hexdigest()[:24]


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def create_access_token(client_id: str, expires_minutes: int = 1440) -> str:
    secret_key = get_env("SECRET_KEY")
    payload = {
        "sub": client_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
        "type": "access",
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_access_token(token: str) -> dict:
    secret_key = get_env("SECRET_KEY")
    return jwt.decode(token, secret_key, algorithms=["HS256"])


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
