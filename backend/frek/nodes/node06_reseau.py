"""
FREK v2 — NODE 06 · RÉSEAU
===========================
FREK ne vit pas seul. Chaque FREK-ID est un nœud dans un graphe vivant.
Le réseau grandit automatiquement avec chaque émission.

5 TYPES DE NŒUDS:
- OEUVRE: L'œuvre certifiée (FREK-ID)
- ARTISTE: Le créateur anonyme (artiste_id)
- LIEU: Coordonnées GPS condensées
- EPOQUE: Période temporelle (YYYY-QX)
- FREQUENCE: Signature fréquentielle dominante

17 TYPES DE RELATIONS (bidirectionnelles, pondérées):
OEUVRE: cree_par, similar_to, derive_de, emis_a
ARTISTE: cree, collabore_avec, influence, etudie_a
LIEU: accueille, resonance_avec, periode
EPOQUE: contient, tendance, cluster_frequentiel
FREQUENCE: presente_dans, dominante_de, cluster

Technologie: PostgreSQL + pgvector (fallback mémoire)
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set
from enum import Enum
from datetime import datetime, timezone
import numpy as np


class NodeType(Enum):
    """Types de nœuds dans le graphe FREK"""
    OEUVRE = "OEUVRE"
    ARTISTE = "ARTISTE"
    LIEU = "LIEU"
    EPOQUE = "EPOQUE"
    FREQUENCE = "FREQUENCE"


class RelationType(Enum):
    """Types de relations entre nœuds (17 types bidirectionnels)"""
    # Relations OEUVRE
    CREE_PAR = "cree_par"
    SIMILAR_TO = "similar_to"
    DERIVE_DE = "derive_de"
    EMIS_A = "emis_a"
    
    # Relations ARTISTE
    CREE = "cree"
    COLLABORE_AVEC = "collabore_avec"
    INFLUENCE = "influence"
    ETUDIE_A = "etudie_a"
    
    # Relations LIEU
    ACCUEILLE = "accueille"
    RESONANCE_AVEC = "resonance_avec"
    PERIODE = "periode"
    
    # Relations EPOQUE
    CONTIENT = "contient"
    TENDANCE = "tendance"
    CLUSTER_FREQUENTIEL = "cluster_frequentiel"
    
    # Relations FREQUENCE
    PRESENTE_DANS = "presente_dans"
    DOMINANTE_DE = "dominante_de"
    CLUSTER = "cluster"


@dataclass
class GraphNode:
    """Nœud dans le graphe FREK"""
    node_id: str
    node_type: NodeType
    created_at: int  # timestamp_ms
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class GraphEdge:
    """Arête (relation) dans le graphe FREK"""
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float  # 0.0 - 1.0
    created_at: int
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "weight": round(self.weight, 4),
            "created_at": self.created_at,
        }


@dataclass
class GraphStats:
    """Statistiques du graphe"""
    total_nodes: int
    total_edges: int
    nodes_by_type: Dict[str, int]
    edges_by_type: Dict[str, int]
    
    def to_dict(self) -> dict:
        return {
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "nodes_by_type": self.nodes_by_type,
            "edges_by_type": self.edges_by_type,
        }


class Node06Reseau:
    """
    Graphe vivant FREK — Réseau de nœuds interconnectés
    
    Propriétés:
    - ÉMERGENT: Le réseau se structure automatiquement
    - RÉSILIENT: Pas de point de défaillance unique
    - CUMULATIF: Plus il grandit, plus il a de valeur
    - LISIBLE: Répond aux questions complexes
    """
    
    def __init__(self):
        # Stockage mémoire (fallback si pas de PostgreSQL)
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        
        # Index pour recherche rapide
        self._nodes_by_type: Dict[NodeType, Set[str]] = {t: set() for t in NodeType}
        self._edges_by_source: Dict[str, List[GraphEdge]] = {}
        self._edges_by_target: Dict[str, List[GraphEdge]] = {}
    
    def _get_epoch_id(self, timestamp_ms: int) -> str:
        """Génère l'ID d'époque (YYYY-QX)"""
        dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        quarter = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{quarter}"
    
    def _get_lieu_id(self, gps_lat: Optional[float], gps_lon: Optional[float]) -> Optional[str]:
        """Génère l'ID de lieu condensé"""
        if gps_lat is None or gps_lon is None:
            return None
        # Condensé à 2 décimales pour regrouper par zone
        return f"GPS-{gps_lat:.2f},{gps_lon:.2f}"
    
    def _get_freq_id(self, vector: List[float]) -> str:
        """Génère l'ID de fréquence dominante"""
        if not vector:
            return "FREQ-UNKNOWN"
        
        # Trouver l'indice de la fréquence dominante (dans les 512 premières = FFT)
        fft_bands = vector[:512] if len(vector) >= 512 else vector
        dominant_idx = int(np.argmax(fft_bands))
        
        # Convertir en Hz approximatif (44100 Hz / 1024 * idx)
        freq_hz = int((44100 / 1024) * dominant_idx)
        
        # Regrouper par bandes de 100 Hz
        freq_band = (freq_hz // 100) * 100
        return f"FREQ-{freq_band}HZ"
    
    async def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        metadata: Optional[Dict] = None,
    ) -> GraphNode:
        """Ajoute un nœud au graphe"""
        if node_id in self._nodes:
            return self._nodes[node_id]
        
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        node = GraphNode(
            node_id=node_id,
            node_type=node_type,
            created_at=now_ms,
            metadata=metadata or {},
        )
        
        self._nodes[node_id] = node
        self._nodes_by_type[node_type].add(node_id)
        
        return node
    
    async def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        metadata: Optional[Dict] = None,
    ) -> GraphEdge:
        """Ajoute une arête (relation) au graphe"""
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        edge = GraphEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=min(1.0, max(0.0, weight)),
            created_at=now_ms,
            metadata=metadata or {},
        )
        
        self._edges.append(edge)
        
        # Index
        if source_id not in self._edges_by_source:
            self._edges_by_source[source_id] = []
        self._edges_by_source[source_id].append(edge)
        
        if target_id not in self._edges_by_target:
            self._edges_by_target[target_id] = []
        self._edges_by_target[target_id].append(edge)
        
        return edge
    
    async def register_emission(
        self,
        frek_id: str,
        artiste_id: str,
        timestamp_ms: int,
        vector: List[float],
        gps_lat: Optional[float] = None,
        gps_lon: Optional[float] = None,
        similar_frek_ids: Optional[List[tuple]] = None,  # [(frek_id, similarity)]
    ) -> Dict:
        """
        Enregistre une émission dans le graphe
        
        Crée automatiquement:
        - 1 nœud OEUVRE
        - 1 nœud ARTISTE (si nouveau)
        - 1 nœud LIEU (si GPS fourni)
        - 1 nœud EPOQUE
        - 1 nœud FREQUENCE (dominante)
        - Relations entre ces nœuds
        """
        nodes_created = []
        edges_created = []
        
        # 1. OEUVRE
        oeuvre = await self.add_node(frek_id, NodeType.OEUVRE, {"timestamp_ms": timestamp_ms})
        nodes_created.append(oeuvre.to_dict())
        
        # 2. ARTISTE
        artiste = await self.add_node(artiste_id, NodeType.ARTISTE)
        if artiste.created_at == oeuvre.created_at:  # Nouveau
            nodes_created.append(artiste.to_dict())
        
        # Relation CREE_PAR
        edge = await self.add_edge(frek_id, artiste_id, RelationType.CREE_PAR, 1.0)
        edges_created.append(edge.to_dict())
        
        # 3. LIEU (si GPS)
        lieu_id = self._get_lieu_id(gps_lat, gps_lon)
        if lieu_id:
            lieu = await self.add_node(lieu_id, NodeType.LIEU, {"lat": gps_lat, "lon": gps_lon})
            if lieu.created_at == oeuvre.created_at:
                nodes_created.append(lieu.to_dict())
            
            edge = await self.add_edge(frek_id, lieu_id, RelationType.EMIS_A, 1.0)
            edges_created.append(edge.to_dict())
        
        # 4. EPOQUE
        epoque_id = self._get_epoch_id(timestamp_ms)
        epoque = await self.add_node(epoque_id, NodeType.EPOQUE, {"year_quarter": epoque_id})
        if epoque.created_at == oeuvre.created_at:
            nodes_created.append(epoque.to_dict())
        
        edge = await self.add_edge(epoque_id, frek_id, RelationType.CONTIENT, 1.0)
        edges_created.append(edge.to_dict())
        
        # 5. FREQUENCE dominante
        freq_id = self._get_freq_id(vector)
        freq = await self.add_node(freq_id, NodeType.FREQUENCE, {"dominant": True})
        if freq.created_at == oeuvre.created_at:
            nodes_created.append(freq.to_dict())
        
        edge = await self.add_edge(freq_id, frek_id, RelationType.DOMINANTE_DE, 1.0)
        edges_created.append(edge.to_dict())
        
        # 6. Relations SIMILAR_TO (basées sur la résonance)
        if similar_frek_ids:
            for similar_id, similarity in similar_frek_ids[:5]:  # Max 5 similaires
                if similar_id != frek_id:
                    edge = await self.add_edge(
                        frek_id, similar_id, 
                        RelationType.SIMILAR_TO, 
                        similarity / 100.0  # Convertir % en poids
                    )
                    edges_created.append(edge.to_dict())
        
        return {
            "nodes_created": len(nodes_created),
            "edges_created": len(edges_created),
            "new_nodes": nodes_created,
            "new_edges": edges_created,
        }
    
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Récupère un nœud par ID"""
        return self._nodes.get(node_id)
    
    async def get_neighbors(
        self,
        node_id: str,
        relation_type: Optional[RelationType] = None,
        direction: str = "both",  # "outgoing", "incoming", "both"
    ) -> List[Dict]:
        """Récupère les voisins d'un nœud"""
        neighbors = []
        
        # Sortants
        if direction in ("outgoing", "both"):
            for edge in self._edges_by_source.get(node_id, []):
                if relation_type is None or edge.relation_type == relation_type:
                    target = self._nodes.get(edge.target_id)
                    if target:
                        neighbors.append({
                            "node": target.to_dict(),
                            "relation": edge.to_dict(),
                            "direction": "outgoing",
                        })
        
        # Entrants
        if direction in ("incoming", "both"):
            for edge in self._edges_by_target.get(node_id, []):
                if relation_type is None or edge.relation_type == relation_type:
                    source = self._nodes.get(edge.source_id)
                    if source:
                        neighbors.append({
                            "node": source.to_dict(),
                            "relation": edge.to_dict(),
                            "direction": "incoming",
                        })
        
        return neighbors
    
    async def get_artiste_graph(self, artiste_id: str) -> Dict:
        """Récupère le sous-graphe d'un artiste"""
        if artiste_id not in self._nodes:
            return {"error": "Artiste introuvable"}
        
        oeuvres = []
        lieux = set()
        epoques = set()
        frequences = set()
        collaborateurs = set()
        
        # Trouver toutes les œuvres de l'artiste
        for edge in self._edges_by_target.get(artiste_id, []):
            if edge.relation_type == RelationType.CREE_PAR:
                oeuvre_id = edge.source_id
                oeuvres.append(oeuvre_id)
                
                # Explorer les relations de chaque œuvre
                for oe_edge in self._edges_by_source.get(oeuvre_id, []):
                    target = self._nodes.get(oe_edge.target_id)
                    if target:
                        if target.node_type == NodeType.LIEU:
                            lieux.add(target.node_id)
                        elif target.node_type == NodeType.FREQUENCE:
                            frequences.add(target.node_id)
                
                for oe_edge in self._edges_by_target.get(oeuvre_id, []):
                    source = self._nodes.get(oe_edge.source_id)
                    if source:
                        if source.node_type == NodeType.EPOQUE:
                            epoques.add(source.node_id)
        
        return {
            "artiste_id": artiste_id,
            "oeuvres_count": len(oeuvres),
            "oeuvres": oeuvres,
            "lieux_uniques": list(lieux),
            "epoques": sorted(list(epoques)),
            "frequences_dominantes": list(frequences),
            "collaborateurs": list(collaborateurs),
        }
    
    async def get_lieu_activity(self, lieu_id: str) -> Dict:
        """Récupère l'activité d'un lieu"""
        if lieu_id not in self._nodes:
            return {"error": "Lieu introuvable"}
        
        oeuvres = []
        artistes = set()
        
        for edge in self._edges_by_target.get(lieu_id, []):
            if edge.relation_type == RelationType.EMIS_A:
                oeuvre_id = edge.source_id
                oeuvres.append(oeuvre_id)
                
                # Trouver l'artiste
                for oe_edge in self._edges_by_source.get(oeuvre_id, []):
                    if oe_edge.relation_type == RelationType.CREE_PAR:
                        artistes.add(oe_edge.target_id)
        
        return {
            "lieu_id": lieu_id,
            "emissions_count": len(oeuvres),
            "artistes_uniques": len(artistes),
            "artistes": list(artistes),
        }
    
    async def get_stats(self) -> GraphStats:
        """Statistiques du graphe"""
        nodes_by_type = {t.value: len(ids) for t, ids in self._nodes_by_type.items()}
        
        edges_by_type = {}
        for edge in self._edges:
            rt = edge.relation_type.value
            edges_by_type[rt] = edges_by_type.get(rt, 0) + 1
        
        return GraphStats(
            total_nodes=len(self._nodes),
            total_edges=len(self._edges),
            nodes_by_type=nodes_by_type,
            edges_by_type=edges_by_type,
        )
    
    async def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 6,
    ) -> Optional[List[Dict]]:
        """Trouve le chemin le plus court entre deux nœuds (BFS)"""
        if start_id not in self._nodes or end_id not in self._nodes:
            return None
        
        if start_id == end_id:
            return [{"node_id": start_id, "depth": 0}]
        
        visited = {start_id}
        queue = [(start_id, [{"node_id": start_id, "depth": 0}])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            # Explorer les voisins
            neighbors = await self.get_neighbors(current_id)
            
            for neighbor in neighbors:
                neighbor_id = neighbor["node"]["node_id"]
                
                if neighbor_id == end_id:
                    return path + [{
                        "node_id": neighbor_id,
                        "depth": len(path),
                        "via_relation": neighbor["relation"]["relation_type"],
                    }]
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [{
                        "node_id": neighbor_id,
                        "depth": len(path),
                        "via_relation": neighbor["relation"]["relation_type"],
                    }]))
        
        return None  # Pas de chemin trouvé


# Instance globale
node06 = Node06Reseau()
