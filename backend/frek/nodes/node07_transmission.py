"""
FREK v2 — NODE 07 · TRANSMISSION
=================================
FREK fonctionne sur tous les canaux. BLE, NFC, WiFi local, ultrasons, 4G/5G.
Le FREK-ID voyage avec le signal — comme un passeport fréquentiel.

5 PROTOCOLES DE TRANSMISSION:
1. BLUETOOTH BLE — Proximité, basse consommation (10m)
2. NFC — Contact, instantané (5cm)
3. WIFI LOCAL — Hors ligne, événements (100m)
4. ULTRASONS — Filigrane inaudible (dans l'audio)
5. CELLULAR — Global, temps réel (partout)

3 PHASES D'INTÉGRATION HARDWARE:
Phase 1 (2026): App + API pure software
Phase 2 (2027): SDK fabricants, premiers micros FREK
Phase 3 (2028+): Intégration OS native, puce FREK

Le FREK-ID peut être transmis hors ligne et synchronisé plus tard.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime, timezone
import hashlib
import struct
import base64


class TransmissionProtocol(Enum):
    """Protocoles de transmission FREK"""
    BLE = "bluetooth_ble"
    NFC = "nfc"
    WIFI_LOCAL = "wifi_local"
    ULTRASONIC = "ultrasonic"
    CELLULAR = "cellular"


class IntegrationPhase(Enum):
    """Phases d'intégration hardware"""
    PHASE_1_SOFTWARE = 1  # 2026: App + API
    PHASE_2_SDK = 2       # 2027: SDK fabricants
    PHASE_3_NATIVE = 3    # 2028+: OS natif + puce


@dataclass
class TransmissionPacket:
    """Paquet de transmission FREK"""
    frek_id: str
    artiste_id: str
    timestamp_ms: int
    protocol: TransmissionProtocol
    signature_short: str  # 8 premiers chars du hash
    gps_condensed: Optional[str] = None
    offline: bool = False
    sync_status: str = "pending"  # pending, synced, failed
    
    def to_bytes(self) -> bytes:
        """Sérialise le paquet pour transmission"""
        # Format compact: frek_id(64) + artiste_id(32) + timestamp(8) + protocol(1) + sig(8)
        data = (
            self.frek_id.encode('utf-8')[:64].ljust(64, b'\x00') +
            self.artiste_id.encode('utf-8')[:32].ljust(32, b'\x00') +
            struct.pack('>Q', self.timestamp_ms) +
            struct.pack('B', list(TransmissionProtocol).index(self.protocol)) +
            self.signature_short.encode('utf-8')[:8].ljust(8, b'\x00')
        )
        return data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'TransmissionPacket':
        """Désérialise un paquet"""
        frek_id = data[:64].rstrip(b'\x00').decode('utf-8')
        artiste_id = data[64:96].rstrip(b'\x00').decode('utf-8')
        timestamp_ms = struct.unpack('>Q', data[96:104])[0]
        protocol_idx = struct.unpack('B', data[104:105])[0]
        signature_short = data[105:113].rstrip(b'\x00').decode('utf-8')
        
        return cls(
            frek_id=frek_id,
            artiste_id=artiste_id,
            timestamp_ms=timestamp_ms,
            protocol=list(TransmissionProtocol)[protocol_idx],
            signature_short=signature_short,
        )
    
    def to_dict(self) -> dict:
        return {
            "frek_id": self.frek_id,
            "artiste_id": self.artiste_id,
            "timestamp_ms": self.timestamp_ms,
            "protocol": self.protocol.value,
            "signature_short": self.signature_short,
            "gps_condensed": self.gps_condensed,
            "offline": self.offline,
            "sync_status": self.sync_status,
            "packet_size_bytes": len(self.to_bytes()),
        }


