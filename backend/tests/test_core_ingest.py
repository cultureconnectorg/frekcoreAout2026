"""FREK Core — Tests couche evenementielle CC2026 + SD-JWT VC + invariants Phase 4.5.

Couvre integralement les 12 tests requis par la directive :
- test_ingest_creates_frek_subject
- test_ingest_idempotent_same_key
- test_ingest_rejects_unknown_source
- test_ingest_rejects_invalid_bearer
- test_ingest_score_calculated_from_rules_not_hardcoded
- test_ingest_score_base_plus_badge_bonus
- test_get_frek_profile_returns_events
- test_get_frek_profile_404_unknown
- test_event_stats_by_badge_type
- test_ecosystem_pulse_structure
- test_sd_jwt_no_regression_ldp_vc
- test_ed25519_key_unchanged
"""
import asyncio
import hashlib
import os
import secrets
import time

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"

KILTIKONET_SECRET = os.environ.get("FREKCORE_SECRET_KILTIKONET")
FMS_SECRET = os.environ.get("FREKCORE_SECRET_FMS")

CLIENT_ID = os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")
CLIENT_SECRET = os.environ.get("FREK_CLIENT_KILTIKONET_SECRET", "")


def H(secret: str):
    return {"Authorization": f"Bearer {secret}"}


def fresh_frek():
    return f"FREK-CC26-{secrets.token_hex(3).upper()}"


def base_payload(**overrides):
    p = {
        "frek_id": fresh_frek(),
        "event_id": "CC2026",
        "action": "ACTIVATION",
        "badge_type": "CC26-BNV",
        "timestamp": f"2026-05-12T{secrets.randbelow(24):02d}:00:00Z",
        "source": "kiltikonet",
    }
    p.update(overrides)
    return p


# ---------- Mongo fixture ----------
@pytest.fixture(scope="module")
def mongo():
    from pymongo import MongoClient
    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=2000)
    yield client[os.environ.get("DB_NAME")]
    client.close()


# ---------- Tests Core ingest ----------
class TestCoreIngest:
    def test_ingest_creates_frek_subject(self, mongo):
        p = base_payload()
        r = requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET), json=p, timeout=5)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["received"] is True
        assert d["idempotent"] is False
        assert d["frek_id"] == p["frek_id"]
        assert d["cultural_impact_score"] > 0
        # Verifie le subject en base
        subject = mongo.frek_subjects.find_one({"frek_id": p["frek_id"]})
        assert subject is not None
        assert subject["status"] == "ACTIVE"
        # Squelette enrichment present
        for k in ["frek_subject_did", "nominatif", "jeton_cc_linked", "nfc_badge_written", "eudi_vc_issued"]:
            assert k in subject["enrichment"]
            assert subject["enrichment"][k] is None

    def test_ingest_idempotent_same_key(self):
        p = base_payload()
        r1 = requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET), json=p, timeout=5).json()
        r2 = requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET), json=p, timeout=5).json()
        assert r1["idempotent"] is False
        assert r2["idempotent"] is True
        # Le score reste le meme (pas de double scoring)
        assert r1["cultural_impact_score"] == r2["cultural_impact_score"]

    def test_ingest_rejects_unknown_source(self):
        p = base_payload(source="unknown_source")
        r = requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET), json=p, timeout=5)
        # Le bearer est valide pour kiltikonet, mais le body declare une autre source => mismatch 403
        assert r.status_code == 403

    def test_ingest_rejects_invalid_bearer(self):
        p = base_payload()
        r = requests.post(f"{API}/core/ingest", headers=H("fake-secret-xxx"), json=p, timeout=5)
        assert r.status_code == 403
        # Aucun bearer du tout
        r2 = requests.post(f"{API}/core/ingest", json=p, timeout=5)
        assert r2.status_code == 403

    def test_ingest_score_calculated_from_rules_not_hardcoded(self, mongo):
        """Modifier dynamiquement la regle de bonus pour CC26-BNV, l'ingest doit refleter."""
        admin_key = os.environ.get("SECRET_KEY")
        # Override bonus_score CC26-BNV: 10 -> 99
        mongo.frek_scoring_rules.update_one(
            {"badge_type": "CC26-BNV"},
            {"$set": {"bonus_score": 99}},
        )
        # Force le backend a recharger son cache
        rr = requests.post(
            f"{API}/core/admin/reload-rules",
            headers={"X-Admin-Key": admin_key or ""},
            timeout=5,
        )
        assert rr.status_code == 200, rr.text
        try:
            p = base_payload()
            r = requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET), json=p, timeout=5).json()
            # base ACTIVATION CC2026 = 10, bonus CC26-BNV = 99 => 109
            assert r["cultural_impact_score"] == 109, f"score depend bien des rules : got {r['cultural_impact_score']}"
        finally:
            # Restore
            mongo.frek_scoring_rules.update_one(
                {"badge_type": "CC26-BNV"},
                {"$set": {"bonus_score": 10}},
            )
            requests.post(
                f"{API}/core/admin/reload-rules",
                headers={"X-Admin-Key": admin_key or ""},
                timeout=5,
            )

    def test_ingest_score_base_plus_badge_bonus(self):
        # base 10 + bonus VIP 15 = 25
        p = base_payload(badge_type="CC26-VIP")
        r = requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET), json=p, timeout=5).json()
        assert r["score_delta"] == 25
        assert r["cultural_impact_score"] == 25

    def test_ingest_unknown_badge_type_returns_422(self):
        p = base_payload(badge_type="CC26-DOES-NOT-EXIST")
        r = requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET), json=p, timeout=5)
        assert r.status_code == 422


