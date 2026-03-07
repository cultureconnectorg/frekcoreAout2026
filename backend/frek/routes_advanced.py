"""
FREK v2 — Routes API Niveaux 6-10
==================================
Endpoints pour les nœuds avancés de FREK:
- NODE 06: Réseau (graphe vivant)
- NODE 07: Transmission (multi-protocole)
- NODE 08: Système (couche système)
- NODE 09: Juridique (neutralité totale)
- NODE 10: Institutionnel (observatoire)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

from .nodes.node06_reseau import node06, NodeType, RelationType
from .nodes.node07_transmission import node07, TransmissionProtocol
from .nodes.node08_systeme import node08, IntegrationTarget
from .nodes.node09_juridique import node09
from .nodes.node10_institutionnel import node10, InstitutionalClient


# Router pour les nœuds 6-10
advanced_router = APIRouter(prefix="/advanced", tags=["FREK v2 Advanced (NODE 06-10)"])


# ═══════════════════════════════════════════════════════════════════
# NODE 06 — RÉSEAU
# ═══════════════════════════════════════════════════════════════════

@advanced_router.get("/reseau")
async def reseau_info():
    """Information sur le NODE 06 — RÉSEAU"""
    stats = await node06.get_stats()
    return {
        "node": "06",
        "name": "RÉSEAU",
        "description": "Graphe vivant — 5 types de nœuds, 17 types de relations",
        "stats": stats.to_dict(),
    }


@advanced_router.get("/reseau/stats")
async def reseau_stats():
    """Statistiques du graphe"""
    stats = await node06.get_stats()
    return stats.to_dict()


@advanced_router.get("/reseau/node/{node_id}")
async def get_node(node_id: str):
    """Récupère un nœud du graphe"""
    node = await node06.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Nœud {node_id} introuvable")
    return node.to_dict()


@advanced_router.get("/reseau/neighbors/{node_id}")
async def get_neighbors(
    node_id: str,
    direction: str = Query("both", enum=["outgoing", "incoming", "both"]),
):
    """Récupère les voisins d'un nœud"""
    neighbors = await node06.get_neighbors(node_id, direction=direction)
    return {
        "node_id": node_id,
        "direction": direction,
        "neighbors_count": len(neighbors),
        "neighbors": neighbors,
    }


@advanced_router.get("/reseau/artiste/{artiste_id}")
async def get_artiste_graph(artiste_id: str):
    """Récupère le sous-graphe d'un artiste"""
    return await node06.get_artiste_graph(artiste_id)


@advanced_router.get("/reseau/lieu/{lieu_id}")
async def get_lieu_activity(lieu_id: str):
    """Récupère l'activité d'un lieu"""
    return await node06.get_lieu_activity(lieu_id)


@advanced_router.get("/reseau/path")
async def find_path(
    start_id: str = Query(..., description="ID du nœud de départ"),
    end_id: str = Query(..., description="ID du nœud d'arrivée"),
    max_depth: int = Query(6, ge=1, le=10),
):
    """Trouve le chemin le plus court entre deux nœuds"""
    path = await node06.find_path(start_id, end_id, max_depth)
    if path is None:
        return {
            "start_id": start_id,
            "end_id": end_id,
            "path_found": False,
            "message": "Aucun chemin trouvé",
        }
    return {
        "start_id": start_id,
        "end_id": end_id,
        "path_found": True,
        "path_length": len(path),
        "path": path,
    }


# ═══════════════════════════════════════════════════════════════════
# NODE 07 — TRANSMISSION
# ═══════════════════════════════════════════════════════════════════

@advanced_router.get("/transmission")
async def transmission_info():
    """Information sur le NODE 07 — TRANSMISSION"""
    stats = await node07.get_stats()
    return {
        "node": "07",
        "name": "TRANSMISSION",
        "description": "Multi-protocole — BLE, NFC, WiFi, Ultrasons, Cellular",
        "stats": stats,
    }


@advanced_router.get("/transmission/protocols")
async def get_protocols():
    """Liste tous les protocoles de transmission"""
    return {
        "protocols": node07.get_all_protocols(),
    }


@advanced_router.get("/transmission/protocol/{protocol}")
async def get_protocol_info(protocol: str):
    """Informations sur un protocole spécifique"""
    try:
        proto = TransmissionProtocol(protocol)
        return node07.get_protocol_info(proto)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Protocole inconnu: {protocol}. Valeurs: {[p.value for p in TransmissionProtocol]}"
        )


class CreatePacketRequest(BaseModel):
    frek_id: str
    artiste_id: str
    sha256_signal: str
    protocol: str
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None


@advanced_router.post("/transmission/packet")
async def create_transmission_packet(request: CreatePacketRequest):
    """Crée un paquet de transmission"""
    try:
        proto = TransmissionProtocol(request.protocol)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Protocole inconnu: {request.protocol}")
    
    packet = node07.create_packet(
        frek_id=request.frek_id,
        artiste_id=request.artiste_id,
        sha256_signal=request.sha256_signal,
        protocol=proto,
        gps_lat=request.gps_lat,
        gps_lon=request.gps_lon,
    )
    return packet.to_dict()


