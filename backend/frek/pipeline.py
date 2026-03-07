"""
FREK v2 — Pipeline Principal
==============================
Orchestration des 5 premiers nœuds:
NODE 01: Extraction (Audio → Vecteur 528D)
NODE 02: Identité (Vecteur → FREK-ID)
NODE 03: Cycle de vie (5 stades luciole)
NODE 04: Mémoire (pgvector storage)
NODE 05: Résonance (similarité, cohérence, tendances)

Ce module orchestre le flux complet de certification FREK.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timezone
import time

from .nodes.node01_extraction import node01, ExtractionResult
from .nodes.node02_identity import node02, FrekMetadata, IdentityResult
from .nodes.node03_cycle import node03, Stade, CycleState
from .nodes.node04_memory import node04, FrekAttestation
from .nodes.node05_resonance import init_node05, ResonanceResult


@dataclass
class CertificationResult:
    """Résultat complet d'une certification FREK"""
    frek_id: str
    extraction: dict
    identity: dict
    cycle: dict
    resonance: dict
    processing_time_ms: int
    
    def to_dict(self) -> dict:
        return {
            "frek_id": self.frek_id,
            "extraction": self.extraction,
            "identity": self.identity,
            "cycle": self.cycle,
            "resonance": self.resonance,
            "processing_time_ms": self.processing_time_ms,
            "status": "CERTIFIED",
        }


