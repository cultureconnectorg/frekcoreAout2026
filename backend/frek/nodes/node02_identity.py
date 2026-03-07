"""
FREK v2 — NODE 02 · IDENTITÉ
=============================
Le vecteur reçu du NODE 01 est transformé en identité permanente.
Trois couches de signature simultanées rendent le FREK-ID 
mathématiquement irréfutable et juridiquement neutre.

Trois couches:
1. SHA-256 Signal (32 bytes) — Empreinte du fichier audio
2. SHA-256 Metadata (32 bytes) — Empreinte du contexte
3. Hash Chaîne (32 bytes) — Lien avec FREK-ID précédent

Output: FREK-ID complet (~2.5 KB)
"""
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
import numpy as np


@dataclass
class FrekMetadata:
    """Métadonnées contextuelles pour le FREK-ID"""
    artiste_id: str
    timestamp_ms: int
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    device_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "artiste_id": self.artiste_id,
            "timestamp_ms": self.timestamp_ms,
            "gps": f"{self.gps_lat},{self.gps_lon}" if self.gps_lat else None,
            "device_id": self.device_id,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass 
class IdentityResult:
    """Résultat de l'identification NODE 02"""
    frek_id: str
    sha256_signal: str
    sha256_metadata: str
    hash_chaine: str
    prev_frek_id: Optional[str]
    timestamp_ms: int
    timestamp_iso: str
    vector_528d: np.ndarray
    stade: int = 4  # Par défaut: EMISSION
    
    @property
    def size_bytes(self) -> int:
        return (
            len(self.frek_id) +
            32 + 32 + 32 +  # SHA-256 hashes
            len(self.vector_528d) * 4 +
            8  # timestamp
        )
    
    def to_dict(self) -> dict:
        return {
            "frek_id": self.frek_id,
            "sha256_signal": self.sha256_signal,
            "sha256_metadata": self.sha256_metadata,
            "hash_chaine": self.hash_chaine,
            "prev_frek_id": self.prev_frek_id,
            "timestamp_ms": self.timestamp_ms,
            "timestamp_iso": self.timestamp_iso,
            "stade": self.stade,
            "vector_dimensions": len(self.vector_528d),
            "size_kb": round(self.size_bytes / 1024, 2),
        }


class Node02Identity:
    """
    Génération d'identité FREK — Triple signature SHA-256
    
    INPUT: Vecteur 528D + Audio bytes + Metadata
    OUTPUT: FREK-ID unique, immuable, irréfutable
    """
    
    # Cache du dernier FREK-ID pour le chaînage
    _last_frek_id: Optional[str] = None
    _last_hash: Optional[str] = None
    
    def __init__(self):
        pass
    
    def _sha256(self, data: bytes) -> str:
        """Calcul SHA-256"""
        return hashlib.sha256(data).hexdigest()
    
    def _generate_frek_id(
        self,
        year: int,
        sequence: int,
        signal_hash_short: str,
        metadata_hash_short: str
    ) -> str:
        """
        Format FREK-ID: FREK-YYYY-NNNN-aaaaaaaa-bbbbbbbb
        - YYYY: Année
        - NNNN: Numéro de séquence (0001-9999)
        - aaaaaaaa: 8 premiers chars du hash signal
        - bbbbbbbb: 8 premiers chars du hash metadata
        """
        return f"FREK-{year}-{sequence:04d}-{signal_hash_short[:8]}-{metadata_hash_short[:8]}"
    
    async def generate_identity(
        self,
        audio_bytes: bytes,
        vector_528d: np.ndarray,
        metadata: FrekMetadata,
        sequence: int,
        prev_frek_id: Optional[str] = None,
        prev_hash: Optional[str] = None,
    ) -> IdentityResult:
        """
        Génère l'identité FREK complète
        
        3 couches de signature:
        1. SHA-256 du signal audio brut
        2. SHA-256 des métadonnées JSON
        3. Hash chaîné avec le FREK-ID précédent
        """
        
        # COUCHE 1: SHA-256 Signal
        sha256_signal = self._sha256(audio_bytes)
        
        # COUCHE 2: SHA-256 Metadata
        metadata_json = metadata.to_json().encode('utf-8')
        sha256_metadata = self._sha256(metadata_json)
        
        # COUCHE 3: Hash Chaîne (blockchain légère)
        if prev_hash:
            chain_input = f"{prev_hash}:{sha256_signal}:{sha256_metadata}"
        else:
            # Genesis — premier de la chaîne
            chain_input = f"GENESIS:{sha256_signal}:{sha256_metadata}"
        
        hash_chaine = self._sha256(chain_input.encode('utf-8'))
        
        # Générer le FREK-ID
        year = datetime.fromtimestamp(metadata.timestamp_ms / 1000, tz=timezone.utc).year
        frek_id = self._generate_frek_id(year, sequence, sha256_signal, sha256_metadata)
        
        # Timestamp ISO
        timestamp_iso = datetime.fromtimestamp(
            metadata.timestamp_ms / 1000, 
            tz=timezone.utc
        ).isoformat()
        
        # Mettre à jour le cache pour le prochain chaînage
        self._last_frek_id = frek_id
        self._last_hash = hash_chaine
        
        return IdentityResult(
            frek_id=frek_id,
            sha256_signal=sha256_signal,
            sha256_metadata=sha256_metadata,
            hash_chaine=hash_chaine,
            prev_frek_id=prev_frek_id,
            timestamp_ms=metadata.timestamp_ms,
            timestamp_iso=timestamp_iso,
            vector_528d=vector_528d,
            stade=4,  # EMISSION par défaut
        )
    
    def get_last_chain_info(self) -> tuple[Optional[str], Optional[str]]:
        """Retourne (last_frek_id, last_hash) pour le chaînage"""
        return self._last_frek_id, self._last_hash


# Instance globale
node02 = Node02Identity()