@dataclass
class UltrasonicWatermark:
    """Filigrane ultrasonique pour embedding dans l'audio"""
    frek_id: str
    frequency_hz: int = 18000  # 18kHz - inaudible pour la plupart des adultes
    duration_ms: int = 500
    amplitude: float = 0.01  # Très faible pour ne pas affecter l'audio
    
    def generate_signal(self, sample_rate: int = 44100) -> List[float]:
        """Génère le signal ultrasonique à embedder"""
        import numpy as np
        
        # Encoder le FREK-ID en motif binaire
        frek_bytes = self.frek_id.encode('utf-8')
        frek_hash = hashlib.sha256(frek_bytes).digest()[:8]
        
        # Durée en samples
        num_samples = int(sample_rate * self.duration_ms / 1000)
        t = np.linspace(0, self.duration_ms / 1000, num_samples)
        
        # Signal porteur
        carrier = np.sin(2 * np.pi * self.frequency_hz * t)
        
        # Modulation FSK simple basée sur le hash
        modulated = np.zeros(num_samples)
        bits_per_byte = 8
        samples_per_bit = num_samples // (len(frek_hash) * bits_per_byte)
        
        for byte_idx, byte_val in enumerate(frek_hash):
            for bit_idx in range(bits_per_byte):
                bit = (byte_val >> (7 - bit_idx)) & 1
                start_sample = (byte_idx * bits_per_byte + bit_idx) * samples_per_bit
                end_sample = start_sample + samples_per_bit
                
                # FSK: 0 = freq_hz, 1 = freq_hz + 500
                freq = self.frequency_hz + (bit * 500)
                modulated[start_sample:end_sample] = np.sin(
                    2 * np.pi * freq * t[start_sample:end_sample]
                )
        
        return (modulated * self.amplitude).tolist()
    
    def to_dict(self) -> dict:
        return {
            "frek_id": self.frek_id,
            "frequency_hz": self.frequency_hz,
            "duration_ms": self.duration_ms,
            "amplitude": self.amplitude,
            "inaudible": self.frequency_hz >= 17000,
        }


@dataclass
class OfflineCertification:
    """Certification hors ligne pour synchronisation ultérieure"""
    packet: TransmissionPacket
    local_storage_path: Optional[str] = None
    sync_attempts: int = 0
    last_sync_attempt: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            "packet": self.packet.to_dict(),
            "local_storage_path": self.local_storage_path,
            "sync_attempts": self.sync_attempts,
            "last_sync_attempt": self.last_sync_attempt,
        }


