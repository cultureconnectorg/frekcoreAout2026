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
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone

from .nodes.node06_reseau import node06, NodeType, RelationType
from .nodes.node07_transmission import node07, TransmissionProtocol
from .nodes.node08_systeme import node08, IntegrationTarget
from .nodes.node09_juridique import node09
from .nodes.node10_institutionnel import node10, InstitutionalClient
from .legacy_compat import legacy_rate_limit_ok, publish_legacy_invocation

logger = logging.getLogger("frek.routes_advanced")

# Router pour les nœuds 6-10
advanced_router = APIRouter(prefix="/advanced", tags=["FREK v2 Advanced (NODE 06-10)"])

# STATE_6 Historical Compatibility Reconciliation (2026-09-02): this
# module previously had no MongoDB access at all -- every NODE 06-10
# node is a pure in-process singleton. `db` is added here ONLY so the
# D3/D4 compatibility touches below (canonical relationship
# cross-reference on /reseau/node/{id}, canonical adapter_info merge on
# /transmission/protocols) can READ canonical, durable state. Nothing in
# this module writes to `db` -- canonical persistence stays exclusively
# owned by `relationship_graph`/`offline_transport`'s own routes
# (NO_PARALLEL_TRUTH_ENGINE_INTRODUCED=TRUE). See `docs/architecture/
# FREK_HISTORICAL_COMPATIBILITY_MATRIX.md`.
db = None


def set_db(database):
    global db
    db = database


# ═══════════════════════════════════════════════════════════════════
# NODE 06 — RÉSEAU
#
# STATE_6 hardening (2026-09-02): all 7 routes below now go through
# `legacy_rate_limit_ok`/`publish_legacy_invocation`
# (`frek/legacy_compat.py`) -- the historical réseau routes had zero
# rate limiting and zero audit visibility (confirmed by D3's own
# historical-route findings). `/reseau/node/{node_id}` additionally
# gains a genuine, additive canonical cross-reference: when `node_id`
# resolves to an OEUVRE (a real FREK-ID), it best-effort reads
# `db.relationships` (canonical `relationship_graph`, D3's own durable
# store) and reuses `relationship_graph.service.bounded_neighbors`/
# `can_read` directly -- never reimplemented -- to attach a
# `canonical_relationships` field. This is read-only, additive
# (existing keys unchanged), and never blocks the legacy response if it
# fails (`db` unset in a test app, or no canonical data exists yet).
# The other 6 routes keep their exact historical response shape and
# their in-memory node06 data source unchanged: node06's own graph
# (per-process, non-durable, including synthetic LIEU/EPOQUE/FREQUENCE
# nodes with no canonical equivalent -- see relationship_graph/models.py
# HISTORICAL_NODE_TYPE_TAXONOMY) is not a subset or superset of
# canonical `relationship_graph` data, so a full read-path replacement
# would silently drop or fabricate data -- NO_PARALLEL_TRUTH_ENGINE_
# INTRODUCED=TRUE is satisfied by keeping node06 as the sole source for
# these 6, not by pretending it doesn't exist.
# ═══════════════════════════════════════════════════════════════════


async def _canonical_relationships_for_oeuvre(node_id: str) -> Optional[Dict[str, Any]]:
    """Best-effort canonical cross-reference for an OEUVRE node
    (node_id == a real FREK-ID, per node06_reseau.py's own
    register_emission call site). Returns None on any failure or when
    `db` is unset -- never raises, never blocks the legacy route."""
    if db is None:
        return None
    try:
        from relationship_graph.service import bounded_neighbors, can_read
        from permissions.models import Scope

        cursor = db.relationships.find(
            {"$or": [{"subject_id": node_id}, {"object_id": node_id}]}, {"_id": 0}
        ).limit(400)
        edges = []
        async for doc in cursor:
            visibility = Scope.model_validate(
                doc.get("visibility") or {"type": "global"}
            )
            # Legacy route is unauthenticated -- only ever surface
            # publicly-visible canonical relationships here, matching
            # this route's own historical zero-auth PUBLIC READ status
            # (never a way to leak an OBJECT/ENTITY/ORGANIZATION-scoped
            # relationship through the legacy compatibility path).
            if can_read(
                visibility,
                actor_id=None,
                is_admin=False,
                parties=[doc.get("subject_id"), doc.get("object_id")],
            ):
                edges.append(doc)
        if not edges:
            return None
        neighbors = bounded_neighbors(edges, node_id, direction="both", limit=50)
        return {
            "source": "relationship_graph (canonical, D3)",
            "count": len(neighbors),
            "relationships": [
                {
                    "relationship_id": e.get("relationship_id"),
                    "predicate": e.get("predicate"),
                    "layer": e.get("layer"),
                    "status": e.get("status"),
                    "direction": e.get("direction"),
                }
                for e in neighbors
            ],
        }
    except Exception:
        logger.warning(
            "canonical relationship cross-reference failed (non-blocking)",
            exc_info=True,
        )
        return None


