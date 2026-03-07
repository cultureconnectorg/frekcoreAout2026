"""
FREK v2 API Tests - NODE 01-10
================================
Tests for all FREK API endpoints:
- Core endpoints (NODE 01-05): /api/frek/*
- Advanced endpoints (NODE 06-10): /api/frek/advanced/*
"""
import pytest
import requests
import os
import base64
import struct

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestFREKCoreAPI:
    """Core FREK API tests (NODE 01-05)"""
    
    def test_frek_info(self):
        """Test GET /api/frek/ - Basic info endpoint"""
        response = requests.get(f"{BASE_URL}/api/frek/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["frek_version"] == "2.0"
        assert "nodes" in data
        assert "01" in data["nodes"]
        assert "02" in data["nodes"]
        assert "03" in data["nodes"]
        assert "04" in data["nodes"]
        assert "05" in data["nodes"]
        print(f"✓ FREK info: version {data['frek_version']}, {len(data['nodes'])} nodes")
    
    def test_frek_stats(self):
        """Test GET /api/frek/stats - Returns 10 active nodes"""
        response = requests.get(f"{BASE_URL}/api/frek/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "nodes_active" in data
        assert len(data["nodes_active"]) == 10
        
        # Verify all 10 nodes are present
        expected_nodes = [
            "01_extraction", "02_identity", "03_cycle", "04_memory", "05_resonance",
            "06_reseau", "07_transmission", "08_systeme", "09_juridique", "10_institutionnel"
        ]
        for node in expected_nodes:
            assert node in data["nodes_active"], f"Missing node: {node}"
        
        print(f"✓ FREK stats: {len(data['nodes_active'])} nodes active")
    
    def test_certify_audio(self):
        """Test POST /api/frek/certify - Audio certification"""
        # Generate minimal valid WAV file (44100 Hz, 16-bit, mono, ~0.5 sec)
        sample_rate = 44100
        num_samples = int(sample_rate * 0.5)  # 0.5 seconds
        
        # WAV header
        wav_data = bytearray()
        wav_data.extend(b'RIFF')
        file_size = 36 + num_samples * 2  # header + data
        wav_data.extend(struct.pack('<I', file_size))
        wav_data.extend(b'WAVE')
        wav_data.extend(b'fmt ')
        wav_data.extend(struct.pack('<I', 16))  # subchunk1 size
        wav_data.extend(struct.pack('<H', 1))   # PCM format
        wav_data.extend(struct.pack('<H', 1))   # mono
        wav_data.extend(struct.pack('<I', sample_rate))
        wav_data.extend(struct.pack('<I', sample_rate * 2))  # byte rate
        wav_data.extend(struct.pack('<H', 2))   # block align
        wav_data.extend(struct.pack('<H', 16))  # bits per sample
        wav_data.extend(b'data')
        wav_data.extend(struct.pack('<I', num_samples * 2))
        
        # Add silent audio data (zeros)
        wav_data.extend(bytes(num_samples * 2))
        
        audio_base64 = base64.b64encode(bytes(wav_data)).decode('utf-8')
        
        payload = {
            "audio_base64": audio_base64,
            "artiste_id": "TEST-ARTISTE-001"
        }
        
        response = requests.post(f"{BASE_URL}/api/frek/certify", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "frek_id" in data
        assert data["frek_id"].startswith("FREK-")
        assert "extraction" in data
        assert "identity" in data
        assert "cycle" in data
        
        print(f"✓ Certification successful: {data['frek_id']}")
        return data["frek_id"]
    
    def test_certify_invalid_audio(self):
        """Test POST /api/frek/certify - Invalid audio rejection"""
        payload = {
            "audio_base64": base64.b64encode(b"too short").decode('utf-8'),
            "artiste_id": "TEST-ARTISTE-001"
        }
        
        response = requests.post(f"{BASE_URL}/api/frek/certify", json=payload)
        assert response.status_code == 400
        print(f"✓ Invalid audio rejected correctly")


class TestFREKAdvancedReseau:
    """NODE 06 - RÉSEAU API tests"""
    
    def test_reseau_info(self):
        """Test GET /api/frek/advanced/reseau - Graph info"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/reseau")
        assert response.status_code == 200
        
        data = response.json()
        assert data["node"] == "06"
        assert data["name"] == "RÉSEAU"
        assert "stats" in data
        assert "total_nodes" in data["stats"]
        assert "total_edges" in data["stats"]
        print(f"✓ Réseau: {data['stats']['total_nodes']} nodes, {data['stats']['total_edges']} edges")
    
    def test_reseau_stats(self):
        """Test GET /api/frek/advanced/reseau/stats - Detailed stats"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/reseau/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "nodes_by_type" in data
        assert "edges_by_type" in data
        print(f"✓ Réseau stats: nodes by type {data['nodes_by_type']}")


class TestFREKAdvancedTransmission:
    """NODE 07 - TRANSMISSION API tests"""
    
    def test_transmission_info(self):
        """Test GET /api/frek/advanced/transmission - Transmission info"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/transmission")
        assert response.status_code == 200
        
        data = response.json()
        assert data["node"] == "07"
        assert data["name"] == "TRANSMISSION"
        print(f"✓ Transmission: {data['description']}")
    
    def test_transmission_protocols(self):
        """Test GET /api/frek/advanced/transmission/protocols - 5 protocols"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/transmission/protocols")
        assert response.status_code == 200
        
        data = response.json()
        assert "protocols" in data
        assert len(data["protocols"]) == 5
        
        # Verify all 5 protocols
        protocol_names = [p["protocol"] for p in data["protocols"]]
        expected = ["bluetooth_ble", "nfc", "wifi_local", "ultrasonic", "cellular"]
        for proto in expected:
            assert proto in protocol_names, f"Missing protocol: {proto}"
        
        print(f"✓ Transmission: {len(data['protocols'])} protocols available")


class TestFREKAdvancedSysteme:
    """NODE 08 - SYSTÈME API tests"""
    
    def test_systeme_info(self):
        """Test GET /api/frek/advanced/systeme - System info"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/systeme")
        assert response.status_code == 200
        
        data = response.json()
        assert data["node"] == "08"
        assert data["name"] == "COUCHE SYSTÈME"
        print(f"✓ Système: {data['description']}")
    
    def test_systeme_position(self):
        """Test GET /api/frek/advanced/systeme/position"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/systeme/position")
        assert response.status_code == 200
        print(f"✓ System position endpoint working")


class TestFREKAdvancedJuridique:
    """NODE 09 - JURIDIQUE API tests"""
    
    def test_juridique_info(self):
        """Test GET /api/frek/advanced/juridique - Legal info"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/juridique")
        assert response.status_code == 200
        
        data = response.json()
        assert data["node"] == "09"
        assert data["name"] == "JURIDIQUE"
        print(f"✓ Juridique: {data['description']}")
    
    def test_juridique_principle(self):
        """Test GET /api/frek/advanced/juridique/principle - Notaire de fait"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/juridique/principle")
        assert response.status_code == 200
        
        data = response.json()
        assert data["principle"] == "notaire_de_fait"
        assert data["not"] == "juge_de_droit"
        assert "core_statements" in data
        assert "never" in data["core_statements"]
        assert "always" in data["core_statements"]
        
        # Verify 5 "never" statements and 5 "always" statements
        assert len(data["core_statements"]["never"]) == 5
        assert len(data["core_statements"]["always"]) == 5
        
        print(f"✓ Juridique principle: {data['principle']}, not {data['not']}")


