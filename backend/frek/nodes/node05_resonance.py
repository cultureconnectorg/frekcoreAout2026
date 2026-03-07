"""
FREK v2 — NODE 05 · RESONANCE
==============================
Les FREK-ID ne vivent pas seuls. Chaque œuvre est un point 
dans un espace à 528 dimensions.

Le moteur de résonance calcule les distances entre points et 
répond à une question: quelles œuvres vibrent comme celle-ci?

TROIS MOTEURS:
1. SIMILARITÉ — Distance cosine entre vecteurs fréquentiels
2. COHÉRENCE ARTISTE — Empreinte globale d'un artiste
3. SYNCHRONISATION — Tendances fréquentielles d'une époque

SEUILS:
- > 95% : Alerte plagiat potentiel (silencieuse)
- 75-95% : Information influence / famille stylistique
- < 60% : Rupture de style détectée
"""
from dataclasses import dataclass
from typing import Optional, List
import numpy as np


@dataclass
class ResonanceMatch:
    """Un match de résonance"""
    frek_id: str
    similarity: float  # 0-100%
    artiste_id: str
    timestamp_ms: int
    reason: str  # "style", "artiste", "lieu", "frequence", "ancetre"


@dataclass
class ResonanceResult:
    """Résultat d'une requête de résonance"""
    source_frek_id: str
    matches: List[ResonanceMatch]
    alerts: List[dict]  # Alertes silencieuses
    artiste_coherence: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "source_frek_id": self.source_frek_id,
            "matches": [
                {
                    "frek_id": m.frek_id,
                    "similarity": round(m.similarity, 1),
                    "artiste_id": m.artiste_id,
                    "reason": m.reason,
                }
                for m in self.matches
            ],
            "alerts": self.alerts,
            "artiste_coherence": self.artiste_coherence,
            "match_count": len(self.matches),
        }


