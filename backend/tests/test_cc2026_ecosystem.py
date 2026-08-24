"""
CC2026 Ecosystem Tests - Badges, Jetons, Email, Event
Tests the 4 components of Culture Connect 2026:
1. Badges (14 types) - Creation, activation, confirmation, listing, stats
2. Jetons/Wallet - Packs, recharge, paiement, solde, historique, stats
3. Email SES - Templates, send (log mode), campaign, stats
4. Event J-0 - Zones, scan, access control, live stats
"""
import pytest
import requests
import os
import time
import uuid

# Get BASE_URL from environment - DO NOT add default
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if BASE_URL:
    BASE_URL = BASE_URL.rstrip('/')

# Client credentials for kiltikonet-cc2026
CLIENT_ID = os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")
CLIENT_SECRET = os.environ.get("FREK_CLIENT_KILTIKONET_SECRET", "")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token from FREK v1 auth endpoint"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
    )
    assert response.status_code == 200, f"Auth failed: {response.text}"
    token_data = response.json()
    assert "access_token" in token_data
    return token_data["access_token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


@pytest.fixture(scope="module")
def test_badge_id(api_client):
    """Create a test badge and return its badge_id"""
    unique_id = str(uuid.uuid4())[:8]
    response = api_client.post(f"{BASE_URL}/api/badges/create", json={
        "email": f"test_{unique_id}@cc2026.test",
        "prenom": "Test",
        "nom": "Badge",
        "type_badge": "VIP",
        "organisation": "Test Org",
        "event": "CC2026"
    })
    assert response.status_code == 200
    data = response.json()
    return data["badge"]["badge_id"]


@pytest.fixture(scope="module")
def test_marchand_id(api_client):
    """Create a test marchand and return its marchand_id"""
    unique_id = str(uuid.uuid4())[:8]
    marchand_id = f"test-marchand-{unique_id}"
    response = api_client.post(f"{BASE_URL}/api/jetons/marchands", json={
        "marchand_id": marchand_id,
        "nom": "Test Marchand",
        "stand": "A-01",
        "type_stand": "restauration"
    })
    # May return 409 if already exists, which is fine
    if response.status_code == 409:
        return "stand-food-01"  # Use existing marchand
    assert response.status_code == 200
    return marchand_id


# ==================== BADGES TESTS ====================
class TestBadgesAPI:
    """Test Badge endpoints - 14 types, lifecycle, stats"""
    
    def test_get_badge_types_returns_14_types(self):
        """GET /api/badges/types - returns 14 badge types"""
        response = requests.get(f"{BASE_URL}/api/badges/types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert "count" in data
        assert data["count"] == 14
        # Verify all 14 types are present
        expected_types = ["ART", "INT", "STF", "BNV", "PRS", "VIP", "OFF", "SPO", 
                         "EXP-B", "EXP-S", "EXP-G", "EXP-P", "EXP-D", "EXP-VIP"]
        for badge_type in expected_types:
            assert badge_type in data["types"], f"Missing badge type: {badge_type}"
        print(f"✓ 14 badge types returned: {list(data['types'].keys())}")
    
    def test_create_badge_vip_with_frek_identity(self, api_client):
        """POST /api/badges/create - create VIP badge with FREK identity"""
        unique_id = str(uuid.uuid4())[:8]
        response = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": f"vip_test_{unique_id}@cc2026.test",
            "prenom": "VIP",
            "nom": "Test",
            "type_badge": "VIP",
            "organisation": "Sponsor Premium",
            "event": "CC2026"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == True
        badge = data["badge"]
        assert badge["type_badge"] == "VIP"
        assert badge["nfc_enabled"] == True  # VIP has NFC
        assert badge["statut"] == "INSCRIT"
        assert "frek_id" in badge
        assert "badge_id" in badge
        assert badge["badge_id"].startswith("CC26-VIP-")
        print(f"✓ VIP badge created: {badge['badge_id']}, FREK ID: {badge['frek_id']}")
    
    def test_create_badge_art_type(self, api_client):
        """POST /api/badges/create - create ART (artist) badge"""
        unique_id = str(uuid.uuid4())[:8]
        response = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": f"art_test_{unique_id}@cc2026.test",
            "prenom": "Artiste",
            "nom": "Test",
            "type_badge": "ART",
            "event": "CC2026"
        })
        assert response.status_code == 200
        data = response.json()
        badge = data["badge"]
        assert badge["type_badge"] == "ART"
        assert badge["nfc_enabled"] == False  # ART has no NFC
        assert badge["badge_id"].startswith("CC26-ART-")
        print(f"✓ ART badge created: {badge['badge_id']}")
    
    def test_create_badge_stf_type(self, api_client):
        """POST /api/badges/create - create STF (staff) badge"""
        unique_id = str(uuid.uuid4())[:8]
        response = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": f"stf_test_{unique_id}@cc2026.test",
            "prenom": "Staff",
            "nom": "Test",
            "type_badge": "STF",
            "event": "CC2026"
        })
        assert response.status_code == 200
        data = response.json()
        badge = data["badge"]
        assert badge["type_badge"] == "STF"
        assert badge["badge_id"].startswith("CC26-STF-")
        print(f"✓ STF badge created: {badge['badge_id']}")
    
    def test_create_badge_idempotent_same_email_returns_existing(self, api_client):
        """POST /api/badges/create - idempotent (same email returns existing badge)"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"idempotent_{unique_id}@cc2026.test"
        
        # First creation
        response1 = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": email,
            "prenom": "First",
            "nom": "Test",
            "type_badge": "INT",
            "event": "CC2026"
        })
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["created"] == True
        badge_id = data1["badge"]["badge_id"]
        
        # Second creation with same email
        response2 = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": email,
            "prenom": "Second",
            "nom": "Attempt",
            "type_badge": "VIP",  # Different type
            "event": "CC2026"
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["created"] == False  # Not created, returned existing
        assert data2["badge"]["badge_id"] == badge_id  # Same badge
        assert "idempotent" in data2["message"].lower()
        print(f"✓ Idempotent: same email returns existing badge {badge_id}")
    
    def test_activate_badge(self, api_client, test_badge_id):
        """POST /api/badges/{id}/activate - activate badge"""
        response = api_client.post(f"{BASE_URL}/api/badges/{test_badge_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["badge_id"] == test_badge_id
        assert data["statut"] == "ACTIVE"
        print(f"✓ Badge activated: {test_badge_id}")
    
    def test_confirm_badge(self, api_client, test_badge_id):
        """POST /api/badges/{id}/confirm - confirm badge"""
        response = api_client.post(f"{BASE_URL}/api/badges/{test_badge_id}/confirm")
        assert response.status_code == 200
        data = response.json()
        assert data["badge_id"] == test_badge_id
        assert data["statut"] == "CONFIRME"
        print(f"✓ Badge confirmed: {test_badge_id}")
    
    def test_list_badges_with_filters(self, api_client):
        """GET /api/badges/ - list badges with filters (type, statut)"""
        # List all CC2026 badges
        response = api_client.get(f"{BASE_URL}/api/badges/?event=CC2026")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "badges" in data
        print(f"✓ Listed {data['total']} badges")
        
        # Filter by type
        response = api_client.get(f"{BASE_URL}/api/badges/?type_badge=VIP&event=CC2026")
        assert response.status_code == 200
        data = response.json()
        for badge in data["badges"]:
            assert badge["type_badge"] == "VIP"
        print(f"✓ Filter by type VIP: {data['total']} badges")
    
    def test_badge_stats_overview(self, api_client):
        """GET /api/badges/stats/overview - badge stats by type, statut, NFC count"""
        response = api_client.get(f"{BASE_URL}/api/badges/stats/overview?event=CC2026")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_type" in data
        assert "by_statut" in data
        assert "nfc_count" in data
        print(f"✓ Badge stats: total={data['total']}, by_type={data['by_type']}, nfc_count={data['nfc_count']}")


# ==================== JETONS/WALLET TESTS ====================
class TestJetonsAPI:
    """Test Jetons endpoints - Packs, recharge, paiement, solde, stats"""
    
    def test_list_packs_returns_4_packs(self):
        """GET /api/jetons/packs - list 4 packs (decouverte/culture/diaspora/vip)"""
        response = requests.get(f"{BASE_URL}/api/jetons/packs")
        assert response.status_code == 200
        data = response.json()
        assert "packs" in data
        assert "jeton_value_eur" in data
        assert data["jeton_value_eur"] == 1.50
        
        # Verify all 4 packs
        expected_packs = ["decouverte", "culture", "diaspora", "vip"]
        for pack in expected_packs:
            assert pack in data["packs"], f"Missing pack: {pack}"
        
        # Verify pack values
        assert data["packs"]["decouverte"]["jetons"] == 10
        assert data["packs"]["culture"]["jetons"] == 25
        assert data["packs"]["diaspora"]["jetons"] == 50
        assert data["packs"]["vip"]["jetons"] == 100
        print(f"✓ 4 packs returned: {list(data['packs'].keys())}")
    
    def test_create_marchand(self, api_client):
        """POST /api/jetons/marchands - create marchand"""
        unique_id = str(uuid.uuid4())[:8]
        response = api_client.post(f"{BASE_URL}/api/jetons/marchands", json={
            "marchand_id": f"test-stand-{unique_id}",
            "nom": "Stand Test",
            "stand": "B-02",
            "type_stand": "artisanat"
        })
        assert response.status_code == 200
        data = response.json()
        assert "marchand_id" in data
        assert data["solde_du"] == 0.0
        print(f"✓ Marchand created: {data['marchand_id']}")
    
    def test_recharge_wallet_with_pack(self, api_client, test_badge_id):
        """POST /api/jetons/recharge - recharge wallet with pack"""
        response = api_client.post(f"{BASE_URL}/api/jetons/recharge", json={
            "badge_id": test_badge_id,
            "pack": "decouverte",
            "payment_method": "stripe"
        })
        assert response.status_code == 200
        data = response.json()
        assert "transaction" in data
        assert "new_solde" in data
        tx = data["transaction"]
        assert tx["type"] == "RECHARGE"
        assert tx["montant_jetons"] == 10  # decouverte pack
        assert tx["pack"] == "decouverte"
        print(f"✓ Wallet recharged: +10 jetons, new solde: {data['new_solde']}")
    
    def test_paiement_marchand_debit_badge_credit_marchand(self, api_client, test_badge_id, test_marchand_id):
        """POST /api/jetons/paiement - pay marchand with jetons"""
        # First recharge some jetons
        api_client.post(f"{BASE_URL}/api/jetons/recharge", json={
            "badge_id": test_badge_id,
            "pack": "culture",  # 25 jetons
            "payment_method": "cash"
        })
        
        # Then make a payment
        response = api_client.post(f"{BASE_URL}/api/jetons/paiement", json={
            "badge_id": test_badge_id,
            "montant_jetons": 5,
            "marchand_id": test_marchand_id,
            "description": "Test achat"
        })
        assert response.status_code == 200
        data = response.json()
        assert "transaction" in data
        tx = data["transaction"]
        assert tx["type"] == "PAIEMENT"
        assert tx["montant_jetons"] == 5
        assert tx["montant_eur"] == 7.50  # 5 * 1.50
        print(f"✓ Payment: -5 jetons to {test_marchand_id}")
    
    def test_paiement_insufficient_balance_returns_400(self, api_client):
        """POST /api/jetons/paiement - insufficient balance returns 400"""
        # Create a new badge with 0 balance
        unique_id = str(uuid.uuid4())[:8]
        create_response = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": f"poor_{unique_id}@cc2026.test",
            "prenom": "Poor",
            "nom": "User",
            "type_badge": "BNV",
            "event": "CC2026"
        })
        badge_id = create_response.json()["badge"]["badge_id"]
        
        # Try to pay with 0 balance
        response = api_client.post(f"{BASE_URL}/api/jetons/paiement", json={
            "badge_id": badge_id,
            "montant_jetons": 100,
            "marchand_id": "stand-food-01",
            "description": "Should fail"
        })
        assert response.status_code == 400
        assert "insuffisant" in response.json()["detail"].lower()
        print("✓ Insufficient balance returns 400")
    
    def test_get_solde(self, api_client, test_badge_id):
        """GET /api/jetons/solde/{badge_id} - get balance"""
        response = api_client.get(f"{BASE_URL}/api/jetons/solde/{test_badge_id}")
        assert response.status_code == 200
        data = response.json()
        assert "badge_id" in data
        assert "solde" in data
        assert "jeton_value_eur" in data
        print(f"✓ Solde: {data['solde']} jetons")
    
    def test_get_historique(self, api_client, test_badge_id):
        """GET /api/jetons/historique/{badge_id} - transaction history"""
        response = api_client.get(f"{BASE_URL}/api/jetons/historique/{test_badge_id}")
        assert response.status_code == 200
        data = response.json()
        assert "badge_id" in data
        assert "total" in data
        assert "transactions" in data
        print(f"✓ Transaction history: {data['total']} transactions")
    
    def test_jetons_stats_float_actif(self, api_client):
        """GET /api/jetons/stats - float actif and jetons in circulation"""
        response = api_client.get(f"{BASE_URL}/api/jetons/stats")
        assert response.status_code == 200
        data = response.json()
        assert "jeton_value_eur" in data
        assert "recharges" in data
        assert "paiements" in data
        assert "float_actif" in data
        assert "jetons_en_circulation" in data
        print(f"✓ Jetons stats: float_actif={data['float_actif']}€, circulation={data['jetons_en_circulation']}J")


# ==================== EMAIL SERVICE TESTS ====================
class TestEmailAPI:
    """Test Email endpoints - Templates, send (log mode), campaign, stats"""
    
    def test_list_email_templates_campaign_types(self):
        """GET /api/email/templates - list campaign types"""
        response = requests.get(f"{BASE_URL}/api/email/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "ses_mode" in data
        # AWS SES peut etre connecte (ses) ou en fallback (log) — on accepte les deux
        assert data["ses_mode"] in ("log", "ses")
        
        # Verify campaign types
        expected_types = ["bienvenue", "j-30", "j-15", "j-7", "j-1", "j-0", "j+1", "recharge"]
        for campaign_type in expected_types:
            assert campaign_type in data["templates"], f"Missing template: {campaign_type}"
        print(f"✓ Email templates: {list(data['templates'].keys())}, mode={data['ses_mode']}")
    
    def test_send_individual_email_log_mode(self, api_client, test_badge_id):
        """POST /api/email/send - send individual email (log mode)"""
        response = api_client.post(f"{BASE_URL}/api/email/send", json={
            "badge_id": test_badge_id,
            "template": "bienvenue"
        })
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        email_log = data["email"]
        assert email_log["status"] == "logged"  # Log mode
        assert email_log["template"] == "bienvenue"
        assert "html_preview" in data
        print(f"✓ Email sent (logged): {email_log['subject']}")
    
    def test_launch_campaign_to_all_badges(self, api_client):
        """POST /api/email/campaign - launch campaign to all badges"""
        response = api_client.post(f"{BASE_URL}/api/email/campaign", json={
            "campaign_type": "j-30",
            "event": "CC2026"
        })
        assert response.status_code == 200
        data = response.json()
        assert "campaign_id" in data
        assert "type" in data
        assert data["type"] == "j-30"
        assert "total_badges" in data
        assert "sent" in data
        print(f"✓ Campaign launched: {data['campaign_id']}, sent to {data['sent']}/{data['total_badges']} badges")
    
    def test_email_statistics(self, api_client):
        """GET /api/email/stats - email statistics"""
        response = api_client.get(f"{BASE_URL}/api/email/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_sent" in data
        assert "total_errors" in data
        assert "deliverability" in data
        assert "by_template" in data
        assert "ses_mode" in data
        print(f"✓ Email stats: sent={data['total_sent']}, deliverability={data['deliverability']}%")


# ==================== EVENT J-0 TESTS ====================
class TestEventAPI:
    """Test Event endpoints - Zones, scan, access control, live stats"""
    
    def test_list_zones_with_access_rules(self):
        """GET /api/event/zones - list all zones with access rules"""
        response = requests.get(f"{BASE_URL}/api/event/zones")
        assert response.status_code == 200
        data = response.json()
        assert "zones" in data
        
        # Verify all zones exist
        expected_zones = ["ENTREE", "SCENE", "VIP_LOUNGE", "BACKSTAGE", "EXPOSANTS", "PRESSE", "ATELIERS"]
        for zone in expected_zones:
            assert zone in data["zones"], f"Missing zone: {zone}"
        
        # Verify access rules
        assert "VIP" in data["zones"]["ENTREE"]
        assert "ART" in data["zones"]["SCENE"]
        print(f"✓ Zones: {list(data['zones'].keys())}")
    
    def test_scan_badge_entry_authorized(self, api_client, test_badge_id):
        """POST /api/event/scan - scan badge entry (authorized access)"""
        # Activate the badge first
        api_client.post(f"{BASE_URL}/api/badges/{test_badge_id}/activate")
        
        response = api_client.post(f"{BASE_URL}/api/event/scan", json={
            "badge_id": test_badge_id,
            "zone": "ENTREE",
            "agent_id": "agent-test-01"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["access"] == "AUTORISE"
        assert "scan" in data
        assert "badge_info" in data
        print(f"✓ Scan authorized: {test_badge_id} -> ENTREE")
    
    def test_scan_vip_can_enter_entree_and_vip_lounge(self, api_client):
        """Zone access: VIP can enter ENTREE+VIP_LOUNGE but NOT BACKSTAGE"""
        # Create a VIP badge
        unique_id = str(uuid.uuid4())[:8]
        create_response = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": f"vip_zone_{unique_id}@cc2026.test",
            "prenom": "VIP",
            "nom": "ZoneTest",
            "type_badge": "VIP",
            "event": "CC2026"
        })
        vip_badge_id = create_response.json()["badge"]["badge_id"]
        api_client.post(f"{BASE_URL}/api/badges/{vip_badge_id}/activate")
        
        # VIP can enter ENTREE
        response1 = api_client.post(f"{BASE_URL}/api/event/scan", json={
            "badge_id": vip_badge_id,
            "zone": "ENTREE",
            "agent_id": "agent-test"
        })
        assert response1.status_code == 200
        assert response1.json()["access"] == "AUTORISE"
        print(f"✓ VIP can enter ENTREE")
        
        # VIP can enter VIP_LOUNGE
        response2 = api_client.post(f"{BASE_URL}/api/event/scan", json={
            "badge_id": vip_badge_id,
            "zone": "VIP_LOUNGE",
            "agent_id": "agent-test"
        })
        assert response2.status_code == 200
        assert response2.json()["access"] == "AUTORISE"
        print(f"✓ VIP can enter VIP_LOUNGE")
        
        # VIP CANNOT enter BACKSTAGE
        response3 = api_client.post(f"{BASE_URL}/api/event/scan", json={
            "badge_id": vip_badge_id,
            "zone": "BACKSTAGE",
            "agent_id": "agent-test"
        })
        assert response3.status_code == 403
        assert "non autorise" in response3.json()["detail"].lower()
        print(f"✓ VIP DENIED from BACKSTAGE (403)")
    
    def test_scan_art_can_enter_scene_and_backstage(self, api_client):
        """Zone access: ART can enter SCENE+BACKSTAGE"""
        # Create an ART badge
        unique_id = str(uuid.uuid4())[:8]
        create_response = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": f"art_zone_{unique_id}@cc2026.test",
            "prenom": "Artiste",
            "nom": "ZoneTest",
            "type_badge": "ART",
            "event": "CC2026"
        })
        art_badge_id = create_response.json()["badge"]["badge_id"]
        api_client.post(f"{BASE_URL}/api/badges/{art_badge_id}/activate")
        
        # ART can enter SCENE
        response1 = api_client.post(f"{BASE_URL}/api/event/scan", json={
            "badge_id": art_badge_id,
            "zone": "SCENE",
            "agent_id": "agent-test"
        })
        assert response1.status_code == 200
        assert response1.json()["access"] == "AUTORISE"
        print(f"✓ ART can enter SCENE")
        
        # ART can enter BACKSTAGE
        response2 = api_client.post(f"{BASE_URL}/api/event/scan", json={
            "badge_id": art_badge_id,
            "zone": "BACKSTAGE",
            "agent_id": "agent-test"
        })
        assert response2.status_code == 200
        assert response2.json()["access"] == "AUTORISE"
        print(f"✓ ART can enter BACKSTAGE")
    
    def test_scan_denied_for_wrong_badge_type_in_zone(self, api_client):
        """POST /api/event/scan - denied access for wrong badge type in zone"""
        # Create a PRS (Press) badge
        unique_id = str(uuid.uuid4())[:8]
        create_response = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": f"prs_zone_{unique_id}@cc2026.test",
            "prenom": "Press",
            "nom": "ZoneTest",
            "type_badge": "PRS",
            "event": "CC2026"
        })
        prs_badge_id = create_response.json()["badge"]["badge_id"]
        api_client.post(f"{BASE_URL}/api/badges/{prs_badge_id}/activate")
        
        # PRS cannot enter VIP_LOUNGE
        response = api_client.post(f"{BASE_URL}/api/event/scan", json={
            "badge_id": prs_badge_id,
            "zone": "VIP_LOUNGE",
            "agent_id": "agent-test"
        })
        assert response.status_code == 403
        print(f"✓ PRS DENIED from VIP_LOUNGE (403)")
    
    def test_live_event_stats(self, api_client):
        """GET /api/event/stats/live - real-time event stats"""
        response = api_client.get(f"{BASE_URL}/api/event/stats/live")
        assert response.status_code == 200
        data = response.json()
        assert "event" in data
        assert "scans_total" in data
        assert "badges" in data
        assert "scans_by_zone" in data
        assert "recent_scans" in data
        print(f"✓ Live stats: {data['scans_total']} scans, badges={data['badges']}")


# ==================== FREK STAGE RECORDING TESTS ====================
class TestFrekStageRecording:
    """Test that FREK stages are recorded during CC2026 operations"""
    
    def test_metamorphose_stage_recorded_on_jeton_recharge(self, api_client):
        """FREK stage METAMORPHOSE recorded on jeton recharge"""
        # Create a new badge
        unique_id = str(uuid.uuid4())[:8]
        create_response = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": f"meta_test_{unique_id}@cc2026.test",
            "prenom": "Meta",
            "nom": "Test",
            "type_badge": "VIP",
            "event": "CC2026"
        })
        badge = create_response.json()["badge"]
        frek_id = badge["frek_id"]
        badge_id = badge["badge_id"]
        
        # Recharge wallet (should record METAMORPHOSE)
        api_client.post(f"{BASE_URL}/api/jetons/recharge", json={
            "badge_id": badge_id,
            "pack": "decouverte",
            "payment_method": "cash"
        })
        
        # Check FREK stages
        response = api_client.get(f"{BASE_URL}/api/v1/identity/{frek_id}/stages")
        assert response.status_code == 200
        data = response.json()
        stages = [s["stage"] for s in data["stages"]]
        assert "GENESIS" in stages  # From badge creation
        assert "METAMORPHOSE" in stages  # From jeton recharge
        print(f"✓ METAMORPHOSE stage recorded: {stages}")
    
    def test_emission_stage_recorded_on_scene_scan(self, api_client):
        """FREK stage EMISSION recorded on SCENE/VIP_LOUNGE scan"""
        # Create a VIP badge
        unique_id = str(uuid.uuid4())[:8]
        create_response = api_client.post(f"{BASE_URL}/api/badges/create", json={
            "email": f"emission_test_{unique_id}@cc2026.test",
            "prenom": "Emission",
            "nom": "Test",
            "type_badge": "VIP",
            "event": "CC2026"
        })
        badge = create_response.json()["badge"]
        frek_id = badge["frek_id"]
        badge_id = badge["badge_id"]
        
        # Activate badge
        api_client.post(f"{BASE_URL}/api/badges/{badge_id}/activate")
        
        # Scan into VIP_LOUNGE (should record EMISSION)
        api_client.post(f"{BASE_URL}/api/event/scan", json={
            "badge_id": badge_id,
            "zone": "VIP_LOUNGE",
            "agent_id": "agent-test"
        })
        
        # Check FREK stages
        response = api_client.get(f"{BASE_URL}/api/v1/identity/{frek_id}/stages")
        assert response.status_code == 200
        data = response.json()
        stages = [s["stage"] for s in data["stages"]]
        assert "GENESIS" in stages
        assert "EMISSION" in stages  # From VIP_LOUNGE scan
        print(f"✓ EMISSION stage recorded: {stages}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