@advanced_router.get("/reseau")
async def reseau_info():
    """Information sur le NODE 06 — RÉSEAU"""
    if not await legacy_rate_limit_ok(scope="reseau_info", write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    stats = await node06.get_stats()
    await publish_legacy_invocation(
        legacy_route="GET /api/frek/advanced/reseau",
        canonical_target="relationship_graph",
        outcome="ok",
    )
    return {
        "node": "06",
        "name": "RÉSEAU",
        "description": "Graphe vivant — 5 types de nœuds, 17 types de relations",
        "stats": stats.to_dict(),
    }


@advanced_router.get("/reseau/stats")
async def reseau_stats():
    """Statistiques du graphe"""
    if not await legacy_rate_limit_ok(scope="reseau_stats", write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    stats = await node06.get_stats()
    await publish_legacy_invocation(
        legacy_route="GET /api/frek/advanced/reseau/stats",
        canonical_target="relationship_graph",
        outcome="ok",
    )
    return stats.to_dict()


@advanced_router.get("/reseau/node/{node_id}")
async def get_node(node_id: str):
    """Récupère un nœud du graphe. Enrichit additivement avec une
    référence croisée canonique (`canonical_relationships`) quand
    `node_id` est une OEUVRE résolvable dans le graphe canonique D3."""
    if not await legacy_rate_limit_ok(scope=node_id, write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    node = await node06.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Nœud {node_id} introuvable")
    out = node.to_dict()
    if out.get("node_type") == NodeType.OEUVRE.value:
        canonical = await _canonical_relationships_for_oeuvre(node_id)
        if canonical is not None:
            out["canonical_relationships"] = canonical
    await publish_legacy_invocation(
        legacy_route="GET /api/frek/advanced/reseau/node/{node_id}",
        canonical_target="relationship_graph",
        outcome="found",
    )
    return out


@advanced_router.get("/reseau/neighbors/{node_id}")
async def get_neighbors(
    node_id: str,
    direction: str = Query("both", enum=["outgoing", "incoming", "both"]),
):
    """Récupère les voisins d'un nœud"""
    if not await legacy_rate_limit_ok(scope=node_id, write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    neighbors = await node06.get_neighbors(node_id, direction=direction)
    await publish_legacy_invocation(
        legacy_route="GET /api/frek/advanced/reseau/neighbors/{node_id}",
        canonical_target="relationship_graph",
        outcome="ok",
    )
    return {
        "node_id": node_id,
        "direction": direction,
        "neighbors_count": len(neighbors),
        "neighbors": neighbors,
    }


@advanced_router.get("/reseau/artiste/{artiste_id}")
async def get_artiste_graph(artiste_id: str):
    """Récupère le sous-graphe d'un artiste"""
    if not await legacy_rate_limit_ok(scope=artiste_id, write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    result = await node06.get_artiste_graph(artiste_id)
    await publish_legacy_invocation(
        legacy_route="GET /api/frek/advanced/reseau/artiste/{artiste_id}",
        canonical_target="relationship_graph",
        outcome="ok",
    )
    return result


@advanced_router.get("/reseau/lieu/{lieu_id}")
async def get_lieu_activity(lieu_id: str):
    """Récupère l'activité d'un lieu"""
    if not await legacy_rate_limit_ok(scope=lieu_id, write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    result = await node06.get_lieu_activity(lieu_id)
    await publish_legacy_invocation(
        legacy_route="GET /api/frek/advanced/reseau/lieu/{lieu_id}",
        canonical_target="relationship_graph",
        outcome="ok",
    )
    return result


@advanced_router.get("/reseau/path")
async def find_path(
    start_id: str = Query(..., description="ID du nœud de départ"),
    end_id: str = Query(..., description="ID du nœud d'arrivée"),
    max_depth: int = Query(6, ge=1, le=10),
):
    """Trouve le chemin le plus court entre deux nœuds"""
    if not await legacy_rate_limit_ok(scope=start_id, write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    path = await node06.find_path(start_id, end_id, max_depth)
    await publish_legacy_invocation(
        legacy_route="GET /api/frek/advanced/reseau/path",
        canonical_target="relationship_graph",
        outcome="found" if path is not None else "not_found",
    )
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
#
# STATE_6 hardening (2026-09-02): all 6 routes below now go through
# `legacy_rate_limit_ok`/`publish_legacy_invocation`. Three genuine
# canonical touches, each additive/non-breaking:
#   - /transmission/protocols and /transmission/protocol/{protocol}
#     merge in `offline_transport.adapters.adapter_info()` (D4's own
#     canonical protocol metadata, which itself already reuses this
#     exact historical PROTOCOL_CONFIG directly -- REUSE_BEFORE_BUILD,
#     not two independent facts about the same protocol).
#   - /transmission/watermark now calls `offline_transport.watermark.
#     create_watermark_reference` directly instead of duplicating the
#     historical call -- its return value is a strict superset of the
#     historical dict (same keys plus `proof`/`validation_status`/
#     `decoder_exists`/`note`), so this is response-compatible.
#   - /transmission/packet's response gains an explicit, honest
#     `signature_short_is_not_cryptographic_signature: true` flag --
#     HISTORICAL_SIGNATURE_SHORT_WAS_NOT_REAL_SIGNATURE=TRUE, preserved
#     as compatibility metadata, never promoted as canonical proof.
#   - /transmission/sync's response gains a `note` clarifying it is a
#     legacy simulation, not canonical offline_transport reconciliation.
# ═══════════════════════════════════════════════════════════════════

@advanced_router.get("/transmission")
async def transmission_info():
    """Information sur le NODE 07 — TRANSMISSION"""
    if not await legacy_rate_limit_ok(scope="transmission_info", write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    stats = await node07.get_stats()
    await publish_legacy_invocation(
        legacy_route="GET /api/frek/advanced/transmission",
        canonical_target="offline_transport",
        outcome="ok",
    )
    return {
        "node": "07",
        "name": "TRANSMISSION",
        "description": "Multi-protocole — BLE, NFC, WiFi, Ultrasons, Cellular",
        "stats": stats,
    }


@advanced_router.get("/transmission/protocols")
async def get_protocols():
    """Liste tous les protocoles de transmission. Enrichit chaque
    protocole historique avec sa fiche canonique D4 (`software_status`,
    `hardware_verified` — jamais revendiqué `True`, aucun matériel réel
    disponible dans cet environnement)."""
    if not await legacy_rate_limit_ok(scope="transmission_protocols", write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    canonical_by_protocol: Dict[str, Any] = {}
    try:
        from offline_transport.adapters import adapter_info

        canonical_by_protocol = adapter_info()
    except Exception:
        logger.warning(
            "canonical adapter_info cross-reference failed (non-blocking)",
            exc_info=True,
        )
    protocols = []
    for p in node07.get_all_protocols():
        entry = dict(p)
        canonical = canonical_by_protocol.get(entry.get("protocol"))
        if canonical is not None:
            entry["canonical_adapter_info"] = canonical
        protocols.append(entry)
    await publish_legacy_invocation(
        legacy_route="GET /api/frek/advanced/transmission/protocols",
        canonical_target="offline_transport",
        outcome="ok",
    )
    return {"protocols": protocols}


@advanced_router.get("/transmission/protocol/{protocol}")
async def get_protocol_info(protocol: str):
    """Informations sur un protocole spécifique"""
    if not await legacy_rate_limit_ok(scope=protocol, write=False):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    try:
        proto = TransmissionProtocol(protocol)
        info = dict(node07.get_protocol_info(proto))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Protocole inconnu: {protocol}. Valeurs: {[p.value for p in TransmissionProtocol]}"
        )
    try:
        from offline_transport.adapters import adapter_info

        canonical = adapter_info().get(protocol)
        if canonical is not None:
            info["canonical_adapter_info"] = canonical
    except Exception:
        logger.warning(
            "canonical adapter_info cross-reference failed (non-blocking)",
            exc_info=True,
        )
    await publish_legacy_invocation(
        legacy_route="GET /api/frek/advanced/transmission/protocol/{protocol}",
        canonical_target="offline_transport",
        outcome="ok",
    )
    return info


class CreatePacketRequest(BaseModel):
    frek_id: str
    artiste_id: str
    sha256_signal: str
    protocol: str
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None


@advanced_router.post("/transmission/packet")
async def create_transmission_packet(request: CreatePacketRequest):
    """Crée un paquet de transmission.

    `signature_short` reste exactement ce qu'il a toujours été
    (un prefixe de hash non signé, jamais une signature cryptographique
    — confirmé par lecture du code, HISTORICAL_SIGNATURE_SHORT_WAS_NOT_
    REAL_SIGNATURE=TRUE) : le champ additionnel ci-dessous le documente
    explicitement plutôt que de le laisser ambigu. Pour une enveloppe
    réellement signée (Ed25519), voir POST /api/v1/offline/envelopes."""
    if not await legacy_rate_limit_ok(scope=request.frek_id, write=True):
        raise HTTPException(status_code=429, detail="Trop de requetes")
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
    out = packet.to_dict()
    out["signature_short_is_not_cryptographic_signature"] = True
    out["canonical_offline_transport_endpoint"] = "/api/v1/offline/envelopes"
    await publish_legacy_invocation(
        legacy_route="POST /api/frek/advanced/transmission/packet",
        canonical_target="offline_transport",
        outcome="created",
    )
    return out


@advanced_router.post("/transmission/watermark")
async def create_watermark(frek_id: str):
    """Crée un filigrane ultrasonique pour un FREK-ID.

    Délègue désormais directement à `offline_transport.watermark.
    create_watermark_reference` (D4's own canonical wrapper around this
    exact historical generator) plutôt que de dupliquer l'appel --
    réponse strictement compatible (sur-ensemble additif des mêmes
    clés historiques). WATERMARK_EQUALS_PROOF=FALSE."""
    if not await legacy_rate_limit_ok(scope=frek_id, write=True):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    from offline_transport.watermark import create_watermark_reference

    out = create_watermark_reference(frek_id)
    await publish_legacy_invocation(
        legacy_route="POST /api/frek/advanced/transmission/watermark",
        canonical_target="offline_transport",
        outcome="created",
    )
    return out


@advanced_router.post("/transmission/sync")
async def sync_pending():
    """Synchronise les certifications en attente.

    Simulation historique en mémoire de processus uniquement --
    n'affecte jamais et n'est jamais affectée par la réconciliation
    canonique D4 (POST /api/v1/offline/envelopes/{id}/sync). Le champ
    `note` ci-dessous le rend explicite plutôt que silencieusement
    ambigu."""
    if not await legacy_rate_limit_ok(scope="transmission_sync", write=True):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    result = await node07.sync_pending()
    if isinstance(result, dict):
        result = {
            **result,
            "note": (
                "Simulation de compatibilite historique uniquement -- non "
                "connectee a la reconciliation canonique offline_transport. "
                "Voir POST /api/v1/offline/envelopes/{envelope_id}/sync pour "
                "FINAL_RECONCILIATION canonique."
            ),
        }
    await publish_legacy_invocation(
        legacy_route="POST /api/frek/advanced/transmission/sync",
        canonical_target="offline_transport",
        outcome="ok",
    )
    return result


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
    """Crée une attestation technique descriptive à partir des valeurs
    fournies par l'appelant.

    STATE_6 hardening (2026-09-02): rate-limited (this route had none
    historically) and audit-visible. The overclaiming wording this
    route used to produce is fixed at the source
    (`node09_juridique.py:to_legal_text`, see that module's own
    docstring) -- this handler itself is otherwise unchanged: it still
    accepts exactly the same request shape and returns exactly the same
    dict keys plus one new, additive
    `canonical_technical_evidence_report_endpoint` field. It still does
    NOT verify anything against canonical FREKCORE state -- for a
    report that does, see `backend/technical_evidence_report/` (D5),
    which resolves ONLY from a resource ID reference, never from
    caller-supplied values like this route's request body."""
    if not await legacy_rate_limit_ok(scope=request.artiste_id, write=True):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    attestation = node09.create_attestation(
        sha256_signal=request.sha256_signal,
        vector_dimensions=request.vector_dimensions,
        artiste_id=request.artiste_id,
        timestamp_ms=request.timestamp_ms,
        gps_lat=request.gps_lat,
        gps_lon=request.gps_lon,
    )
    await publish_legacy_invocation(
        legacy_route="POST /api/frek/advanced/juridique/attestation",
        canonical_target="technical_evidence_report",
        outcome="created",
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