class TestFREKAdvancedInstitutionnel:
    """NODE 10 - INSTITUTIONNEL API tests"""
    
    def test_institutionnel_info(self):
        """Test GET /api/frek/advanced/institutionnel - Institutional info"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/institutionnel")
        assert response.status_code == 200
        
        data = response.json()
        assert data["node"] == "10"
        assert data["name"] == "INSTITUTIONNEL"
        print(f"✓ Institutionnel: {data['description']}")
    
    def test_institutionnel_oapi(self):
        """Test GET /api/frek/advanced/institutionnel/oapi - 17 OAPI countries"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/institutionnel/oapi")
        assert response.status_code == 200
        
        data = response.json()
        assert "countries" in data
        assert data["total_countries"] == 17
        assert len(data["countries"]) == 17
        
        # Verify some known OAPI countries
        country_names = [c["name"] for c in data["countries"]]
        assert "Sénégal" in country_names
        assert "Cameroun" in country_names
        assert "Côte d'Ivoire" in country_names
        
        print(f"✓ OAPI: {data['total_countries']} countries")
    
    def test_institutionnel_offers(self):
        """Test GET /api/frek/advanced/institutionnel/offers"""
        response = requests.get(f"{BASE_URL}/api/frek/advanced/institutionnel/offers")
        assert response.status_code == 200
        
        data = response.json()
        assert "offers" in data
        assert len(data["offers"]) >= 6
        print(f"✓ Institutional offers: {len(data['offers'])} available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
