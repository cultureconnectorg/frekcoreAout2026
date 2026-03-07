"""
FREK v2 — NODE 03 · CYCLE DE VIE
=================================
FREK ne certifie pas un fichier à un instant T. 
Il certifie une vie créative complète.

5 STADES (comme la luciole):
1. GENESIS — L'œuf brille avant d'éclore
2. WORKSHOP — La larve se construit dans l'ombre
3. METAMORPHOSE — La nymphe se transforme
4. EMISSION — L'adulte s'allume une seule fois
5. LEGACY — Elle s'éteint. Ses œufs continuent.

Chaque stade a son propre FREK-ID (ou PRE-ID).
La chaîne prouve l'antériorité et le processus de création.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, timezone
from enum import IntEnum
import hashlib
import json


class Stade(IntEnum):
    """Les 5 stades du cycle de vie FREK"""
    GENESIS = 1       # Déclaration d'intention
    WORKSHOP = 2      # Versions intermédiaires
    METAMORPHOSE = 3  # Version finale, cohérence vérifiée
    EMISSION = 4      # Signal public, irréversible
    LEGACY = 5        # Dérivés, samples, remixes


@dataclass
class WorkshopVersion:
    """Version intermédiaire en stade WORKSHOP"""
    version_id: str
    created_at: int  # timestamp_ms
    partial_vector: List[float]  # Vecteur partiel
    sha256_version: str
    notes: Optional[str] = None


@dataclass
class CycleState:
    """État du cycle de vie d'une œuvre"""
    pre_id: str
    artiste_id: str
    stade_actif: Stade
    created_at: int
    
    # Données par stade
    genesis_data: Optional[dict] = None
    workshop_versions: List[WorkshopVersion] = field(default_factory=list)
    metamorphose_data: Optional[dict] = None
    emission_data: Optional[dict] = None
    
    # Score de cohérence (calculé à la métamorphose)
    coherence_score: Optional[float] = None
    
    # FREK-ID final (après émission)
    frek_id_final: Optional[str] = None
    
    # Enfants (stade LEGACY)
    children_frek_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "pre_id": self.pre_id,
            "artiste_id": self.artiste_id,
            "stade_actif": self.stade_actif.name,
            "stade_num": self.stade_actif.value,
            "created_at": self.created_at,
            "workshop_versions_count": len(self.workshop_versions),
            "coherence_score": self.coherence_score,
            "frek_id_final": self.frek_id_final,
            "children_count": len(self.children_frek_ids),
        }


