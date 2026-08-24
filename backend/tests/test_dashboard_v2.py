"""
FREK v2 Dashboard & Admin Tests - CC2026 Monitor Operationnel
Tests dashboard endpoints, admin X-Admin-Key protection, and RGPD deletion.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://culture-chain.preview.emergentagent.com"

# Admin key from .env - must be passed as X-Admin-Key header
ADMIN_KEY = os.environ.get("SECRET_KEY", "")

# Client credentials for creating test identities
KILTIKONET_CLIENT_ID = os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")
KILTIKONET_SECRET = os.environ.get("FREK_CLIENT_KILTIKONET_SECRET", "")


class TestDashboardCC2026:
    """GET /api/v1/dashboard/cc2026 - Dashboard consolidated metrics"""
    
    def test_dashboard_cc2026_returns_metrics(self):
        """Dashboard endpoint returns consolidated CC2026 metrics"""
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/cc2026")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify required fields
        assert data["event"] == "CC2026", f"Expected event 'CC2026', got {data.get('event')}"
        assert "timestamp" in data, "Response should contain timestamp"
        assert data["system_status"] == "connected", f"Expected system_status 'connected', got {data.get('system_status')}"
        assert data["target"] == 40000, f"Expected target 40000, got {data.get('target')}"
        
        # Verify metrics object
        metrics = data.get("metrics", {})
        assert "total_identities" in metrics, "metrics should contain total_identities"
        assert "active_identities" in metrics, "metrics should contain active_identities"
        assert "total_all_clients" in metrics, "metrics should contain total_all_clients"
        assert "progression_percent" in metrics, "metrics should contain progression_percent"
        
        # Verify other required structures
        assert "stages_breakdown" in data, "Response should contain stages_breakdown"
        assert "luciole_funnel" in data, "Response should contain luciole_funnel"
        assert "timeline_30d" in data, "Response should contain timeline_30d"
        assert "clients_activity" in data, "Response should contain clients_activity"
        
        print(f"✓ Dashboard CC2026 - total: {metrics['total_identities']}, active: {metrics['active_identities']}, progression: {metrics['progression_percent']}%")
    
    def test_dashboard_luciole_funnel_has_5_stages(self):
        """Luciole funnel should have all 5 stages"""
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/cc2026")
        assert response.status_code == 200
        
        data = response.json()
        funnel = data.get("luciole_funnel", [])
        
        # Should have exactly 5 stages
        assert len(funnel) == 5, f"Expected 5 stages in funnel, got {len(funnel)}"
        
        expected_stages = ["GENESIS", "WORKSHOP", "METAMORPHOSE", "EMISSION", "LEGACY"]
        funnel_stages = [f["stage"] for f in funnel]
        
        for stage in expected_stages:
            assert stage in funnel_stages, f"Stage {stage} missing from funnel"
        
        # Each funnel item should have stage and count
        for item in funnel:
            assert "stage" in item, "Funnel item should have 'stage'"
            assert "count" in item, "Funnel item should have 'count'"
            assert isinstance(item["count"], int), f"count should be int, got {type(item['count'])}"
        
        print(f"✓ Luciole funnel has all 5 stages: {funnel_stages}")
        for item in funnel:
            print(f"  - {item['stage']}: {item['count']}")
    
    def test_dashboard_cc2026_with_admin_key_returns_more_data(self):
        """Dashboard with X-Admin-Key returns recent_activity and admin_mode"""
        # Without admin key
        response_no_key = requests.get(f"{BASE_URL}/api/v1/dashboard/cc2026")
        data_no_key = response_no_key.json()
        assert "admin_mode" not in data_no_key, "Without admin key, admin_mode should not be present"
        assert "recent_activity" not in data_no_key, "Without admin key, recent_activity should not be present"
        
        # With admin key
        response_with_key = requests.get(
            f"{BASE_URL}/api/v1/dashboard/cc2026",
            headers={"X-Admin-Key": ADMIN_KEY}
        )
        assert response_with_key.status_code == 200
        data_with_key = response_with_key.json()
        
        assert data_with_key.get("admin_mode") == True, "With admin key, admin_mode should be True"
        assert "recent_activity" in data_with_key, "With admin key, recent_activity should be present"
        
        print("✓ Dashboard with X-Admin-Key returns admin_mode=True and recent_activity")


class TestDashboardLive:
    """GET /api/v1/dashboard/cc2026/live - Lightweight live polling endpoint"""
    
    def test_live_endpoint_returns_lightweight_metrics(self):
        """Live endpoint returns lightweight metrics for polling"""
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/cc2026/live")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify required fields
        assert "total" in data, "Response should contain total"
        assert "active" in data, "Response should contain active"
        assert "target" in data, "Response should contain target"
        assert "percentage" in data, "Response should contain percentage"
        assert "last_activity" in data, "Response should contain last_activity"
        assert "ts" in data, "Response should contain ts (timestamp)"
        
        # Verify target is 40000
        assert data["target"] == 40000, f"Expected target 40000, got {data.get('target')}"
        
        # Verify types
        assert isinstance(data["total"], int), f"total should be int, got {type(data['total'])}"
        assert isinstance(data["active"], int), f"active should be int, got {type(data['active'])}"
        assert isinstance(data["percentage"], (int, float)), f"percentage should be numeric"
        
        print(f"✓ Live endpoint - total: {data['total']}, active: {data['active']}, percentage: {data['percentage']}%")
        
        # Verify last_activity structure if present
        if data["last_activity"]:
            last_activity = data["last_activity"]
            print(f"  - Last activity: stage={last_activity.get('stage')}, frek_id={last_activity.get('frek_id')}")


class TestAdminEndpointsXAdminKey:
    """Admin endpoints require X-Admin-Key header"""
    
    @pytest.fixture
    def kiltikonet_token(self):
        """Get OAuth token for creating test data"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": KILTIKONET_CLIENT_ID,
            "client_secret": KILTIKONET_SECRET,
            "grant_type": "client_credentials"
        })
        return response.json()["access_token"]
    
    def test_list_clients_no_auth_required(self):
        """GET /api/v1/admin/clients - public (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/v1/admin/clients")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "clients" in data
        assert isinstance(data["clients"], list)
        
        # Verify kiltikonet and cvl-brain are present
        client_ids = [c["client_id"] for c in data["clients"]]
        assert "kiltikonet-cc2026" in client_ids
        assert "cvl-brain" in client_ids
        
        print(f"✓ GET /api/v1/admin/clients - {len(data['clients'])} clients (public endpoint)")
    
    def test_create_client_without_admin_key_returns_403(self):
        """POST /api/v1/admin/clients without X-Admin-Key returns 403 (intentional silence)"""
        response = requests.post(
            f"{BASE_URL}/api/v1/admin/clients",
            json={
                "client_id": "test-unauthorized",
                "name": "Unauthorized Client",
                "permissions": ["stats"]
            }
        )
        # Without X-Admin-Key header, Phase 2.5 returns 403 (silence de l'autorite)
        assert response.status_code == 403, f"Expected 403 without X-Admin-Key, got {response.status_code}"
        print("✓ POST /api/v1/admin/clients without X-Admin-Key returns 403")
    
    def test_create_client_with_invalid_admin_key_returns_403(self):
        """POST /api/v1/admin/clients with invalid X-Admin-Key returns 403"""
        response = requests.post(
            f"{BASE_URL}/api/v1/admin/clients",
            headers={"X-Admin-Key": "invalid-admin-key"},
            json={
                "client_id": "test-invalid-key",
                "name": "Invalid Key Client",
                "permissions": ["stats"]
            }
        )
        assert response.status_code == 403, f"Expected 403 with invalid key, got {response.status_code}"
        print("✓ POST /api/v1/admin/clients with invalid X-Admin-Key returns 403")
    
    def test_create_client_with_valid_admin_key_succeeds(self):
        """POST /api/v1/admin/clients with valid X-Admin-Key succeeds"""
        new_client_id = f"TEST_admin_{uuid.uuid4().hex[:6]}"
        
        response = requests.post(
            f"{BASE_URL}/api/v1/admin/clients",
            headers={"X-Admin-Key": ADMIN_KEY},
            json={
                "client_id": new_client_id,
                "name": "Admin Created Client",
                "permissions": ["stats"]
            }
        )
        assert response.status_code == 200, f"Expected 200 with valid key, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["client_id"] == new_client_id
        assert "client_secret" in data
        print(f"✓ POST /api/v1/admin/clients with valid X-Admin-Key - created {new_client_id}")
    
    def test_delete_client_without_admin_key_returns_403(self):
        """DELETE /api/v1/admin/clients/{id} without X-Admin-Key returns 403 (Phase 2.5 silence)"""
        response = requests.delete(f"{BASE_URL}/api/v1/admin/clients/nonexistent-client")
        assert response.status_code == 403, f"Expected 403 without X-Admin-Key, got {response.status_code}"
        print("✓ DELETE /api/v1/admin/clients/{id} without X-Admin-Key returns 403")
    
    def test_delete_client_with_invalid_admin_key_returns_403(self):
        """DELETE /api/v1/admin/clients/{id} with invalid X-Admin-Key returns 403"""
        response = requests.delete(
            f"{BASE_URL}/api/v1/admin/clients/nonexistent-client",
            headers={"X-Admin-Key": "invalid-key"}
        )
        assert response.status_code == 403, f"Expected 403 with invalid key, got {response.status_code}"
        print("✓ DELETE /api/v1/admin/clients/{id} with invalid X-Admin-Key returns 403")
    
    def test_delete_client_with_valid_admin_key_and_nonexistent_returns_404(self):
        """DELETE /api/v1/admin/clients/{id} with valid key but nonexistent client returns 404"""
        response = requests.delete(
            f"{BASE_URL}/api/v1/admin/clients/nonexistent-client-12345",
            headers={"X-Admin-Key": ADMIN_KEY}
        )
        assert response.status_code == 404, f"Expected 404 for nonexistent client, got {response.status_code}"
        print("✓ DELETE /api/v1/admin/clients/{id} - nonexistent client returns 404")


class TestRGPDDeletionEndpoint:
    """DELETE /api/v1/admin/identity/{id}/gdpr - RGPD right to erasure"""
    
    @pytest.fixture
    def kiltikonet_token(self):
        """Get OAuth token for creating test data"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json={
            "client_id": KILTIKONET_CLIENT_ID,
            "client_secret": KILTIKONET_SECRET,
            "grant_type": "client_credentials"
        })
        return response.json()["access_token"]
    
    def test_rgpd_delete_without_admin_key_returns_403(self):
        """DELETE /api/v1/admin/identity/{id}/gdpr without X-Admin-Key returns 403 (Phase 2.5 silence)"""
        response = requests.delete(f"{BASE_URL}/api/v1/admin/identity/fake-frek-id/gdpr")
        assert response.status_code == 403, f"Expected 403 without X-Admin-Key, got {response.status_code}"
        print("✓ RGPD delete without X-Admin-Key returns 403")
    
    def test_rgpd_delete_with_invalid_admin_key_returns_403(self):
        """DELETE /api/v1/admin/identity/{id}/gdpr with invalid X-Admin-Key returns 403"""
        response = requests.delete(
            f"{BASE_URL}/api/v1/admin/identity/fake-frek-id/gdpr",
            headers={"X-Admin-Key": "invalid-key"}
        )
        assert response.status_code == 403, f"Expected 403 with invalid key, got {response.status_code}"
        print("✓ RGPD delete with invalid X-Admin-Key returns 403")
    
    def test_rgpd_delete_nonexistent_identity_returns_404(self):
        """DELETE /api/v1/admin/identity/{id}/gdpr with nonexistent frek_id returns 404"""
        response = requests.delete(
            f"{BASE_URL}/api/v1/admin/identity/00000000-0000-0000-0000-000000000000/gdpr",
            headers={"X-Admin-Key": ADMIN_KEY}
        )
        assert response.status_code == 404, f"Expected 404 for nonexistent identity, got {response.status_code}"
        print("✓ RGPD delete nonexistent identity returns 404")
    
    def test_rgpd_delete_creates_and_deletes_identity(self, kiltikonet_token):
        """DELETE /api/v1/admin/identity/{id}/gdpr - full RGPD deletion flow"""
        # Create a test identity
        test_email = f"TEST_gdpr_{uuid.uuid4().hex[:6]}@example.com"
        
        emit_response = requests.post(
            f"{BASE_URL}/api/v1/identity/emit",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={
                "email": test_email,
                "source": "api_test",
                "event": "CC2026"
            }
        )
        assert emit_response.status_code == 200, f"Failed to create identity: {emit_response.text}"
        frek_id = emit_response.json()["frek_id"]
        print(f"  Created test identity: {frek_id}")
        
        # Add a stage to the identity
        stage_response = requests.post(
            f"{BASE_URL}/api/v1/identity/{frek_id}/stage",
            headers={"Authorization": f"Bearer {kiltikonet_token}"},
            json={
                "stage": "WORKSHOP",
                "fingerprint": "g" * 64,
                "source": "gdpr_test"
            }
        )
        assert stage_response.status_code == 200, f"Failed to add stage: {stage_response.text}"
        
        # Verify identity exists
        status_response = requests.get(f"{BASE_URL}/api/v1/identity/{frek_id}/status")
        assert status_response.status_code == 200, "Identity should exist before RGPD delete"
        
        # RGPD Delete
        delete_response = requests.delete(
            f"{BASE_URL}/api/v1/admin/identity/{frek_id}/gdpr",
            headers={"X-Admin-Key": ADMIN_KEY}
        )
        assert delete_response.status_code == 200, f"Expected 200 for RGPD delete, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert data["frek_id"] == frek_id
        assert data["identity_deleted"] == True
        assert "stages_deleted" in data
        assert data["stages_deleted"] >= 1, "Should have deleted at least 1 stage (WORKSHOP)"
        
        print(f"✓ RGPD delete - identity deleted, {data['stages_deleted']} stages deleted")
        
        # Verify identity no longer exists
        verify_response = requests.get(f"{BASE_URL}/api/v1/identity/{frek_id}/status")
        assert verify_response.status_code == 404, "Identity should not exist after RGPD delete"
        print("✓ Identity confirmed deleted (404 on status check)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
