"""FREK Cultural Fingerprint Layer (Phase 5) — Tests E2E.

Couvre les 7 couches, le consentement segmente, la purge, le matching cosinus,
et le respect strict des invariants (consent_required quand opt-out).
"""

import os
import secrets

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/core/fingerprint"
INGEST = f"{BASE_URL}/api/core/ingest"

ADMIN_KEY = os.environ.get("SECRET_KEY", "")
KILTIKONET_SECRET = os.environ.get("FREKCORE_SECRET_KILTIKONET")


def H_admin():
    return {"X-Admin-Key": ADMIN_KEY}


def H_kiltik():
    return {"Authorization": f"Bearer {KILTIKONET_SECRET}"}


def fresh_frek():
    return f"FREK-CFL-{secrets.token_hex(3).upper()}"


def _ingest(frek_id, badge="CC26-BNV", ts=None):
    body = {
        "frek_id": frek_id,
        "event_id": "CC2026",
        "action": "ACTIVATION",
        "badge_type": badge,
        "timestamp": ts
        or f"2026-05-17T{secrets.randbelow(24):02d}:{secrets.randbelow(60):02d}:00Z",
        "source": "kiltikonet",
    }
    return requests.post(INGEST, headers=H_kiltik(), json=body, timeout=5).json()


@pytest.fixture(scope="module")
def mongo():
    from pymongo import MongoClient

    c = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=2000)
    yield c[os.environ.get("DB_NAME")]
    c.close()


# ---------- Consent segmente ----------
class TestConsent:
    def test_default_all_off(self):
        fid = fresh_frek()
        r = requests.get(f"{API}/consent/{fid}", timeout=5).json()
        for layer in [
            "cadence",
            "affinity",
            "device",
            "social",
            "anomaly",
            "coupling",
            "linguistic",
        ]:
            assert r["layers"][layer] is False

    def test_grant_subset(self):
        fid = fresh_frek()
        r = requests.post(
            f"{API}/consent/{fid}",
            json={"layers": {"cadence": True, "affinity": True}},
            headers=H_admin(),
            timeout=5,
        ).json()
        assert r["updated"]["layers"]["cadence"] is True
        assert r["updated"]["layers"]["affinity"] is True
        # Les autres restent false
        assert r["updated"]["layers"]["device"] is False
        assert r["updated"]["layers"]["social"] is False

    def test_revoke_triggers_purge(self, mongo):
        fid = fresh_frek()
        # Grant device + observe
        requests.post(
            f"{API}/consent/{fid}",
            json={"layers": {"device": True}},
            headers=H_admin(),
            timeout=5,
        )
        requests.post(
            f"{API}/observe/device",
            json={"frek_id": fid, "raw_device_hash": "abc123def"},
            timeout=5,
        )
        assert mongo.frek_device_observations.count_documents({"frek_id": fid}) == 1
        # Revoke device
        r = requests.post(
            f"{API}/consent/{fid}",
            json={"layers": {"device": False}},
            headers=H_admin(),
            timeout=5,
        ).json()
        assert "device" in r["purged_layers"]
        # Les observations sont effacees (RGPD)
        assert mongo.frek_device_observations.count_documents({"frek_id": fid}) == 0


# ---------- P0 fix regression (docs/decisions/0001-founder-decisions-2026-08-31.md) ----------
class TestConsentWriteAuth:
    """POST /consent/{frek_id} was reachable with no credential at all before
    this fix — anyone could silently flip another FREK-ID's tracking consent.
    Proves the fix actually rejects an unauthorized write and that a
    legitimate (admin-keyed) write still works."""

    def test_consent_write_without_admin_key_is_rejected(self):
        fid = fresh_frek()
        r = requests.post(
            f"{API}/consent/{fid}", json={"layers": {"cadence": True}}, timeout=5
        )
        assert r.status_code == 403
        # And the mutation must not have applied
        after = requests.get(f"{API}/consent/{fid}", timeout=5).json()
        assert after["layers"]["cadence"] is False

    def test_consent_write_with_wrong_admin_key_is_rejected(self):
        fid = fresh_frek()
        r = requests.post(
            f"{API}/consent/{fid}",
            json={"layers": {"cadence": True}},
            headers={"X-Admin-Key": "definitely-not-the-real-key"},
            timeout=5,
        )
        assert r.status_code == 403

    def test_consent_write_with_admin_key_still_works(self):
        fid = fresh_frek()
        r = requests.post(
            f"{API}/consent/{fid}",
            json={"layers": {"cadence": True}},
            headers=H_admin(),
            timeout=5,
        )
        assert r.status_code == 200
        assert r.json()["updated"]["layers"]["cadence"] is True


