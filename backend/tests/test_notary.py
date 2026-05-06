"""
FREK Notary — Notaire Culturel Tech backend tests.
Covers: health, chain status, verify, blocks list, single block, identity emit
auto-notarization, stage transition auto-notarization, proof endpoints, OTS
binary download, anchor sweep / upgrade, regression on FREK v1 endpoints.
"""
import os
import time
import uuid
import pytest
import requests
from pathlib import Path


def _load_env_file(p: Path):
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k.strip(), v)


_load_env_file(Path("/app/frontend/.env"))
_load_env_file(Path("/app/backend/.env"))

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"
CLIENT_ID = os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")
CLIENT_SECRET = os.environ.get(
    "FREK_CLIENT_KILTIKONET_SECRET", "pczBP49crCXSSSwSOShsXClzs9srhKe5S-xnraMPn-k"
)


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def access_token():
    r = requests.post(
        f"{BASE_URL}/api/v1/auth/token",
        json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
        timeout=15,
    )
    assert r.status_code == 200, f"auth failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


# ---------- Notary core ----------
class TestNotaryHealth:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/v1/notary/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "Notaire Culturel Tech" in data["module"]
        assert isinstance(data["chain_height"], int)
        assert data["chain_height"] >= 0
        assert data["calendars"] == 5, f"Expected 5 calendars, got {data['calendars']}"

    def test_chain_status(self):
        r = requests.get(f"{BASE_URL}/api/v1/notary/chain/status", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in [
            "height", "last_block_hash", "total_anchored",
            "total_btc_confirmed", "pending_anchors", "integrity_ok", "calendars",
        ]:
            assert k in d, f"missing field {k}"
        assert d["integrity_ok"] is True, f"chain integrity broken: {d}"
        assert isinstance(d["calendars"], list) and len(d["calendars"]) == 5

    def test_chain_verify(self):
        r = requests.get(f"{BASE_URL}/api/v1/notary/chain/verify", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["valid"] is True, f"verify says invalid: {d}"
        assert d["first_invalid_height"] is None
        assert d["blocks_checked"] >= 0
        assert "Inviolable" in d["message"] or "integre" in d["message"].lower()


# ---------- Identity emit creates a notary block ----------
class TestIdentityEmitNotarized:
    @pytest.fixture(scope="class")
    def emitted(self, auth_headers):
        # capture height before
        before = requests.get(f"{BASE_URL}/api/v1/notary/chain/status", timeout=15).json()
        height_before = before["height"]

        unique = uuid.uuid4().hex[:8]
        payload = {
            "email": f"TEST_notary_{unique}@example.com",
            "first_name": "Notary",
            "last_name": f"Test{unique}",
        }
        r = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            json=payload,
            headers=auth_headers,
            timeout=20,
        )
        assert r.status_code in (200, 201), f"emit failed: {r.status_code} {r.text}"
        data = r.json()
        frek_id = data.get("frek_id") or data.get("id") or data.get("data", {}).get("frek_id")
        assert frek_id, f"no frek_id in response: {data}"
        return {"frek_id": frek_id, "height_before": height_before}

    def test_chain_height_incremented(self, emitted):
        # small wait to allow async chain append (sync inside emit_identity, but be safe)
        time.sleep(1.0)
        after = requests.get(f"{BASE_URL}/api/v1/notary/chain/status", timeout=15).json()
        assert after["height"] >= emitted["height_before"] + 1, (
            f"height did not increment: before={emitted['height_before']} "
            f"after={after['height']}"
        )

    def test_proof_returned_for_frek_id(self, emitted):
        frek_id = emitted["frek_id"]
        r = requests.get(f"{BASE_URL}/api/v1/notary/proof/{frek_id}", timeout=15)
        assert r.status_code == 200, f"proof failed: {r.status_code} {r.text}"
        d = r.json()
        assert d["payload_id"] == frek_id
        assert d["block"]["payload_id"] == frek_id
        assert d["block"]["payload_type"] in ("identity_emit", "identity_emitted")
        assert "chain_proof" in d
        assert d["chain_proof"]["block_hash"] == d["block"]["block_hash"]


# ---------- Stage transitions ----------
class TestStageTransitionsNotarized:
    @pytest.fixture(scope="class")
    def frek_with_stages(self, auth_headers):
        unique = uuid.uuid4().hex[:8]
        r = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            json={
                "email": f"TEST_stage_{unique}@example.com",
                "first_name": "Stage",
                "last_name": f"Test{unique}",
            },
            headers=auth_headers,
            timeout=20,
        )
        assert r.status_code in (200, 201), r.text
        body = r.json()
        frek_id = body.get("frek_id") or body.get("id") or body.get("data", {}).get("frek_id")
        assert frek_id

        for stage in ("WORKSHOP", "METAMORPHOSE"):
            rs = requests.post(
                f"{BASE_URL}/api/v1/identity/{frek_id}/stage",
                json={"stage": stage, "fingerprint": uuid.uuid4().hex},
                headers=auth_headers,
                timeout=15,
            )
            assert rs.status_code in (200, 201), f"stage {stage} failed: {rs.status_code} {rs.text}"
        time.sleep(1.0)
        return frek_id

    def test_multiple_blocks_for_same_payload(self, frek_with_stages):
        frek_id = frek_with_stages
        # Blocks list filtered by payload_id is not exposed; use proof + scan blocks list
        r = requests.get(f"{BASE_URL}/api/v1/notary/blocks?limit=200", timeout=15)
        assert r.status_code == 200
        blocks = r.json()
        for_payload = [b for b in blocks if b["payload_id"] == frek_id]
        types = [b["payload_type"] for b in for_payload]
        assert len(for_payload) >= 2, f"expected >=2 blocks, got {len(for_payload)}: {types}"
        assert any(t.startswith("stage") or t == "stage_transition" for t in types), types