class Node07Transmission:
    """
    Couche de transmission FREK — Multi-protocole
    
    Le FREK-ID voyage partout:
    - BLE: Badge, micro, wearable
    - NFC: Tap pour certifier
    - WiFi: Événements hors ligne
    - Ultrasons: Embedded dans l'audio
    - Cellular: Synchronisation globale
    """
    
    # Configurations par protocole
    PROTOCOL_CONFIG = {
        TransmissionProtocol.BLE: {
            "range_m": 10,
            "power_mw": 1,
            "latency_ms": 100,
            "offline_capable": True,
        },
        TransmissionProtocol.NFC: {
            "range_cm": 5,
            "power_mw": 0.1,
            "latency_ms": 50,
            "offline_capable": True,
        },
        TransmissionProtocol.WIFI_LOCAL: {
            "range_m": 100,
            "power_mw": 100,
            "latency_ms": 10,
            "offline_capable": True,
        },
        TransmissionProtocol.ULTRASONIC: {
            "range_m": 5,
            "power_mw": 0,
            "latency_ms": 500,
            "offline_capable": True,
            "embedded_in_audio": True,
        },
        TransmissionProtocol.CELLULAR: {
            "range_m": "global",
            "power_mw": 1000,
            "latency_ms": 200,
            "offline_capable": False,
        },
    }
    
    def __init__(self):
        self._pending_sync: List[OfflineCertification] = []
        self._synced_packets: List[TransmissionPacket] = []
        self._current_phase = IntegrationPhase.PHASE_1_SOFTWARE
    
    def create_packet(
        self,
        frek_id: str,
        artiste_id: str,
        sha256_signal: str,
        protocol: TransmissionProtocol,
        gps_lat: Optional[float] = None,
        gps_lon: Optional[float] = None,
    ) -> TransmissionPacket:
        """Crée un paquet de transmission"""
        timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        gps_condensed = None
        if gps_lat is not None and gps_lon is not None:
            gps_condensed = f"{gps_lat:.2f},{gps_lon:.2f}"
        
        config = self.PROTOCOL_CONFIG[protocol]
        offline = config.get("offline_capable", False)
        
        return TransmissionPacket(
            frek_id=frek_id,
            artiste_id=artiste_id,
            timestamp_ms=timestamp_ms,
            protocol=protocol,
            signature_short=sha256_signal[:8],
            gps_condensed=gps_condensed,
            offline=offline,
            sync_status="pending" if offline else "synced",
        )
    
    def create_ultrasonic_watermark(self, frek_id: str) -> UltrasonicWatermark:
        """Crée un filigrane ultrasonique pour embedding"""
        return UltrasonicWatermark(frek_id=frek_id)
    
    def embed_watermark_in_audio(
        self,
        audio_samples: List[float],
        watermark: UltrasonicWatermark,
        position_ms: int = 0,
        sample_rate: int = 44100,
    ) -> List[float]:
        """Embed le filigrane ultrasonique dans l'audio"""
        watermark_signal = watermark.generate_signal(sample_rate)
        
        # Position d'insertion
        start_sample = int(position_ms * sample_rate / 1000)
        
        # Copier l'audio original
        result = audio_samples.copy()
        
        # Ajouter le filigrane
        for i, sample in enumerate(watermark_signal):
            if start_sample + i < len(result):
                result[start_sample + i] += sample
        
        return result
    
    async def queue_for_sync(
        self,
        packet: TransmissionPacket,
        local_path: Optional[str] = None,
    ) -> OfflineCertification:
        """Met en file d'attente pour synchronisation"""
        offline_cert = OfflineCertification(
            packet=packet,
            local_storage_path=local_path,
        )
        self._pending_sync.append(offline_cert)
        return offline_cert
    
    async def sync_pending(self) -> Dict:
        """Synchronise les certifications en attente"""
        synced = []
        failed = []
        
        for cert in self._pending_sync[:]:
            try:
                # Simulation de sync (en prod: appel API)
                cert.packet.sync_status = "synced"
                cert.sync_attempts += 1
                cert.last_sync_attempt = int(datetime.now(timezone.utc).timestamp() * 1000)
                
                self._synced_packets.append(cert.packet)
                self._pending_sync.remove(cert)
                synced.append(cert.packet.frek_id)
            except Exception as e:
                cert.sync_attempts += 1
                cert.packet.sync_status = "failed"
                failed.append({"frek_id": cert.packet.frek_id, "error": str(e)})
        
        return {
            "synced_count": len(synced),
            "failed_count": len(failed),
            "pending_count": len(self._pending_sync),
            "synced": synced,
            "failed": failed,
        }
    
    def get_protocol_info(self, protocol: TransmissionProtocol) -> Dict:
        """Informations sur un protocole"""
        config = self.PROTOCOL_CONFIG[protocol]
        return {
            "protocol": protocol.value,
            **config,
        }
    
    def get_all_protocols(self) -> List[Dict]:
        """Liste tous les protocoles disponibles"""
        return [
            {
                "protocol": p.value,
                "name": p.name,
                **self.PROTOCOL_CONFIG[p],
            }
            for p in TransmissionProtocol
        ]
    
    async def get_stats(self) -> Dict:
        """Statistiques de transmission"""
        return {
            "current_phase": self._current_phase.name,
            "pending_sync": len(self._pending_sync),
            "total_synced": len(self._synced_packets),
            "protocols_available": len(TransmissionProtocol),
            "offline_protocols": sum(
                1 for p, c in self.PROTOCOL_CONFIG.items()
                if c.get("offline_capable", False)
            ),
        }


# Instance globale
node07 = Node07Transmission()