@advanced_router.post("/transmission/watermark")
async def create_watermark(frek_id: str):
    """Crée un filigrane ultrasonique pour un FREK-ID"""
    watermark = node07.create_ultrasonic_watermark(frek_id)
    return watermark.to_dict()


@advanced_router.post("/transmission/sync")
async def sync_pending():
    """Synchronise les certifications en attente"""
    return await node07.sync_pending()


# ═══════════════════════════════════════════════════════════════════
# NODE 08 — SYSTÈME
# ═══════════════════════════════════════════════════════════════════

@advanced_router.get("/systeme")
async def systeme_info():
    """Information sur le NODE 08 — SYSTÈME"""
    stats = await node08.get_stats()
    return {
        "node": "08",
        "name": "COUCHE SYSTÈME",
        "description": "FREK comme couche système — entre DSP et reconnaissance",
        "stats": stats,
    }


@advanced_router.get("/systeme/position")
async def get_system_position():
    """Position de FREK dans la stack système"""
    return node08.get_system_position()


@advanced_router.get("/systeme/references")
async def get_system_references():
    """Références système comparables (Dolby, Shazam, Siri)"""
    return {
        "references": node08.get_references(),
    }


@advanced_router.get("/systeme/roadmap")
async def get_system_roadmap():
    """Roadmap d'adoption système"""
    return {
        "roadmap": node08.get_roadmap(),
        "current": node08.get_current_milestone(),
    }


@advanced_router.get("/systeme/integrations")
async def get_integrations(status: Optional[str] = None):
    """Liste les intégrations disponibles"""
    return {
        "integrations": node08.get_integrations(status=status),
    }


# ═══════════════════════════════════════════════════════════════════
# NODE 09 — JURIDIQUE
# ═══════════════════════════════════════════════════════════════════

@advanced_router.get("/juridique")
async def juridique_info():
    """Information sur le NODE 09 — JURIDIQUE"""
    stats = await node09.get_stats()
    return {
        "node": "09",
        "name": "JURIDIQUE",
        "description": "Notaire de fait — jamais juge de droit",
        "stats": stats,
    }


@advanced_router.get("/juridique/principle")
async def get_legal_principle():
    """Principe juridique fondamental"""
    return node09.get_principle()


@advanced_router.get("/juridique/protection")
async def get_protection_layers():
    """Couches de protection juridique"""
    return {
        "layers": node09.get_protection_layers(),
    }


@advanced_router.get("/juridique/jurisdictions")
async def get_jurisdictions():
    """Juridictions supportées"""
    return node09.get_jurisdictions()


@advanced_router.get("/juridique/compliance")
async def check_compliance():
    """Vérifie la conformité juridique"""
    return node09.check_compliance()


class AttestationRequest(BaseModel):
    sha256_signal: str
    vector_dimensions: int = 528
    artiste_id: str
    timestamp_ms: int
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None


@advanced_router.post("/juridique/attestation")
async def create_attestation(request: AttestationRequest):
    """Crée une attestation technique légale"""
    attestation = node09.create_attestation(
        sha256_signal=request.sha256_signal,
        vector_dimensions=request.vector_dimensions,
        artiste_id=request.artiste_id,
        timestamp_ms=request.timestamp_ms,
        gps_lat=request.gps_lat,
        gps_lon=request.gps_lon,
    )
    return attestation.to_dict()


# ═══════════════════════════════════════════════════════════════════
# NODE 10 — INSTITUTIONNEL
# ═══════════════════════════════════════════════════════════════════

@advanced_router.get("/institutionnel")
async def institutionnel_info():
    """Information sur le NODE 10 — INSTITUTIONNEL"""
    stats = await node10.get_stats()
    return {
        "node": "10",
        "name": "INSTITUTIONNEL",
        "description": "Observatoire culturel — connaissance, pas contrôle",
        "stats": stats,
    }


@advanced_router.get("/institutionnel/offers")
async def get_institutional_offers(client_type: Optional[str] = None):
    """Liste les offres institutionnelles"""
    if client_type:
        try:
            ct = InstitutionalClient(client_type)
            return {"offers": [node10.get_offer_for_client(ct)]}
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Type client inconnu: {client_type}"
            )
    return {"offers": node10.get_offers()}


@advanced_router.get("/institutionnel/oapi")
async def get_oapi_info():
    """Informations sur l'OAPI (17 pays africains)"""
    return node10.get_oapi_info()


@advanced_router.get("/institutionnel/cvl-brain")
async def get_cvl_brain_info():
    """Informations sur l'intégration CVL BRAIN"""
    return node10.get_cvl_brain_info()


@advanced_router.get("/institutionnel/sovereignty")
async def get_sovereignty_benefits():
    """Bénéfices de souveraineté des données"""
    return node10.get_sovereignty_benefits()


@advanced_router.get("/institutionnel/observatory")
async def get_observatory_metrics(
    period_days: int = Query(30, ge=1, le=365),
):
    """Métriques de l'observatoire culturel"""
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    period_start_ms = now_ms - (period_days * 24 * 60 * 60 * 1000)
    
    metrics = await node10.generate_observatory_metrics(period_start_ms, now_ms)
    return metrics.to_dict()