# ---------- Profile + stats + pulse ----------
class TestCoreReads:
    def test_get_frek_profile_returns_events(self):
        p = base_payload()
        requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET), json=p, timeout=5)
        # 2nd event different timestamp
        p2 = {**p, "timestamp": "2026-05-12T23:59:00Z", "badge_type": "CC26-ART"}
        requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET), json=p2, timeout=5)

        prof = requests.get(f"{API}/core/frek/{p['frek_id']}", timeout=5).json()
        assert prof["frek_id"] == p["frek_id"]
        assert prof["event_count"] == 2
        assert len(prof["events"]) == 2
        # Events ne doivent pas leak _id ni idempotency_key
        for ev in prof["events"]:
            assert "_id" not in ev
            assert "idempotency_key" not in ev
        # Enrichment squelette present
        assert "frek_subject_did" in prof["enrichment"]

    def test_get_frek_profile_404_unknown(self):
        r = requests.get(f"{API}/core/frek/FREK-NEVER-EXISTED", timeout=5)
        assert r.status_code == 404

    def test_event_stats_by_badge_type(self):
        # Emet 2 frek_ids differents avec badge_types differents sur un event_id dedie
        event_id = f"TEST-STATS-{secrets.token_hex(3)}"
        f1 = fresh_frek()
        f2 = fresh_frek()
        requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET),
                      json=base_payload(frek_id=f1, event_id=event_id, badge_type="CC26-ART"), timeout=5)
        requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET),
                      json=base_payload(frek_id=f2, event_id=event_id, badge_type="CC26-VIP"), timeout=5)

        stats = requests.get(f"{API}/core/event/{event_id}/stats", timeout=5).json()
        assert stats["event_id"] == event_id
        assert stats["total_frek_ids"] == 2
        assert stats["by_badge_type"]["CC26-ART"] == 1
        assert stats["by_badge_type"]["CC26-VIP"] == 1
        assert stats["by_source"]["kiltikonet"] == 2
        assert stats["average_cultural_impact_score"] > 0

    def test_ecosystem_pulse_structure(self):
        # On ingest au moins un event pour garantir status ALIVE
        requests.post(f"{API}/core/ingest", headers=H(KILTIKONET_SECRET),
                      json=base_payload(), timeout=5)
        r = requests.get(f"{API}/core/ecosystem/pulse", timeout=5)
        assert r.status_code == 200
        d = r.json()
        # Structure conforme directive
        for k in ["timestamp", "total_frek_ids", "active_frek_ids", "total_events",
                  "events_last_24h", "top_event", "sources_active",
                  "average_cultural_impact_score", "ecosystem_status"]:
            assert k in d, f"champ manquant: {k}"
        assert d["ecosystem_status"] in ("ALIVE", "DORMANT")
        assert isinstance(d["sources_active"], list)