class Node03Cycle:
    """
    Gestion du cycle de vie FREK — 5 stades
    
    Chaque œuvre traverse les stades séquentiellement.
    La chaîne prouve l'antériorité du processus créatif.
    """
    
    def __init__(self):
        # In-memory storage (sera remplacé par DB)
        self._cycles: dict[str, CycleState] = {}
        self._pre_id_counter = 0
    
    def _generate_pre_id(self, artiste_id: str, year: int) -> str:
        """Génère un PRE-ID embryonnaire"""
        self._pre_id_counter += 1
        return f"PRE-{year}-{artiste_id[:4]}-{self._pre_id_counter:04d}"
    
    async def start_genesis(
        self,
        artiste_id: str,
        intention: dict,  # { concept, lieu, description }
    ) -> CycleState:
        """
        STADE 1 — GENESIS
        L'artiste déclare son intention de créer.
        L'œuvre existe dans FREK avant d'exister dans le monde.
        """
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        year = datetime.now(timezone.utc).year
        
        pre_id = self._generate_pre_id(artiste_id, year)
        
        # Hash de l'intention
        intention_json = json.dumps(intention, sort_keys=True)
        sha256_intention = hashlib.sha256(intention_json.encode()).hexdigest()
        
        cycle = CycleState(
            pre_id=pre_id,
            artiste_id=artiste_id,
            stade_actif=Stade.GENESIS,
            created_at=now_ms,
            genesis_data={
                "intention": intention,
                "sha256_intention": sha256_intention,
                "declared_at": now_ms,
            }
        )
        
        self._cycles[pre_id] = cycle
        return cycle
    
    async def add_workshop_version(
        self,
        pre_id: str,
        partial_vector: List[float],
        audio_bytes: bytes,
        notes: Optional[str] = None,
    ) -> CycleState:
        """
        STADE 2 — WORKSHOP
        L'artiste dépose une version intermédiaire.
        Privée. Non publiée. Horodatée.
        """
        if pre_id not in self._cycles:
            raise ValueError(f"PRE-ID {pre_id} introuvable")
        
        cycle = self._cycles[pre_id]
        
        if cycle.stade_actif.value > Stade.WORKSHOP.value:
            raise ValueError("Cycle déjà au-delà du stade WORKSHOP")
        
        # Passer en WORKSHOP si encore en GENESIS
        if cycle.stade_actif == Stade.GENESIS:
            cycle.stade_actif = Stade.WORKSHOP
        
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        version_num = len(cycle.workshop_versions) + 1
        version_id = f"{pre_id}-V{version_num:02d}"
        
        sha256_version = hashlib.sha256(audio_bytes).hexdigest()
        
        version = WorkshopVersion(
            version_id=version_id,
            created_at=now_ms,
            partial_vector=partial_vector,
            sha256_version=sha256_version,
            notes=notes,
        )
        
        cycle.workshop_versions.append(version)
        return cycle
    
    async def submit_final(
        self,
        pre_id: str,
        final_vector: List[float],
        audio_bytes: bytes,
    ) -> tuple[CycleState, float]:
        """
        STADE 3 — METAMORPHOSE
        L'artiste soumet la version finale.
        FREK compare avec les versions larvaires.
        Retourne (cycle, score_coherence)
        """
        if pre_id not in self._cycles:
            raise ValueError(f"PRE-ID {pre_id} introuvable")
        
        cycle = self._cycles[pre_id]
        
        # Calculer le score de cohérence
        coherence_score = self._calculate_coherence(
            cycle.workshop_versions,
            final_vector
        )
        
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        sha256_final = hashlib.sha256(audio_bytes).hexdigest()
        
        cycle.stade_actif = Stade.METAMORPHOSE
        cycle.coherence_score = coherence_score
        cycle.metamorphose_data = {
            "submitted_at": now_ms,
            "sha256_final": sha256_final,
            "coherence_score": coherence_score,
            "workshop_versions_compared": len(cycle.workshop_versions),
        }
        
        return cycle, coherence_score
    
    def _calculate_coherence(
        self,
        workshop_versions: List[WorkshopVersion],
        final_vector: List[float]
    ) -> float:
        """
        Calcule le score de cohérence entre versions intermédiaires
        et version finale. Utilise la distance cosine.
        """
        if not workshop_versions:
            return 100.0  # Pas de versions intermédiaires = cohérence parfaite
        
        import numpy as np
        
        final = np.array(final_vector)
        
        # Calculer la similarité moyenne avec les versions
        similarities = []
        for version in workshop_versions:
            partial = np.array(version.partial_vector)
            # Ajuster la taille si nécessaire
            min_len = min(len(final), len(partial))
            final_cut = final[:min_len]
            partial_cut = partial[:min_len]
            
            # Distance cosine
            dot_product = np.dot(final_cut, partial_cut)
            norm_a = np.linalg.norm(final_cut)
            norm_b = np.linalg.norm(partial_cut)
            
            if norm_a > 0 and norm_b > 0:
                similarity = dot_product / (norm_a * norm_b)
                similarities.append(max(0, similarity))
        
        if not similarities:
            return 100.0
        
        # Score moyen en pourcentage
        return float(np.mean(similarities) * 100)
    
    async def emit(self, pre_id: str, frek_id: str) -> CycleState:
        """
        STADE 4 — EMISSION
        L'artiste active son FREK-ID.
        Signal public. Unique. Irréversible.
        """
        if pre_id not in self._cycles:
            raise ValueError(f"PRE-ID {pre_id} introuvable")
        
        cycle = self._cycles[pre_id]
        
        if cycle.stade_actif != Stade.METAMORPHOSE:
            raise ValueError("L'œuvre doit être en METAMORPHOSE avant EMISSION")
        
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        cycle.stade_actif = Stade.EMISSION
        cycle.frek_id_final = frek_id
        cycle.emission_data = {
            "emitted_at": now_ms,
            "frek_id": frek_id,
        }
        
        return cycle
    
    async def add_child(self, parent_frek_id: str, child_frek_id: str) -> Optional[CycleState]:
        """
        STADE 5 — LEGACY
        Une œuvre dérivée (sample, remix) est rattachée au parent.
        """
        # Trouver le cycle parent par frek_id_final
        for cycle in self._cycles.values():
            if cycle.frek_id_final == parent_frek_id:
                cycle.stade_actif = Stade.LEGACY
                cycle.children_frek_ids.append(child_frek_id)
                return cycle
        return None
    
    def get_cycle(self, pre_id: str) -> Optional[CycleState]:
        """Récupère un cycle par PRE-ID"""
        return self._cycles.get(pre_id)
    
    def get_cycle_by_frek_id(self, frek_id: str) -> Optional[CycleState]:
        """Récupère un cycle par FREK-ID final"""
        for cycle in self._cycles.values():
            if cycle.frek_id_final == frek_id:
                return cycle
        return None


# Instance globale
node03 = Node03Cycle()
