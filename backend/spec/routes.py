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
        "Sectoral-agnostic : la chaine ne distingue pas la nature de l'acte. Culture, sante, education, telecom, justice — meme garantie cryptographique.",
    ],
    "domains": {
        "_principle": "FREK est ne dans la culture mais le standard est sectoriellement neutre. Tout acte numerique ayant valeur de preuve peut etre ancre sans modification du protocole.",
        "supported": {
            "culture": "Acts artistiques, evenements culturels (genese de FREK, CC2026)",
            "education": "Diplomes, certifications, parcours universitaires",
            "health": "Acts medicaux, dossier patient, consentement eclaire",
            "justice": "Actes notariaux, contrats, pieces a conviction numeriques",
            "finance": "Preuves de detention, attestations, audit reglementaire",
            "telecom": "Identite numerique, eSIM, attestation de connexion",
            "media": "Provenance de contenu, integrite editoriale, anti-deepfake",
            "phygital": "Pont monde physique / numerique (NFC, biens d'art, certificats produit)",
            "tech": "Identite developpeur, signature de release, supply chain",
            "identity": "Identite nationale ou supra-nationale (CARICOM, etc.)",
        },
        "extension_model": (
            "Pour adopter FREK dans un nouveau secteur : utiliser le champ event_id pour scoper, "
            "metadata.domain pour categoriser, et eventuellement publier un payload_type custom (ex: 'medical_consent', 'diploma_issuance'). "
            "La spec v1.0.0 reste invariable ; les nouveaux types sont retrocompatibles tant qu'ils respectent la signature SHA-256."
        ),
        "sector_examples": {
            "hospital_caribbean": "Hopital ancre les consentements eclaires patient via payload_type='medical_consent' + event_id='HOSP-MQ-001'",
            "university_diploma": "Universite delivre diplome via payload_type='diploma_issuance' + event_id='UNI-XYZ-2026'",
            "telecom_esim": "Operateur certifie activation eSIM via payload_type='esim_activation' + event_id='OP-TLC-001'",
            "notary_act": "Notaire ancre acte authentique via payload_type='notarial_deed' + event_id='ETUDE-FR-097'",
            "media_provenance": "Redaction signe article via payload_type='editorial_act' + event_id='MEDIA-FR-001'",
        },
    },
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
    "passport": {
        "principle": "Souverainete du porteur. Le passeport est un fichier JSON signe Ed25519 que le porteur peut emporter, archiver et presenter sans dependance reseau a FREKCORE.",
        "signature_algorithm": "Ed25519 (RFC 8032)",
        "selective_disclosure": "Merkle tree binaire SHA-256 sur les claims. Le porteur revele un sous-ensemble en fournissant le merkle_path par claim. Les claims caches restent representes uniquement par leur empreinte.",
        "leaf_hash_input": "canonical_json({\"key\", \"nonce\", \"value\"}) hashe en SHA-256",
        "envelope_signed_fields": [
            "spec_version", "passport_version", "key_id", "frek_id",
            "issued_at", "claims_count", "merkle_root",
        ],
        "default_claim_keys": [
            "frek_id", "issued_at", "spec_version",
            "current_stage", "stages_completed", "event_id", "source",
            "expires_at", "revoked",
            "chain_height", "chain_block_hash", "btc_anchored",
        ],
        "endpoints": {
            "public_key": "GET /api/v1/passport/key",
            "export_full": "GET /api/v1/passport/{frek_id}",
            "selective_disclosure": "POST /api/v1/passport/disclose",
            "verify_utility": "POST /api/v1/passport/verify",
        },
        "offline_verification": (
            "Un verificateur tiers a besoin uniquement de la cle publique (PEM ou raw 32 bytes b64) "
            "et d'une lib Ed25519 standard. La verification se fait sans appel reseau a FREKCORE : "
            "(1) recompute SHA-256 des leaves a partir des claims reveles, (2) folding via merkle_path, "
            "(3) Ed25519 verify sur canonical_json(envelope)."
        ),
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
    "security_policies": {
        "rate_limiting": {
            "model": "Sliding window MongoDB par (scope, action). 429 silencieux, sans Retry-After, sans header explicatif.",
            "defaults": {
                "identity_emit": "100/heure/client_id",
                "stage_transition": "500/heure/client_id",
                "scan_access": "5000/heure/client_id",
                "staff_login_fail": "5/15min => lockout automatique",
            },
            "configurable_via_env": ["FREK_RATE_EMIT_PER_HOUR", "FREK_RATE_STAGE_PER_HOUR", "FREK_RATE_SCAN_PER_HOUR"],
        },
        "brute_force_lockout": {
            "trigger": "5 tentatives PIN echouees en 15 minutes",
            "duration_minutes": 15,
            "unlock": "Automatique apres expiration OU manuel via /admin/security/staff/{agent_id}/unlock",
        },
        "anomaly_trail": {
            "storage": "MongoDB collection security_events (admin-only)",
            "endpoints": [
                "/api/v1/admin/security/events (admin)",
                "/api/v1/admin/security/lockouts (admin)",
                "/api/v1/admin/security/staff/{agent_id}/unlock (admin)",
            ],
            "principle": "L'autorite ne se defend pas en public. Elle enregistre et agit en silence.",
            "optional_webhook": "FREK_SECURITY_WEBHOOK_URL — notifie warning/critical en POST JSON",
        },
        "secret_rotation": {
            "endpoint": "POST /api/v1/admin/clients/{client_id}/rotate",
            "guarantee": "Sans downtime. Tous les tokens en cours sont revoques via lookup token_hash. Le standard continue de tourner.",
        },
    },
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
    {
        "version": "1.0.0+passport",
        "date": "2026-05-07",
        "changes": [
            "Phase 3 — Souverainete porteur (additif, retrocompatible) :",
            "Passeport JSON signe Ed25519 (key_id 'frek-passport-v1', cle publique exposee)",
            "Disclosure selective via Merkle tree SHA-256 binaire (le porteur choisit les claims reveles)",
            "Verification 100% offline avec la cle publique (aucune dependance reseau a FREKCORE)",
            "12 claims par defaut : frek_id, issued_at, spec_version, current_stage, stages_completed, event_id, source, expires_at, revoked, chain_height, chain_block_hash, btc_anchored",
            "Aucun changement sur la FREK-Chain ni sur les blocks existants",
        ],
    },
    {
        "version": "1.0.0+did-vc",
        "date": "2026-05-07",
        "changes": [
            "Phase 4 — Interop W3C (additif, retrocompatible) :",
            "Methode DID 'did:frek:{frek_id}' deterministe, conforme W3C DID Core 1.0",
            "DID Document JSON-LD avec Multikey + 3 services (verify, passport, vc)",
            "Verifiable Credential W3C VC Data Model 2.0 + DataIntegrityProof / eddsa-jcs-2022",
            "Compatible eIDAS 2.0 et EUDI Wallet (importable comme issuer)",
            "Racine de confiance partagee : meme cle Ed25519 que les passeports souverains",
            "Endpoints : GET /api/v1/did/{frek_id}, GET /api/v1/vc/{frek_id}, POST /api/v1/vc/verify",
        ],
    },
    {
        "version": "1.0.0+eudi-standards",
        "date": "2026-05-07",
        "changes": [
            "Phase 4.5 — Plugin EUDI Wallet + Manifest universel (additif, retrocompatible) :",
            "Endpoints OID4VCI Draft 13 : /.well-known/openid-credential-issuer + /.well-known/oauth-authorization-server",
            "Pre-authorized code flow : POST /api/v1/eudi/credential-offer/{frek_id} -> /token -> /credential",
            "QR deep-link `openid-credential-offer://...` scannable par tout wallet EUDI compatible",
            "JWK Set RFC 7517 universel : /.well-known/jwks.json (kty=OKP, crv=Ed25519)",
            "DIF DID Configuration : /.well-known/did-configuration.json (preuve domaine -> did:frek:frekcore signee)",
            "Manifest universel : GET /api/v1/standards/manifest declare la compatibilite W3C / EUDI / ID4Africa / ITU / ISO mDL / CARICOM",
            "Roadmap geographique annoncee : CC2026 -> CARICOM -> ID4Africa -> EUDI -> USA mDL -> IPO 2028",
        ],
    },
    {
        "version": "1.0.0+core-events-sdjwt",
        "date": "2026-05-12",
        "changes": [
            "Phase d'amorcage CC2026 — Systeme nerveux souverain CVLN (additif, retrocompatible) :",
            "Module `core/` — couche evenementielle souveraine sur /api/core/* (separe de /api/v1/*)",
            "Collections nouvelles : frek_subjects (sujets vivants), frek_events (timeline horodatable), frek_scoring_rules (table de ponderation editable a chaud)",
            "POST /api/core/ingest — receveur souverain idempotent (sha256 frek_id|event_id|action|timestamp)",
            "Sources autorisees : kiltikonet, fms, kora — secrets bearers rotatifs par source (FREKCORE_SECRET_*)",
            "GET /api/core/frek/{frek_id}, /event/{event_id}/stats, /ecosystem/pulse, POST /admin/reload-rules",
            "Cultural Impact Score = base(action,context) + bonus(badge_type) — JAMAIS hardcode, toujours lu depuis Mongo",
            "Squelette enrichment pose des la naissance (frek_subject_did, nominatif, jeton_cc_linked, nfc_badge_written, eudi_vc_issued) — Phases 2/3/5 pretes sans migration",
            "Phase 4.6 — SD-JWT VC : format `vc+sd-jwt` ajoute en complement de ldp_vc (IETF draft-ietf-oauth-sd-jwt-vc), meme cle Ed25519",
            "POST /api/v1/eudi/credential/verify-sdjwt + issuer metadata declare les 2 formats",
            "Aucune cle Ed25519 regeneree. Aucun /.well-known/* modifie. Aucun flow OID4VCI casse.",
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