# ---------- P1: real per-holder authorization ----------
# docs/architecture/FREK_ID_RECONCILIATION.md #3 / reports/FREKCORE_COMPLETION_BACKLOG.md
# P1 #3 — replaces the P0 interim admin-key-only gate above with a real
# holder path, kept alongside (not instead of) the admin override.
class TestHolderAuth:
    """The admin-key tests above still pass unchanged (that path is
    preserved) — these prove the new holder path actually works, and that
    it stays correctly subject-scoped (a session can't act for a frek_id
    it doesn't own or hasn't linked)."""

    @pytest.fixture()
    def holder_session(self):
        import sys
        from pathlib import Path

        backend_dir = Path(__file__).resolve().parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        from identity_engine import service as identity_service

        r = requests.post(
            f"{BASE_URL}/api/v1/identity/init",
            json={"identity_type": "individual"},
            timeout=5,
        )
        assert r.status_code == 200, r.text
        frek_id = r.json()["frek_id"]
        token = identity_service.issue_session_token(frek_id)
        return frek_id, token

    @staticmethod
    def H_holder(token):
        return {"X-FREK-Session": token}

    def test_consent_write_with_own_holder_session_works(self, holder_session):
        frek_id, token = holder_session
        r = requests.post(
            f"{API}/consent/{frek_id}",
            json={"layers": {"device": True}},
            headers=self.H_holder(token),
            timeout=5,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["layers"]["device"] is True

    def test_consent_write_with_holder_session_for_a_different_frek_id_is_rejected(
        self, holder_session
    ):
        _frek_id, token = holder_session
        r = requests.post(
            f"{API}/consent/{fresh_frek()}",
            json={"layers": {"device": True}},
            headers=self.H_holder(token),
            timeout=5,
        )
        assert r.status_code == 403

    def test_consent_write_via_linked_object_works(self, holder_session):
        """The frek_id fingerprint actually keys by is often not an
        identity_engine person at all (e.g. a frek_v1-minted UUID —
        frek_v1 has no holder-session concept of its own, see
        docs/architecture/FREK_ID_RECONCILIATION.md). POST
        /identity/link-object is the existing mechanism ("this object is
        mine") that lets a real holder session cover it anyway."""
        _frek_id, token = holder_session
        external_fp_id = fresh_frek()
        link = requests.post(
            f"{BASE_URL}/api/v1/identity/link-object",
            json={"object_id": external_fp_id},
            headers=self.H_holder(token),
            timeout=5,
        )
        assert link.status_code == 200, link.text
        r = requests.post(
            f"{API}/consent/{external_fp_id}",
            json={"layers": {"device": True}},
            headers=self.H_holder(token),
            timeout=5,
        )
        assert r.status_code == 200, r.text

    def test_get_fingerprint_with_own_holder_session_works(self, holder_session):
        frek_id, token = holder_session
        r = requests.get(f"{API}/{frek_id}", headers=self.H_holder(token), timeout=5)
        assert r.status_code == 200, r.text

    def test_export_with_own_holder_session_works_without_export_key(
        self, holder_session
    ):
        frek_id, token = holder_session
        r = requests.get(
            f"{API}/export/{frek_id}", headers=self.H_holder(token), timeout=5
        )
        assert r.status_code == 200, r.text

    def test_match_still_requires_admin_even_with_a_valid_holder_session(
        self, holder_session
    ):
        """/match deliberately was NOT widened (see fingerprint/routes.py's
        match() docstring) — cross-subject, a single holder can't prove
        authority over the other frek_id too."""
        frek_id, token = holder_session
        r = requests.post(
            f"{API}/match",
            json={"frek_id_a": frek_id, "frek_id_b": fresh_frek()},
            headers=self.H_holder(token),
            timeout=5,
        )
        assert r.status_code == 403


# ---------- Observe ----------
class TestObserve:
    def test_device_observe_requires_consent(self):
        fid = fresh_frek()
        r = requests.post(
            f"{API}/observe/device",
            json={"frek_id": fid, "raw_device_hash": "x" * 16},
            timeout=5,
        ).json()
        assert r["recorded"] is False
        assert r["reason"] == "consent_required"

    def test_device_observe_records_when_consented(self):
        fid = fresh_frek()
        requests.post(
            f"{API}/consent/{fid}",
            json={"layers": {"device": True}},
            headers=H_admin(),
            timeout=5,
        )
        r = requests.post(
            f"{API}/observe/device",
            json={"frek_id": fid, "raw_device_hash": "deadbeef1234"},
            timeout=5,
        ).json()
        assert r["recorded"] is True
        assert "device_hash_prefix" in r

    def test_nfc_coupling_requires_consent(self):
        fid = fresh_frek()
        r = requests.post(
            f"{API}/observe/nfc",
            json={"frek_id": fid, "nfc_scan_id": "scan-1"},
            timeout=5,
        ).json()
        assert r["recorded"] is False

    def test_nfc_then_web_couples(self):
        fid = fresh_frek()
        requests.post(
            f"{API}/consent/{fid}",
            json={"layers": {"coupling": True}},
            headers=H_admin(),
            timeout=5,
        )
        requests.post(
            f"{API}/observe/nfc",
            json={"frek_id": fid, "nfc_scan_id": "scan-XYZ"},
            timeout=5,
        )
        r = requests.post(
            f"{API}/observe/web-verify",
            json={"frek_id": fid, "nfc_scan_id": "scan-XYZ"},
            timeout=5,
        ).json()
        assert r["coupled"] is True


# ---------- Read fingerprint ----------
class TestReadFingerprint:
    def test_admin_only(self):
        fid = fresh_frek()
        r = requests.get(f"{API}/{fid}", timeout=5)
        assert r.status_code == 403

    def test_consent_gates_each_layer(self):
        fid = fresh_frek()
        _ingest(fid)
        # Aucune couche consentie
        r = requests.get(f"{API}/{fid}", headers=H_admin(), timeout=5).json()
        for layer in [
            "cadence",
            "affinity",
            "device",
            "social",
            "anomaly",
            "coupling",
            "linguistic",
        ]:
            assert r["layers"][layer]["available"] is False
            assert r["layers"][layer].get("reason") == "consent_required"

    def test_cadence_computes_when_consented(self):
        fid = fresh_frek()
        for i in range(4):
            _ingest(
                fid,
                ts=f"2026-05-17T10:0{i}:00Z",
                badge="CC26-BNV" if i % 2 else "CC26-ART",
            )
        requests.post(
            f"{API}/consent/{fid}",
            json={"layers": {"cadence": True}},
            headers=H_admin(),
            timeout=5,
        )
        r = requests.get(f"{API}/{fid}", headers=H_admin(), timeout=5).json()
        c = r["layers"]["cadence"]
        assert c["available"] is True
        assert c["event_count"] >= 1
        assert "hour_histogram" in c
        assert len(c["hour_histogram"]) == 24

    def test_affinity_vector_normalized(self):
        fid = fresh_frek()
        for i in range(3):
            _ingest(fid, badge="CC26-ART", ts=f"2026-05-17T0{i}:00:00Z")
        requests.post(
            f"{API}/consent/{fid}",
            json={"layers": {"affinity": True}},
            headers=H_admin(),
            timeout=5,
        )
        r = requests.get(f"{API}/{fid}", headers=H_admin(), timeout=5).json()
        v = r["layers"]["affinity"]
        assert v["available"] is True
        assert v["dim"] == 64
        assert len(v["vector"]) == 64
        # Norme L2 ~= 1
        n2 = sum(x * x for x in v["vector"])
        assert 0.95 < n2 < 1.05


# ---------- Match cosinus ----------
class TestMatch:
    def test_match_two_similar_freks(self):
        f1, f2 = fresh_frek(), fresh_frek()
        # Profils tres similaires : memes badges, memes events
        for f in (f1, f2):
            for i in range(3):
                _ingest(f, badge="CC26-ART", ts=f"2026-05-17T0{i}:00:00Z")
            requests.post(
                f"{API}/consent/{f}",
                json={"layers": {"affinity": True}},
                headers=H_admin(),
                timeout=5,
            )
        r = requests.post(
            f"{API}/match",
            json={"frek_id_a": f1, "frek_id_b": f2},
            headers=H_admin(),
            timeout=5,
        ).json()
        assert r["available"] is True
        assert r["similarity"] > 0.5  # profils proches

    def test_match_requires_consent_on_both(self):
        f1, f2 = fresh_frek(), fresh_frek()
        requests.post(
            f"{API}/consent/{f1}",
            json={"layers": {"affinity": True}},
            headers=H_admin(),
            timeout=5,
        )
        # f2 n'a pas consenti
        r = requests.post(
            f"{API}/match",
            json={"frek_id_a": f1, "frek_id_b": f2},
            headers=H_admin(),
            timeout=5,
        )
        assert r.status_code == 403


# ---------- Anomaly + Device collision ----------
class TestAnomalyAndDevice:
    def test_anomaly_bot_signal_high_for_regular_cadence(self, mongo):
        fid = fresh_frek()
        # Injection directe Mongo : cadence parfaitement reguliere (10s entre events)
        # Bypass des variations reseau qui font echouer le test en suite complete.
        from datetime import datetime, timezone, timedelta

        base = datetime.now(timezone.utc) - timedelta(minutes=10)
        for i in range(8):
            t = (base + timedelta(seconds=i * 10)).isoformat()
            mongo.frek_events.insert_one(
                {
                    "frek_id": fid,
                    "event_id": "TEST-ANOMALY",
                    "action": "ACTIVATION",
                    "badge_type": "CC26-BNV",
                    "source": "kiltikonet",
                    "timestamp": t,
                    "ingested_at": t,
                    "score_delta": 0,
                    "idempotency_key": f"anom-{fid}-{i}",
                }
            )
        requests.post(
            f"{API}/consent/{fid}",
            json={"layers": {"anomaly": True}},
            headers=H_admin(),
            timeout=5,
        )
        r = requests.get(f"{API}/{fid}", headers=H_admin(), timeout=5).json()
        a = r["layers"]["anomaly"]
        assert a["available"] is True
        # Cadence parfaitement reguliere => CV proche de 0 => bot_signal proche de 1
        assert a["bot_signal"] >= 0.9, f"got {a['bot_signal']}, cv={a['cadence_cv']}"
        # Cleanup
        mongo.frek_events.delete_many({"frek_id": fid})

    def test_device_collision_detected(self):
        f1, f2 = fresh_frek(), fresh_frek()
        for f in (f1, f2):
            requests.post(
                f"{API}/consent/{f}",
                json={"layers": {"device": True}},
                headers=H_admin(),
                timeout=5,
            )
            requests.post(
                f"{API}/observe/device",
                json={"frek_id": f, "raw_device_hash": "SHARED-DEVICE-XYZ"},
                timeout=5,
            )
        r = requests.get(f"{API}/{f1}", headers=H_admin(), timeout=5).json()
        d = r["layers"]["device"]
        assert d["available"] is True
        # f1 doit voir au moins 1 device partage
        assert len(d["shared_devices"]) >= 1
        assert d["shared_devices"][0]["shared_with_count"] >= 1


# ---------- Social ----------
class TestSocial:
    def test_social_copresence(self):
        f1, f2 = fresh_frek(), fresh_frek()
        shared_event = f"EVT-SHARED-{secrets.token_hex(3)}"
        for f in (f1, f2):
            body = {
                "frek_id": f,
                "event_id": shared_event,
                "action": "ACTIVATION",
                "badge_type": "CC26-BNV",
                "timestamp": f"2026-05-17T10:{secrets.randbelow(60):02d}:00Z",
                "source": "kiltikonet",
            }
            requests.post(INGEST, headers=H_kiltik(), json=body, timeout=5)
            requests.post(
                f"{API}/consent/{f}",
                json={"layers": {"social": True}},
                headers=H_admin(),
                timeout=5,
            )
        r = requests.get(f"{API}/{f1}", headers=H_admin(), timeout=5).json()
        s = r["layers"]["social"]
        assert s["available"] is True
        # Au moins une co-presence (f2)
        assert s["co_presence_count"] >= 1


# ---------- Export RGPD ----------
class TestExport:
    def test_export_returns_all_layers(self):
        fid = fresh_frek()
        _ingest(fid)
        # Consent all
        requests.post(
            f"{API}/consent/{fid}",
            json={
                "layers": {
                    l: True
                    for l in [
                        "cadence",
                        "affinity",
                        "device",
                        "social",
                        "anomaly",
                        "coupling",
                        "linguistic",
                    ]
                }
            },
            headers=H_admin(),
            timeout=5,
        )
        r = requests.get(
            f"{API}/export/{fid}", headers={"X-Export-Key": ADMIN_KEY}, timeout=5
        ).json()
        assert r["frek_id"] == fid
        assert "consent" in r
        for layer in [
            "cadence",
            "affinity",
            "device",
            "social",
            "anomaly",
            "coupling",
            "linguistic",
        ]:
            assert layer in r["layers"]
        assert "CVLN Group" in r["ownership"]