class FrekPipeline:
    """
    Pipeline de certification FREK v2
    
    Flux complet en < 3 secondes:
    1. Extraction des features audio (NODE 01)
    2. Génération de l'identité FREK-ID (NODE 02)
    3. Gestion du cycle de vie (NODE 03)
    4. Stockage minimal (NODE 04)
    5. Calcul des résonances (NODE 05)
    """
    
    def __init__(self):
        self.node01 = node01
        self.node02 = node02
        self.node03 = node03
        self.node04 = node04
        self.node05 = init_node05(node04)
    
    async def certify(
        self,
        audio_bytes: bytes,
        artiste_id: str,
        gps_lat: Optional[float] = None,
        gps_lon: Optional[float] = None,
        device_id: Optional[str] = None,
        pre_id: Optional[str] = None,  # Si déjà en cycle
    ) -> CertificationResult:
        """
        Certification complète d'une œuvre audio
        
        C'est LA fonction principale de FREK.
        Une action utilisateur → 17 opérations automatiques → FREK-ID
        """
        start_time = time.time()
        
        # ═══════════════════════════════════════════════════════
        # NODE 01 — EXTRACTION
        # ═══════════════════════════════════════════════════════
        extraction_result = await self.node01.extract_from_bytes(audio_bytes)
        vector_528d = extraction_result.vector_528d
        
        # ═══════════════════════════════════════════════════════
        # NODE 02 — IDENTITÉ
        # ═══════════════════════════════════════════════════════
        timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        metadata = FrekMetadata(
            artiste_id=artiste_id,
            timestamp_ms=timestamp_ms,
            gps_lat=gps_lat,
            gps_lon=gps_lon,
            device_id=device_id,
        )
        
        # Récupérer la chaîne pour le hash chaîné
        prev_frek_id, prev_hash = await self.node04.get_chain_info()
        sequence = await self.node04.get_next_sequence()
        
        identity_result = await self.node02.generate_identity(
            audio_bytes=audio_bytes,
            vector_528d=vector_528d,
            metadata=metadata,
            sequence=sequence,
            prev_frek_id=prev_frek_id,
            prev_hash=prev_hash,
        )
        
        # ═══════════════════════════════════════════════════════
        # NODE 03 — CYCLE DE VIE
        # ═══════════════════════════════════════════════════════
        if pre_id:
            # Continuer un cycle existant (METAMORPHOSE → EMISSION)
            cycle, coherence = await self.node03.submit_final(
                pre_id=pre_id,
                final_vector=vector_528d.tolist(),
                audio_bytes=audio_bytes,
            )
            cycle = await self.node03.emit(pre_id, identity_result.frek_id)
        else:
            # Emission directe (pas de cycle préalable)
            cycle = CycleState(
                pre_id=f"DIRECT-{identity_result.frek_id}",
                artiste_id=artiste_id,
                stade_actif=Stade.EMISSION,
                created_at=timestamp_ms,
                frek_id_final=identity_result.frek_id,
                coherence_score=100.0,
            )
        
        # ═══════════════════════════════════════════════════════
        # NODE 04 — STOCKAGE
        # ═══════════════════════════════════════════════════════
        attestation = FrekAttestation(
            frek_id=identity_result.frek_id,
            sha256_signal=identity_result.sha256_signal,
            sha256_metadata=identity_result.sha256_metadata,
            hash_chaine=identity_result.hash_chaine,
            vector_528d=vector_528d.tolist(),
            timestamp_ms=timestamp_ms,
            artiste_id=artiste_id,
            gps_lat=gps_lat,
            gps_lon=gps_lon,
            stade=cycle.stade_actif.value,
            prev_frek_id=prev_frek_id,
        )
        
        await self.node04.store(attestation)
        
        # ═══════════════════════════════════════════════════════
        # NODE 05 — RÉSONANCE
        # ═══════════════════════════════════════════════════════
        resonance_result = await self.node05.find_resonance(
            source_frek_id=identity_result.frek_id,
            limit=5
        )
        
        # Temps de traitement
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return CertificationResult(
            frek_id=identity_result.frek_id,
            extraction=extraction_result.to_dict(),
            identity=identity_result.to_dict(),
            cycle=cycle.to_dict(),
            resonance=resonance_result.to_dict(),
            processing_time_ms=processing_time_ms,
        )
    
    async def verify(self, frek_id: str) -> Optional[dict]:
        """
        Vérifie l'existence et récupère les détails d'un FREK-ID
        """
        attestation = await self.node04.get(frek_id)
        if not attestation:
            return None
        
        cycle = self.node03.get_cycle_by_frek_id(frek_id)
        resonance = await self.node05.find_resonance(frek_id, limit=5)
        
        return {
            "frek_id": frek_id,
            "verified": True,
            "timestamp_ms": attestation.timestamp_ms,
            "timestamp_iso": datetime.fromtimestamp(
                attestation.timestamp_ms / 1000, 
                tz=timezone.utc
            ).isoformat(),
            "artiste_id": attestation.artiste_id,
            "stade": attestation.stade,
            "sha256_signal": attestation.sha256_signal[:16] + "...",
            "cycle": cycle.to_dict() if cycle else None,
            "resonance": resonance.to_dict(),
        }
    
    async def start_genesis(
        self,
        artiste_id: str,
        intention: dict,
    ) -> dict:
        """
        Démarre un nouveau cycle de vie (GENESIS)
        L'artiste déclare son intention de créer.
        """
        cycle = await self.node03.start_genesis(artiste_id, intention)
        return {
            "pre_id": cycle.pre_id,
            "stade": cycle.stade_actif.name,
            "message": "Cycle GENESIS créé. L'œuvre existe dans FREK avant d'exister dans le monde.",
        }
    
    async def add_workshop(
        self,
        pre_id: str,
        audio_bytes: bytes,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Ajoute une version intermédiaire (WORKSHOP)
        """
        extraction = await self.node01.extract_from_bytes(audio_bytes)
        
        cycle = await self.node03.add_workshop_version(
            pre_id=pre_id,
            partial_vector=extraction.vector_528d.tolist(),
            audio_bytes=audio_bytes,
            notes=notes,
        )
        
        return {
            "pre_id": pre_id,
            "stade": cycle.stade_actif.name,
            "versions_count": len(cycle.workshop_versions),
            "message": f"Version {len(cycle.workshop_versions)} ajoutée au cycle.",
        }
    
    async def get_stats(self) -> dict:
        """
        Statistiques globales FREK
        """
        storage_stats = await self.node04.get_stats()
        return {
            "frek_version": "2.0",
            "nodes_active": ["01_extraction", "02_identity", "03_cycle", "04_memory", "05_resonance"],
            "storage": storage_stats,
        }


# Instance globale du pipeline
pipeline = FrekPipeline()