class Node05Resonance:
    """
    Moteur de résonance FREK — Recherche de similarité vectorielle
    
    Utilise pgvector pour recherche approximative en millisecondes
    sur des millions d'œuvres.
    """
    
    # Seuils de similarité
    THRESHOLD_PLAGIAT = 95.0
    THRESHOLD_INFLUENCE_HIGH = 75.0
    THRESHOLD_INFLUENCE_LOW = 60.0
    
    def __init__(self, memory_node):
        """Injecte le NODE 04 pour accès aux données"""
        self.memory = memory_node
    
    def _cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Calcule la similarité cosine entre deux vecteurs"""
        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = dot_product / (norm_a * norm_b)
        return max(0.0, min(1.0, similarity)) * 100  # En pourcentage
    
    async def find_resonance(
        self,
        source_frek_id: str,
        limit: int = 5,
    ) -> ResonanceResult:
        """
        MOTEUR 1 — Recherche les œuvres similaires à une source
        """
        source = await self.memory.get(source_frek_id)
        if not source:
            return ResonanceResult(
                source_frek_id=source_frek_id,
                matches=[],
                alerts=[{"type": "error", "message": "FREK-ID introuvable"}]
            )
        
        source_vector = np.array(source.vector_528d)
        
        # Recherche dans le stockage (mémoire ou pgvector)
        all_attestations = await self.memory.get_latest(1000)  # Limiter pour perf
        
        matches = []
        alerts = []
        
        for attestation in all_attestations:
            if attestation.frek_id == source_frek_id:
                continue
            
            target_vector = np.array(attestation.vector_528d)
            similarity = self._cosine_similarity(source_vector, target_vector)
            
            # Déterminer la raison du match
            if attestation.artiste_id == source.artiste_id:
                reason = "artiste"
            elif similarity > self.THRESHOLD_INFLUENCE_HIGH:
                reason = "style"
            else:
                reason = "frequence"
            
            match = ResonanceMatch(
                frek_id=attestation.frek_id,
                similarity=similarity,
                artiste_id=attestation.artiste_id,
                timestamp_ms=attestation.timestamp_ms,
                reason=reason,
            )
            matches.append(match)
            
            # Alerte silencieuse si plagiat potentiel
            if similarity > self.THRESHOLD_PLAGIAT and attestation.artiste_id != source.artiste_id:
                alerts.append({
                    "type": "plagiat_potential",
                    "severity": "warning",
                    "similarity": round(similarity, 1),
                    "target_frek_id": attestation.frek_id,
                    "message": f"Similarité > {self.THRESHOLD_PLAGIAT}% avec un autre artiste"
                })
        
        # Trier par similarité et limiter
        matches.sort(key=lambda x: x.similarity, reverse=True)
        matches = matches[:limit]
        
        # Calculer la cohérence artiste
        artiste_coherence = await self.calculate_artiste_coherence(source.artiste_id)
        
        return ResonanceResult(
            source_frek_id=source_frek_id,
            matches=matches,
            alerts=alerts,
            artiste_coherence=artiste_coherence,
        )
    
    async def find_similar_vector(
        self,
        vector: List[float],
        limit: int = 5,
        exclude_frek_id: Optional[str] = None,
    ) -> List[ResonanceMatch]:
        """
        Recherche les œuvres similaires à un vecteur donné
        (utile pour vérifier avant émission)
        """
        source_vector = np.array(vector)
        all_attestations = await self.memory.get_latest(1000)
        
        matches = []
        
        for attestation in all_attestations:
            if attestation.frek_id == exclude_frek_id:
                continue
            
            target_vector = np.array(attestation.vector_528d)
            similarity = self._cosine_similarity(source_vector, target_vector)
            
            match = ResonanceMatch(
                frek_id=attestation.frek_id,
                similarity=similarity,
                artiste_id=attestation.artiste_id,
                timestamp_ms=attestation.timestamp_ms,
                reason="style" if similarity > self.THRESHOLD_INFLUENCE_HIGH else "frequence",
            )
            matches.append(match)
        
        matches.sort(key=lambda x: x.similarity, reverse=True)
        return matches[:limit]
    
    async def calculate_artiste_coherence(self, artiste_id: str) -> Optional[float]:
        """
        MOTEUR 2 — Calcule la cohérence stylistique d'un artiste
        
        Moyenne de la similarité entre toutes ses œuvres.
        < 60% = rupture de style détectée
        """
        artiste_works = await self.memory.get_by_artiste(artiste_id)
        
        if len(artiste_works) < 2:
            return None  # Pas assez d'œuvres pour calculer
        
        vectors = [np.array(w.vector_528d) for w in artiste_works]
        
        # Calculer la similarité moyenne entre toutes les paires
        similarities = []
        for i, vec_a in enumerate(vectors):
            for j, vec_b in enumerate(vectors):
                if i < j:
                    similarity = self._cosine_similarity(vec_a, vec_b)
                    similarities.append(similarity)
        
        if not similarities:
            return 100.0
        
        return float(np.mean(similarities))
    
    async def detect_trends(
        self,
        period_start_ms: int,
        period_end_ms: int,
        min_cluster_size: int = 5,
    ) -> List[dict]:
        """
        MOTEUR 3 — Détecte les tendances fréquentielles d'une période
        
        Identifie les clusters de vecteurs similaires.
        """
        # Récupérer les œuvres de la période
        all_attestations = await self.memory.get_latest(10000)
        period_works = [
            a for a in all_attestations
            if period_start_ms <= a.timestamp_ms <= period_end_ms
        ]
        
        if len(period_works) < min_cluster_size:
            return []
        
        # Calculer le centroïde moyen de la période
        vectors = np.array([a.vector_528d for a in period_works])
        centroid = np.mean(vectors, axis=0)
        
        # Calculer la dispersion
        distances = [
            self._cosine_similarity(centroid, np.array(a.vector_528d))
            for a in period_works
        ]
        
        return [{
            "period_start": period_start_ms,
            "period_end": period_end_ms,
            "works_count": len(period_works),
            "mean_coherence": round(float(np.mean(distances)), 1),
            "std_coherence": round(float(np.std(distances)), 1),
            "dominant_artistes": self._get_top_artistes(period_works, 5),
        }]
    
    def _get_top_artistes(self, works, limit: int) -> List[dict]:
        """Identifie les artistes les plus actifs"""
        from collections import Counter
        artiste_counts = Counter(w.artiste_id for w in works)
        return [
            {"artiste_id": aid, "count": count}
            for aid, count in artiste_counts.most_common(limit)
        ]
    
    async def check_before_emission(
        self,
        vector: List[float],
        artiste_id: str,
    ) -> dict:
        """
        Vérifie avant émission s'il y a des conflits potentiels
        """
        matches = await self.find_similar_vector(vector, limit=10)
        
        # Filtrer les matches d'autres artistes avec haute similarité
        conflicts = [
            m for m in matches
            if m.artiste_id != artiste_id and m.similarity > self.THRESHOLD_PLAGIAT
        ]
        
        influences = [
            m for m in matches
            if m.similarity > self.THRESHOLD_INFLUENCE_HIGH and m.similarity <= self.THRESHOLD_PLAGIAT
        ]
        
        return {
            "can_emit": len(conflicts) == 0,
            "conflicts": [
                {"frek_id": c.frek_id, "similarity": round(c.similarity, 1)}
                for c in conflicts
            ],
            "influences_detected": [
                {"frek_id": i.frek_id, "similarity": round(i.similarity, 1)}
                for i in influences
            ],
            "warning": "Similarité > 95% avec une œuvre existante" if conflicts else None,
        }


# L'instance sera créée après import de node04
node05 = None

def init_node05(memory_node):
    """Initialise NODE 05 avec le NODE 04"""
    global node05
    node05 = Node05Resonance(memory_node)
    return node05