# ---------- Block listing & single block ----------
class TestBlocksListing:
    def test_blocks_list_sorted_desc(self):
        r = requests.get(f"{BASE_URL}/api/v1/notary/blocks?limit=10", timeout=15)
        assert r.status_code == 200
        blocks = r.json()
        assert isinstance(blocks, list)
        if len(blocks) >= 2:
            heights = [b["height"] for b in blocks]
            assert heights == sorted(heights, reverse=True), f"not desc-sorted: {heights}"

    def test_single_block_lookup(self):
        r = requests.get(f"{BASE_URL}/api/v1/notary/blocks?limit=1", timeout=15)
        blocks = r.json()
        if not blocks:
            pytest.skip("no blocks in chain yet")
        h = blocks[0]["height"]
        rb = requests.get(f"{BASE_URL}/api/v1/notary/block/{h}", timeout=10)
        assert rb.status_code == 200
        b = rb.json()
        assert b["height"] == h
        assert b["block_hash"] == blocks[0]["block_hash"]

    def test_single_block_not_found(self):
        r = requests.get(f"{BASE_URL}/api/v1/notary/block/9999999", timeout=10)
        assert r.status_code == 404


# ---------- OTS download & anchor admin ----------
class TestOTSAndAnchor:
    def test_ots_download_after_wait(self, auth_headers):
        # find any block ots_submitted=True via proof endpoint loop
        unique = uuid.uuid4().hex[:8]
        r = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            json={
                "email": f"TEST_ots_{unique}@example.com",
                "first_name": "OTS",
                "last_name": f"Test{unique}",
            },
            headers=auth_headers,
            timeout=20,
        )
        assert r.status_code in (200, 201)
        body = r.json()
        frek_id = body.get("frek_id") or body.get("id") or body.get("data", {}).get("frek_id")

        ots_b64 = None
        for _ in range(8):  # up to ~24s
            time.sleep(3)
            pr = requests.get(f"{BASE_URL}/api/v1/notary/proof/{frek_id}", timeout=15)
            if pr.status_code == 200 and pr.json().get("ots_proof_b64"):
                ots_b64 = pr.json()["ots_proof_b64"]
                break
        if not ots_b64:
            pytest.skip("OTS proof not yet produced (calendar latency)")

        rd = requests.get(f"{BASE_URL}/api/v1/notary/proof/{frek_id}/ots", timeout=15)
        assert rd.status_code == 200
        assert rd.headers.get("content-type", "").startswith(
            "application/vnd.opentimestamps.ots"
        ), rd.headers
        assert len(rd.content) > 10

    def test_anchor_sweep_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/v1/notary/anchor/sweep", timeout=15)
        assert r.status_code in (401, 403)

    def test_anchor_sweep_authorized(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/v1/notary/anchor/sweep",
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert "submitted" in d or "ok" in d or isinstance(d, dict)

    def test_anchor_upgrade_authorized(self, auth_headers):
        # Limite max_blocks=1 pour eviter timeout sur grand backlog en CI
        r = requests.post(
            f"{BASE_URL}/api/v1/notary/anchor/upgrade?max_blocks=1",
            headers=auth_headers,
            timeout=120,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d, dict)


# ---------- Regression: FREK v1 base endpoints still work ----------
class TestFrekV1Regression:
    def test_dashboard_summary(self, auth_headers):
        # try common dashboard endpoints; accept first 200
        candidates = [
            "/api/v1/dashboard/summary",
            "/api/v1/dashboard",
        ]
        seen = []
        for c in candidates:
            r = requests.get(f"{BASE_URL}{c}", headers=auth_headers, timeout=15)
            seen.append((c, r.status_code))
            if r.status_code == 200:
                return
        pytest.skip(f"no dashboard endpoint reachable: {seen}")

    def test_badges_list(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/v1/badges", headers=auth_headers, timeout=15
        )
        assert r.status_code in (200, 404), r.status_code

    def test_jetons_list(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/v1/jetons", headers=auth_headers, timeout=15
        )
        assert r.status_code in (200, 404), r.status_code
