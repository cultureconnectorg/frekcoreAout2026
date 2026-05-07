"""FREK Staff — Tests bcrypt + migration legacy SHA256."""
import os

import bcrypt
import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/v1"


@pytest.fixture(scope="module")
def mongo():
    from pymongo import MongoClient
    client = MongoClient(os.environ.get("MONGO_URL"), serverSelectionTimeoutMS=2000)
    yield client[os.environ.get("DB_NAME", "test_database")]
    client.close()


# ---------- Hash helpers ----------
class TestPinHashHelpers:
    def test_hash_pin_returns_bcrypt_format(self):
        from staff.routes import _hash_pin
        h = _hash_pin("9999")
        assert h.startswith("$2"), f"expected bcrypt format, got {h[:5]}"
        # Bcrypt round-trip
        assert bcrypt.checkpw(b"9999", h.encode("ascii")) is True

    def test_verify_pin_bcrypt_valid(self):
        from staff.routes import _hash_pin, _verify_pin
        h = _hash_pin("1234")
        ok, rehash = _verify_pin("1234", h)
        assert ok is True
        assert rehash is False  # deja bcrypt, pas besoin

    def test_verify_pin_bcrypt_invalid(self):
        from staff.routes import _hash_pin, _verify_pin
        h = _hash_pin("1234")
        ok, rehash = _verify_pin("9999", h)
        assert ok is False
        assert rehash is False

    def test_verify_pin_legacy_sha256_valid_triggers_rehash(self):
        from staff.routes import _legacy_hash_pin, _verify_pin
        legacy = _legacy_hash_pin("9999")
        ok, rehash = _verify_pin("9999", legacy)
        assert ok is True
        assert rehash is True  # signal de migration

    def test_verify_pin_legacy_sha256_invalid_no_rehash(self):
        from staff.routes import _legacy_hash_pin, _verify_pin
        legacy = _legacy_hash_pin("9999")
        ok, rehash = _verify_pin("0000", legacy)
        assert ok is False
        assert rehash is False

    def test_verify_pin_empty_hash(self):
        from staff.routes import _verify_pin
        ok, rehash = _verify_pin("9999", "")
        assert ok is False
        assert rehash is False


# ---------- Migration end-to-end (HTTP) ----------
class TestLegacyMigration:
    def test_login_with_legacy_pin_migrates_to_bcrypt(self, mongo):
        """Force un staff en legacy SHA256, login via API, verifie qu'il est migre en bcrypt."""
        from staff.routes import _legacy_hash_pin

        agent_id = "TEST_LEGACY_MIGR"
        pin = "5678"
        # Inject staff legacy
        mongo.staff.delete_one({"agent_id": agent_id})
        mongo.staff.insert_one({
            "agent_id": agent_id,
            "nom": "Test Legacy",
            "role": "agent_acces",
            "pin_hash": _legacy_hash_pin(pin),  # SHA256 legacy
            "allowed_zones": ["ENTREE"],
            "active": True,
            "created_at": "2026-01-01T00:00:00+00:00",
        })

        # Login via API
        r = requests.post(
            f"{API}/staff/login",
            json={"agent_id": agent_id, "pin": pin},
            timeout=5,
        )
        assert r.status_code == 200, r.text

        # Verifie que le hash a ete migre en bcrypt
        staff = mongo.staff.find_one({"agent_id": agent_id})
        assert staff["pin_hash"].startswith("$2"), f"PIN pas migre en bcrypt: {staff['pin_hash'][:10]}"
        assert "pin_migrated_at" in staff
        # Le PIN original fonctionne toujours
        assert bcrypt.checkpw(pin.encode(), staff["pin_hash"].encode()) is True

        # Cleanup
        mongo.staff.delete_one({"agent_id": agent_id})

    def test_login_wrong_pin_does_not_migrate(self, mongo):
        """Un mauvais PIN ne migre rien (pas d'effet de bord)."""
        from staff.routes import _legacy_hash_pin

        agent_id = "TEST_LEGACY_BADPIN"
        pin = "5678"
        legacy_hash = _legacy_hash_pin(pin)
        mongo.staff.delete_one({"agent_id": agent_id})
        mongo.staff.insert_one({
            "agent_id": agent_id,
            "nom": "Test Legacy Bad",
            "role": "agent_acces",
            "pin_hash": legacy_hash,
            "allowed_zones": [],
            "active": True,
        })

        r = requests.post(
            f"{API}/staff/login",
            json={"agent_id": agent_id, "pin": "WRONG"},
            timeout=5,
        )
        assert r.status_code == 401

        staff = mongo.staff.find_one({"agent_id": agent_id})
        assert staff["pin_hash"] == legacy_hash  # inchange
        mongo.staff.delete_one({"agent_id": agent_id})