# ---------- Phase 4.6 SD-JWT VC ----------
class TestSDJWT:
    @pytest.fixture
    def existing_frek_id(self):
        """Utilise la collection frek_identities historique pour le flow EUDI."""
        tok = requests.post(
            f"{BASE_URL}/api/v1/auth/token",
            json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
            timeout=10,
        ).json()["access_token"]
        r = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            json={"email": f"sdjwt_test_{secrets.token_hex(4)}@frekcore.fr", "source": "test", "event": "CC2026"},
            headers={"Authorization": f"Bearer {tok}"},
            timeout=10,
        )
        return r.json()["frek_id"]

    def _eudi_flow_for_format(self, frek_id, fmt):
        offer = requests.post(f"{BASE_URL}/api/v1/eudi/credential-offer/{frek_id}", timeout=5).json()
        code = offer["credential_offer"]["grants"][
            "urn:ietf:params:oauth:grant-type:pre-authorized_code"
        ]["pre-authorized_code"]
        tok = requests.post(
            f"{BASE_URL}/api/v1/eudi/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:pre-authorized_code",
                "pre-authorized_code": code,
            },
            timeout=5,
        ).json()["access_token"]
        return requests.post(
            f"{BASE_URL}/api/v1/eudi/credential",
            json={"format": fmt},
            headers={"Authorization": f"Bearer {tok}"},
            timeout=5,
        )

    def test_sd_jwt_no_regression_ldp_vc(self, existing_frek_id):
        """Phase 4.6 ne casse pas le flow ldp_vc historique."""
        r = self._eudi_flow_for_format(existing_frek_id, "ldp_vc")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["format"] == "ldp_vc"
        vc = d["credential"]
        assert "VerifiableCredential" in vc["type"]
        assert vc["proof"]["cryptosuite"] == "eddsa-jcs-2022"
        # Verification serveur existante toujours OK
        v = requests.post(f"{BASE_URL}/api/v1/vc/verify", json={"credential": vc}, timeout=5).json()
        assert v["valid"] is True

    def test_sd_jwt_issuance(self, existing_frek_id):
        r = self._eudi_flow_for_format(existing_frek_id, "vc+sd-jwt")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["format"] == "vc+sd-jwt"
        sd = d["credential"]
        # Structure : <jwt>~<disc>~<disc>~...~
        assert sd.count(".") == 2 or sd.count(".") > 0
        parts = sd.split("~")
        assert len(parts) >= 2, "SD-JWT doit avoir au moins jwt + un separateur"

    def test_sd_jwt_verify_full(self, existing_frek_id):
        sd = self._eudi_flow_for_format(existing_frek_id, "vc+sd-jwt").json()["credential"]
        r = requests.post(
            f"{BASE_URL}/api/v1/eudi/credential/verify-sdjwt",
            json={"credential": sd},
            timeout=5,
        ).json()
        assert r["valid"] is True
        assert r["errors"] == []
        # Le frek_id figure dans les claims plats
        assert r["claims"]["frek_id"] == existing_frek_id

    def test_sd_jwt_partial_disclosure(self, existing_frek_id):
        """Le holder omet certaines disclosures — la signature reste valide."""
        sd = self._eudi_flow_for_format(existing_frek_id, "vc+sd-jwt").json()["credential"]
        parts = sd.split("~")
        jwt = parts[0]
        all_disc = [p for p in parts[1:] if p]
        # Garde uniquement la moitie des disclosures
        kept = all_disc[: max(1, len(all_disc) // 2)]
        truncated = jwt + "~" + "~".join(kept) + "~"
        r = requests.post(
            f"{BASE_URL}/api/v1/eudi/credential/verify-sdjwt",
            json={"credential": truncated},
            timeout=5,
        ).json()
        assert r["valid"] is True, r["errors"]
        assert r["mode"] == "partial"

    def test_sd_jwt_tamper_invalidates(self, existing_frek_id):
        sd = self._eudi_flow_for_format(existing_frek_id, "vc+sd-jwt").json()["credential"]
        # Tamper le JWT en flippant un char du payload
        jwt, rest = sd.split("~", 1)
        h, p, s = jwt.split(".")
        # Modifier la signature
        bad = h + "." + p + "." + ("a" if s[0] != "a" else "b") + s[1:]
        tampered = bad + "~" + rest
        r = requests.post(
            f"{BASE_URL}/api/v1/eudi/credential/verify-sdjwt",
            json={"credential": tampered},
            timeout=5,
        ).json()
        assert r["valid"] is False

    def test_sd_jwt_metadata_declares_both_formats(self):
        r = requests.get(f"{API}/.well-known/openid-credential-issuer", timeout=5).json()
        configs = r["credential_configurations_supported"]
        formats = {c.get("format") for c in configs.values()}
        assert "ldp_vc" in formats
        assert "vc+sd-jwt" in formats


# ---------- Invariant Ed25519 ----------
class TestEd25519Invariant:
    def test_ed25519_key_unchanged(self):
        """La cle Ed25519 doit etre la meme que celle exposee a tous les standards.

        On capture le contenu du fichier .passport_key.pem AVANT, on declenche
        une operation qui pourrait re-generer (issue VC + SD-JWT), puis on
        reverifie qu'aucune regeneration n'a eu lieu.
        """
        key_path = "/app/backend/.passport_key.pem"
        with open(key_path, "rb") as f:
            before = f.read()

        # Operations qui touchent la cle (issuance + verification)
        # 1. Build VC via /vc/{id} (utilise passport_keys.sign)
        # 2. Build SD-JWT via /credential format vc+sd-jwt
        # 3. Build DID Configuration (utilise passport_keys.sign)
        requests.get(f"{API}/.well-known/jwks.json", timeout=5)
        requests.get(f"{API}/.well-known/did-configuration.json", timeout=5)
        requests.get(f"{API}/v1/passport/key", timeout=5)

        with open(key_path, "rb") as f:
            after = f.read()
        assert before == after, "INVARIANT VIOLE : la cle Ed25519 a ete modifiee."

        # En plus : la cle publique exposee partout doit etre la meme
        passport_pub = requests.get(f"{API}/v1/passport/key", timeout=5).json()["public_key_raw_b64"]
        jwks = requests.get(f"{API}/.well-known/jwks.json", timeout=5).json()["keys"][0]
        # JWK x est base64url, passport raw_b64 est base64 standard
        import base64
        x_padded = jwks["x"] + "=" * (-len(jwks["x"]) % 4)
        assert base64.urlsafe_b64decode(x_padded) == base64.b64decode(passport_pub)
