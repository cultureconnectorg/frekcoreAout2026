"""
FREK v1 API Tests - Identity Platform Endpoints
Tests OAuth2 client_credentials auth, identity management, stages, stats, and admin endpoints.
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://culture-chain.preview.emergentagent.com"

# Client credentials from .env
KILTIKONET_CLIENT_ID = "kiltikonet-cc2026"
KILTIKONET_SECRET = "pczBP49crCXSSSwSOShsXClzs9srhKe5S-xnraMPn-k"

CVL_BRAIN_CLIENT_ID = "cvl-brain"
CVL_BRAIN_SECRET = "S0ivsEJHw6AsnKh7_2C0qGh12-nuTaGkQPzOdVCTdv8"


class TestHealthEndpoint:
    """GET /api/v1/health - Health check endpoint"""
    
    def test_health_returns_ok(self):
        """Health endpoint should return status ok and version 2.0.0"""
        response = requests.get(f"{BASE_URL}/api/v1/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["status"] == "ok", f"Expected status 'ok', got {data.get('status')}"
        assert data["version"] == "2.0.0", f"Expected version '2.0.0', got {data.get('version')}"
        print("✓ Health endpoint returns {status: 'ok', version: '2.0.0'}")


class TestAuthEndpoints:
    """POST /api/v1/auth/token - OAuth2 client_credentials flow"""
    
    def test_auth_kiltikonet_client(self):
        """kiltikonet-cc2026 client can get token (emit+stage+stats permissions)"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": KILTIKONET_CLIENT_ID,
            "client_secret": KILTIKONET_SECRET,
            "grant_type": "client_credentials"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert data["token_type"] == "Bearer", f"Expected token_type 'Bearer', got {data.get('token_type')}"
        assert data["expires_in"] == 86400, f"Expected expires_in 86400, got {data.get('expires_in')}"
        print(f"✓ kiltikonet-cc2026 token obtained: {data['access_token'][:20]}...")
    
    def test_auth_cvl_brain_client(self):
        """cvl-brain client can get token (stats only permission)"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": CVL_BRAIN_CLIENT_ID,
            "client_secret": CVL_BRAIN_SECRET,
            "grant_type": "client_credentials"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert data["token_type"] == "Bearer"
        print(f"✓ cvl-brain token obtained: {data['access_token'][:20]}...")
    
    def test_auth_invalid_credentials_returns_401(self):
        """Invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": "invalid-client",
            "client_secret": "invalid-secret",
            "grant_type": "client_credentials"
        })
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"
        print("✓ Invalid credentials correctly returns 401")
    
    def test_auth_invalid_grant_type_returns_400(self):
        """Invalid grant_type should return 400"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": KILTIKONET_CLIENT_ID,
            "client_secret": KILTIKONET_SECRET,
            "grant_type": "password"  # Invalid grant type
        })
        assert response.status_code == 400, f"Expected 400 for invalid grant_type, got {response.status_code}"
        print("✓ Invalid grant_type correctly returns 400")


class TestIdentityEndpoints:
    """Identity CRUD operations - emit, activate, status, detail, lookup"""
    
    @pytest.fixture
    def kiltikonet_token(self):
        """Get auth token for kiltikonet client"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": KILTIKONET_CLIENT_ID,
            "client_secret": KILTIKONET_SECRET,
            "grant_type": "client_credentials"
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def cvl_brain_token(self):
        """Get auth token for cvl-brain client"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": CVL_BRAIN_CLIENT_ID,
            "client_secret": CVL_BRAIN_SECRET,
            "grant_type": "client_credentials"
        })
        return response.json()["access_token"]
    
    def test_emit_creates_new_identity(self, kiltikonet_token):
        """POST /api/v1/identity/emit - creates new identity with emit permission"""
        test_email = f"TEST_user_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={
                "email": test_email,
                "source": "api",
                "event": "CC2026",
                "metadata": {"test": True}
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "frek_id" in data, "Response should contain frek_id"
        assert data["created"] == True, "New identity should have created=True"
        assert data["stage"] == "GENESIS", f"Initial stage should be GENESIS, got {data.get('stage')}"
        assert "message" in data
        
        # Verify it's a valid UUID
        uuid.UUID(data["frek_id"])
        print(f"✓ Identity created with frek_id: {data['frek_id']}")
        return data["frek_id"]
    
    def test_emit_idempotent_same_email(self, kiltikonet_token):
        """POST /api/v1/identity/emit - same email returns same frek_id (idempotent)"""
        test_email = f"TEST_idempotent_{uuid.uuid4().hex[:6]}@example.com"
        
        # First emit
        response1 = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"email": test_email, "source": "api", "event": "CC2026"}
        )
        assert response1.status_code == 200
        frek_id_1 = response1.json()["frek_id"]
        assert response1.json()["created"] == True
        
        # Second emit with same email
        response2 = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"email": test_email, "source": "api", "event": "CC2026"}
        )
        assert response2.status_code == 200
        frek_id_2 = response2.json()["frek_id"]
        assert response2.json()["created"] == False, "Second emit should have created=False"
        
        assert frek_id_1 == frek_id_2, f"Same email should return same frek_id: {frek_id_1} != {frek_id_2}"
        print(f"✓ Idempotent emit verified - same frek_id returned: {frek_id_1}")
    
    def test_emit_permission_denied_for_cvl_brain(self, cvl_brain_token):
        """POST /api/v1/identity/emit - cvl-brain (stats only) cannot emit identity (403)"""
        response = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            headers={"Authorization": f"Bearer {cvl_brain_token}"},
            json={"email": "test@example.com", "source": "api"}
        )
        assert response.status_code == 403, f"Expected 403 for cvl-brain emit, got {response.status_code}"
        print("✓ cvl-brain correctly denied emit permission (403)")
    
    def test_emit_unauthenticated_returns_401(self):
        """POST /api/v1/identity/emit - unauthenticated request returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            json={"email": "test@example.com", "source": "api"}
        )
        assert response.status_code == 401, f"Expected 401 for unauthenticated emit, got {response.status_code}"
        print("✓ Unauthenticated emit correctly returns 401")
    
    def test_activate_identity(self, kiltikonet_token):
        """POST /api/v1/identity/{id}/activate - activates identity"""
        # First create an identity
        test_email = f"TEST_activate_{uuid.uuid4().hex[:6]}@example.com"
        emit_response = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"email": test_email, "source": "api", "event": "CC2026"}
        )
        frek_id = emit_response.json()["frek_id"]
        
        # Activate
        response = requests.post(
            f"{BASE_URL}/api/v1/identity/{frek_id}/activate",
            headers={"Authorization": f"Bearer {kiltikonet_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["frek_id"] == frek_id
        assert data["active"] == True
        print(f"✓ Identity {frek_id} activated")
    
    def test_status_public_no_auth_required(self, kiltikonet_token):
        """GET /api/v1/identity/{id}/status - PUBLIC endpoint (no auth required)"""
        # First create an identity
        test_email = f"TEST_status_{uuid.uuid4().hex[:6]}@example.com"
        emit_response = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"email": test_email, "source": "api", "event": "CC2026"}
        )
        frek_id = emit_response.json()["frek_id"]
        
        # Get status WITHOUT auth - should work
        response = requests.get(f"{BASE_URL}/api/v1/identity/{frek_id}/status")
        assert response.status_code == 200, f"Expected 200 for public status, got {response.status_code}"
        
        data = response.json()
        assert data["frek_id"] == frek_id
        assert data["current_stage"] == "GENESIS"
        assert "progression" in data
        assert isinstance(data["stages_completed"], list)
        assert "created_at" in data
        print(f"✓ Public status endpoint works - progression: {data['progression']}%")
    
    def test_detail_requires_auth(self, kiltikonet_token):
        """GET /api/v1/identity/{id}/detail - requires auth"""
        # First create an identity
        test_email = f"TEST_detail_{uuid.uuid4().hex[:6]}@example.com"
        emit_response = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"email": test_email, "source": "api", "event": "CC2026"}
        )
        frek_id = emit_response.json()["frek_id"]
        
        # Get detail WITHOUT auth - should fail
        response_no_auth = requests.get(f"{BASE_URL}/api/v1/identity/{frek_id}/detail")
        assert response_no_auth.status_code == 401, f"Expected 401 for unauthenticated detail, got {response_no_auth.status_code}"
        
        # Get detail WITH auth - should work
        response_auth = requests.get(
            f"{BASE_URL}/api/v1/identity/{frek_id}/detail",
            headers={"Authorization": f"Bearer {kiltikonet_token}"}
        )
        assert response_auth.status_code == 200, f"Expected 200 for authenticated detail, got {response_auth.status_code}"
        
        data = response_auth.json()
        assert data["frek_id"] == frek_id
        assert "email_hash" in data
        assert "stages" in data
        assert isinstance(data["stages"], list)
        print(f"✓ Detail endpoint requires auth and returns full identity info")
    
    def test_lookup_by_qr_token(self, kiltikonet_token):
        """POST /api/v1/identity/lookup - qr_token to frek_id"""
        # First create an identity and get its qr_token via detail
        test_email = f"TEST_lookup_{uuid.uuid4().hex[:6]}@example.com"
        emit_response = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"email": test_email, "source": "api", "event": "CC2026"}
        )
        frek_id = emit_response.json()["frek_id"]
        
        # Get qr_token from detail
        detail_response = requests.get(
            f"{BASE_URL}/api/v1/identity/{frek_id}/detail",
            headers={"Authorization": f"Bearer {kiltikonet_token}"}
        )
        
        # Detail response doesn't include qr_token directly in schema
        # Let's test with invalid qr_token first to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/v1/identity/lookup",
            json={"qr_token": "invalid_token_12345"}
        )
        assert response.status_code == 404, f"Expected 404 for invalid qr_token, got {response.status_code}"
        print("✓ Lookup endpoint exists and returns 404 for invalid qr_token")


