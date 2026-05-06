"""
FREK Spec — Documentation publique du standard FREK v1.0.0.
Endpoint sans auth, immutable (versionnee), expose le contrat protocolaire
pour permettre l'implementation independante de verificateurs.
"""
from fastapi import APIRouter

spec_router = APIRouter(prefix="/spec", tags=["FREK Standard — Spec publique"])

FREK_SPEC = {
    "spec_version": "1.0.0",
    "name": "FREK — Standard d'identite culturelle souveraine",
    "publisher": "FREKCORE (Notaire Culturel Tech)",
    "license": "Open standard, libre d'implementation",
    "summary": (
        "FREK definit un standard d'identite culturelle compose de : "
        "1) un identifiant FREK-ID, 2) une chaine d'evenements ancree sur Bitcoin "
        "via OpenTimestamps, 3) un protocole de cycle de vie (revocation, expiration, transfert)."
    ),
    "principles": [
        "Souverainete : aucune dependance a un fournisseur de cloud privatif",
        "Immutabilite : chaque empreinte est ancree sur Bitcoin (preuve hors-ligne verifiable)",
        "Silence : FREKCORE est une autorite silencieuse, pas une marque grand public",
        "Portabilite : le porteur peut exporter et reimporter son passeport culturel",
        "Versioning explicite : chaque block contient spec_version pour evolution sans rupture",
    ],
    "frek_id": {
        "format": "UUID v4 (RFC 4122)",
        "size_bytes": 36,
        "uniqueness": "globale",
        "lifecycle_states": ["active", "revoked", "expired"],
    },
    "frek_chain": {
        "type": "Append-only hash chain",
        "block_hash_algorithm": "SHA-256",
        "block_hash_input": "height|prev_hash|payload_hash|payload_type|payload_id|timestamp|event_id|spec_version",
        "genesis_prev_hash": "0" * 64,
        "anchor_protocol": "OpenTimestamps (RFC OTS draft)",
        "anchor_blockchain": "Bitcoin (mainnet)",
        "calendars_default": [
            "https://a.pool.opentimestamps.org",
            "https://b.pool.opentimestamps.org",
            "https://alice.btc.calendar.opentimestamps.org",
            "https://bob.btc.calendar.opentimestamps.org",
            "https://finney.calendar.eternitywall.com",
        ],
    },
    "block_payload_types": {
        "identity_emit": "Emission d'un nouveau FREK-ID (GENESIS)",
        "stage_transition": "Transition stage Luciole (GENESIS->WORKSHOP->METAMORPHOSE->EMISSION->LEGACY)",
        "access_scan": "Scan de controle d'acces (terrain)",
        "jeton_tx": "Mouvement cashless (debit/credit jetons locaux)",
        "walkin_emit": "Emission terrain walk-in (PWA staff)",
        "revocation": "Revocation immutable d'un FREK-ID (CRL-like, jamais de delete)",
        "renewal": "Renouvellement / mise a jour expires_at",
        "transfer": "Transmission de FREK-ID (heritage / delegation, P2 backlog)",
    },
    "luciole_stages": [
        {"order": 1, "name": "GENESIS", "definition": "Premiere apparition culturelle"},
        {"order": 2, "name": "WORKSHOP", "definition": "Atelier / construction"},
        {"order": 3, "name": "METAMORPHOSE", "definition": "Mutation / transformation"},
        {"order": 4, "name": "EMISSION", "definition": "Diffusion publique"},
        {"order": 5, "name": "LEGACY", "definition": "Heritage / archivage perenne"},
    ],
    "verification_endpoints": {
        "public_verify": "GET /api/v1/notary/proof/{frek_id}",
        "public_audit_timeline": "GET /api/v1/audit/{frek_id}",
        "public_chain_status": "GET /api/v1/notary/chain/status",
        "public_chain_verify": "GET /api/v1/notary/chain/verify",
        "public_block": "GET /api/v1/notary/block/{height}",
        "public_blocks_by_event": "GET /api/v1/notary/blocks?event_id={event}",
        "ots_proof_download": "GET /api/v1/notary/proof/{frek_id}/ots",
    },
    "client_authentication": {
        "type": "OAuth2 client_credentials",
        "token_endpoint": "POST /api/v1/auth/token",
        "token_format": "JWT (HS256)",
        "token_lifetime_seconds": 86400,
        "permissions": ["emit", "stage", "stats"],
    },
    "data_integrity_guarantees": [
        "Tamper-evidence : modifier un block invalide tous les blocks suivants",
        "Append-only : aucune suppression de blocks (sauf RGPD droit a l'oubli sur frek_identities, jamais sur la chain)",
        "Idempotence : client_uuid garantit replay-safe pour scans + transactions",
        "Bitcoin proof : preuve hors-ligne verifiable via fichier .ots standard",
        "Backwards compat : verifier les blocs anciens via fallback hash sans event_id/spec_version",
    ],
    "governance": {
        "current_version": "1.0.0",
        "changelog_url": "/api/v1/spec/changelog",
        "contact": "frekcore@gmail.com",
        "ratification": "Multi-signature comite FREK Foundation (a venir P2)",
    },
}

CHANGELOG = [
    {
        "version": "1.0.0",
        "date": "2026-05-06",
        "changes": [
            "Genese du standard FREK",
            "FREK-Chain : append-only hash chain ancree Bitcoin (OpenTimestamps)",
            "FREK-ID : UUID v4 + cycle de vie (active/revoked/expired)",
            "Stages Luciole : GENESIS->WORKSHOP->METAMORPHOSE->EMISSION->LEGACY",
            "Block payload types : identity_emit, stage_transition, access_scan, jeton_tx, walkin_emit, revocation, renewal",
            "Multi-tenant : event_id sparse-indexed sur chaque block, queries scopees",
            "Idempotence : client_uuid sur scans + transactions",
            "Backwards-compat : verifier blocs legacy via fallback hash sans event_id",
        ],
    },
]


@spec_router.get("/")
async def spec_index():
    return {
        "current_version": FREK_SPEC["spec_version"],
        "versions_published": ["1.0.0"],
        "endpoints": {
            "current": "/api/v1/spec/v1.0.0",
            "changelog": "/api/v1/spec/changelog",
            "openapi": "/api/openapi.json",
            "swagger": "/docs",
        },
    }


@spec_router.get("/v1.0.0")
async def spec_v1_0_0():
    """Specification figee de FREK v1.0.0 — immutable, vouee a la perennite."""
    return FREK_SPEC


@spec_router.get("/changelog")
async def spec_changelog():
    return {"versions": CHANGELOG}