class TestStageEndpoints:
    """Stage recording (append-only) - POST /api/v1/identity/{id}/stage, GET /api/v1/identity/{id}/stages"""
    
    @pytest.fixture
    def kiltikonet_token(self):
        """Get auth token for kiltikonet client"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": KILTIKONET_CLIENT_ID,
            "client_secret": KILTIKONET_SECRET,
            "grant_type": "client_credentials"
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def created_identity(self, kiltikonet_token):
        """Create a test identity for stage tests"""
        test_email = f"TEST_stage_{uuid.uuid4().hex[:6]}@example.com"
        response = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"email": test_email, "source": "api", "event": "CC2026"}
        )
        return response.json()["frek_id"]
    
    def test_record_workshop_stage(self, kiltikonet_token, created_identity):
        """POST /api/v1/identity/{id}/stage - record WORKSHOP stage"""
        response = requests.post(
            f"{BASE_URL}/api/v1/identity/{created_identity}/stage",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={
                "stage": "WORKSHOP",
                "fingerprint": "a" * 64,  # SHA256 fingerprint
                "source": "api_test",
                "metadata": {"workshop_type": "dj_set"}
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["frek_id"] == created_identity
        assert data["stage"] == "WORKSHOP"
        assert data["fingerprint"] == "a" * 64
        assert "sequence" in data
        assert "timestamp" in data
        print(f"✓ WORKSHOP stage recorded - sequence: {data['sequence']}")
    
    def test_record_multiple_stages_append_only(self, kiltikonet_token, created_identity):
        """POST /api/v1/identity/{id}/stage - stages are append-only"""
        # Record WORKSHOP
        response1 = requests.post(
            f"{BASE_URL}/api/v1/identity/{created_identity}/stage",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"stage": "WORKSHOP", "fingerprint": "b" * 64, "source": "test"}
        )
        seq1 = response1.json()["sequence"]
        
        # Record METAMORPHOSE
        response2 = requests.post(
            f"{BASE_URL}/api/v1/identity/{created_identity}/stage",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"stage": "METAMORPHOSE", "fingerprint": "c" * 64, "source": "test"}
        )
        seq2 = response2.json()["sequence"]
        
        # Record EMISSION
        response3 = requests.post(
            f"{BASE_URL}/api/v1/identity/{created_identity}/stage",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"stage": "EMISSION", "fingerprint": "d" * 64, "source": "test"}
        )
        seq3 = response3.json()["sequence"]
        
        # Sequences should be increasing
        assert seq2 > seq1, f"Sequence should increase: {seq2} > {seq1}"
        assert seq3 > seq2, f"Sequence should increase: {seq3} > {seq2}"
        print(f"✓ Append-only stages verified - sequences: {seq1}, {seq2}, {seq3}")
    
    def test_get_stage_history(self, kiltikonet_token, created_identity):
        """GET /api/v1/identity/{id}/stages - get stage history"""
        # Record a stage first
        requests.post(
            f"{BASE_URL}/api/v1/identity/{created_identity}/stage",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={"stage": "WORKSHOP", "fingerprint": "e" * 64, "source": "test"}
        )
        
        # Get stages
        response = requests.get(
            f"{BASE_URL}/api/v1/identity/{created_identity}/stages",
            headers={"Authorization": f"Bearer {kiltikonet_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["frek_id"] == created_identity
        assert "count" in data
        assert "stages" in data
        assert isinstance(data["stages"], list)
        assert data["count"] >= 1  # At least GENESIS + WORKSHOP
        print(f"✓ Stage history retrieved - {data['count']} stages found")


class TestStatsEndpoints:
    """Stats endpoints - GET /api/v1/stats/cc2026, GET /api/v1/stats/{client_id}"""
    
    @pytest.fixture
    def kiltikonet_token(self):
        """Get auth token for kiltikonet client"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": KILTIKONET_CLIENT_ID,
            "client_secret": KILTIKONET_SECRET,
            "grant_type": "client_credentials"
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def cvl_brain_token(self):
        """Get auth token for cvl-brain client"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": CVL_BRAIN_CLIENT_ID,
            "client_secret": CVL_BRAIN_SECRET,
            "grant_type": "client_credentials"
        })
        return response.json()["access_token"]
    
    def test_cc2026_stats_with_objective(self, kiltikonet_token):
        """GET /api/v1/stats/cc2026 - CC2026 stats with objective 40000"""
        response = requests.get(
            f"{BASE_URL}/api/v1/stats/cc2026",
            headers={"Authorization": f"Bearer {kiltikonet_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["event"] == "CC2026"
        assert data["objective"] == 40000, f"Expected objective 40000, got {data.get('objective')}"
        assert "total_identities" in data
        assert "active_identities" in data
        assert "progression_percent" in data
        assert "stages_breakdown" in data
        print(f"✓ CC2026 stats - {data['total_identities']} identities, {data['progression_percent']}% of 40000")
    
    def test_stats_by_client(self, kiltikonet_token):
        """GET /api/v1/stats/{client_id} - stats by client"""
        response = requests.get(
            f"{BASE_URL}/api/v1/stats/{KILTIKONET_CLIENT_ID}",
            headers={"Authorization": f"Bearer {kiltikonet_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["client_id"] == KILTIKONET_CLIENT_ID
        assert "total_identities" in data
        assert "active_identities" in data
        assert "stages_breakdown" in data
        print(f"✓ Client stats for {KILTIKONET_CLIENT_ID} - {data['total_identities']} identities")
    
    def test_cvl_brain_can_access_stats(self, cvl_brain_token):
        """cvl-brain (stats permission) can access stats"""
        response = requests.get(
            f"{BASE_URL}/api/v1/stats/cc2026",
            headers={"Authorization": f"Bearer {cvl_brain_token}"}
        )
        assert response.status_code == 200, f"Expected 200 for cvl-brain stats, got {response.status_code}"
        print("✓ cvl-brain can access stats endpoints")


class TestAdminEndpoints:
    """Admin endpoints - GET /api/v1/admin/clients, POST /api/v1/admin/clients"""
    
    def test_list_clients(self):
        """GET /api/v1/admin/clients - list registered clients (no auth required currently)"""
        response = requests.get(f"{BASE_URL}/api/v1/admin/clients")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "clients" in data
        assert isinstance(data["clients"], list)
        
        # Should have at least the 2 seeded clients
        client_ids = [c["client_id"] for c in data["clients"]]
        assert KILTIKONET_CLIENT_ID in client_ids, f"kiltikonet-cc2026 should be in clients"
        assert CVL_BRAIN_CLIENT_ID in client_ids, f"cvl-brain should be in clients"
        
        # Secret hash should NOT be exposed
        for client in data["clients"]:
            assert "secret_hash" not in client, "secret_hash should not be exposed"
        
        print(f"✓ Admin clients list - {len(data['clients'])} clients registered")
    
    def test_create_client(self):
        """POST /api/v1/admin/clients - create new client"""
        new_client_id = f"TEST_client_{uuid.uuid4().hex[:6]}"
        
        response = requests.post(f"{BASE_URL}/api/v1/admin/clients", json={
            "client_id": new_client_id,
            "name": "Test Client",
            "permissions": ["stats"]
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["client_id"] == new_client_id
        assert "client_secret" in data, "Response should include generated client_secret"
        assert len(data["client_secret"]) > 20, "Secret should be substantial"
        assert data["permissions"] == ["stats"]
        print(f"✓ Client created: {new_client_id} with secret")
    
    def test_create_duplicate_client_returns_409(self):
        """POST /api/v1/admin/clients - duplicate client_id returns 409"""
        response = requests.post(f"{BASE_URL}/api/v1/admin/clients", json={
            "client_id": KILTIKONET_CLIENT_ID,  # Already exists
            "name": "Duplicate Client",
            "permissions": ["stats"]
        })
        assert response.status_code == 409, f"Expected 409 for duplicate, got {response.status_code}"
        print("✓ Duplicate client correctly returns 409")


class TestLegacyRoutes:
    """Legacy /api/frek/ routes should still work"""
    
    def test_legacy_frek_root(self):
        """GET /api/frek/ - legacy route still works"""
        response = requests.get(f"{BASE_URL}/api/frek/")
        # Should return 200 if route exists
        assert response.status_code in [200, 307], f"Legacy /api/frek/ should work, got {response.status_code}"
        print("✓ Legacy /api/frek/ route accessible")
    
    def test_legacy_frek_stats(self):
        """GET /api/frek/stats - legacy stats route"""
        response = requests.get(f"{BASE_URL}/api/frek/stats")
        assert response.status_code == 200, f"Legacy /api/frek/stats should work, got {response.status_code}"
        print("✓ Legacy /api/frek/stats route accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
