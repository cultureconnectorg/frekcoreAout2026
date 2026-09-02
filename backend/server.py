from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone

# Import FREK v2 routes
from frek.routes import frek_router

# Import FREK v1 API (identity platform)
from frek_v1.router import v1_router, init_v1_db
from frek_v1.utils import hash_secret

# Import CC2026 modules
from badges.routes import badge_router, set_db as badges_set_db
from jetons.routes import jetons_router, set_db as jetons_set_db
from email_service.routes import email_router, set_db as email_set_db
from event.routes import event_router, set_db as event_set_db
from services.stripe_pay import stripe_router, set_db as stripe_set_db
from services.webhook import webhook_router, set_db as webhook_set_db

# Import FREK Notary (Bitcoin anchoring via OpenTimestamps)
from notary.routes import notary_router, set_db as notary_set_db, get_chain as notary_get_chain, get_anchor as notary_get_anchor
from notary.service import init_service as notary_init_service
from notary.chain_watchdog import watchdog_loop as notary_watchdog_loop

# Import FREK Staff PWA (Scanner terrain)
from staff.routes import staff_router, set_db as staff_set_db, seed_default_staff
from staff.scan_routes import scan_router, set_db as scan_set_db

# Import FREK Audit (timeline humaine consolidee)
from audit.routes import audit_router, set_db as audit_set_db

# Import FREK Spec (documentation standard publique)
from spec.routes import spec_router

# Import FREK Security (rate limiting silencieux + audit trail)
from security.policies import (
    set_db as security_set_db,
    ensure_indexes as security_ensure_indexes,
    record_anomaly as security_record_anomaly,
)
from security.routes import security_router, set_db as security_routes_set_db

# Import FREK Passport (Phase 3 — souverainete du porteur, Ed25519 + Merkle disclosure)
from passport.routes import passport_router, set_db as passport_set_db

# Import FREK DID + VC (Phase 4 — W3C DID Core 1.0 + VC Data Model 2.0, eIDAS 2.0 / EUDI Wallet)
from did.routes import did_router, vc_router, set_db as did_set_db

# Import FREK EUDI Wallet plugin (Phase 4.5 — OID4VCI manifest + flow)
from eudi.routes import eudi_router, wellknown_router as eudi_wellknown_router, set_db as eudi_set_db
from eudi.service import ensure_indexes as eudi_ensure_indexes

# Import FREK Standards (manifest universel + JWKS + DID Configuration)
from standards.routes import standards_router, standards_wellknown_router

# Import FREK Core — couche evenementielle souveraine CC2026 (greffe additive)
from core.routes import core_router, set_db as core_set_db
from core.service import ensure_indexes as core_ensure_indexes
from core.scoring import seed_default_rules_if_empty as core_seed_rules

# Import FREK Cultural Fingerprint Layer (Phase 5 — propriete CVLN)
from fingerprint.routes import fp_router, set_db as fp_set_db, ensure_indexes as fp_ensure_indexes

# D1 — Content Binding (founder decision D1, 2026-09-01): canonical,
# hardened successor concept to backend/frek/'s historical certify/verify
# routes (untouched, see content_binding/routes.py's own module docstring).
from content_binding.routes import (
    content_binding_router,
    set_db as content_binding_set_db,
    ensure_indexes as content_binding_ensure_indexes,
)

# Import FREK Certified Seal (script JS embeddable pour partenaires)
from seal import seal_router

# Import FREK Geo — Phase 6 Couche geolocalite souveraine (additif, namespace /api/geo/*)
from geo.routes import geo_router, set_db as geo_set_db
from geo.service import ensure_indexes as geo_ensure_indexes

# Import FREK PDF Batch — generation self-service de badges PDF (additif)
from pdf_batch.routes import pdf_batch_router, set_db as pdf_batch_set_db


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


def cors_origins_from_env() -> list[str]:
    """Return a credential-safe CORS allowlist.

    Wildcard origins cannot safely be combined with credentialed browser requests.
    Local origins are available by default for the supported development servers; a
    production deployment must set ``CORS_ORIGINS`` explicitly.
    """
    configured = os.environ.get("CORS_ORIGINS")
    if not configured:
        if os.environ.get("FREK_ENV", "development").lower() == "production":
            raise RuntimeError("CORS_ORIGINS must be configured in production")
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    if not origins or "*" in origins:
        raise RuntimeError("CORS_ORIGINS must be a non-empty explicit allowlist when credentials are enabled")
    return origins


def configured_client_secret(env_name: str) -> str | None:
    """Read a bootstrap secret without turning a missing value into credentials."""
    value = os.environ.get(env_name, "").strip()
    return value or None

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
# Sprint G P1 fix: fail-fast si Mongo indisponible (3s au lieu de 30s default)
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=3000,
    connectTimeoutMS=3000,
    socketTimeoutMS=10000,
)
db = client[os.environ['DB_NAME']]

# Initialize v1 API with database
init_v1_db(db)

# Initialize CC2026 modules
badges_set_db(db)
jetons_set_db(db)
email_set_db(db)
event_set_db(db)
stripe_set_db(db)
webhook_set_db(db)

# Initialize FREK Notary (Bitcoin anchoring)
notary_set_db(db)
notary_init_service(notary_get_chain(), notary_get_anchor())

# FREK-Chain integrity watchdog task handle (started in startup, cancelled
# in shutdown — see notary/chain_watchdog.py and memory/RESILIENCE_REPORT_
# v1.0.md Sprint G §7#4).
_chain_watchdog_task = None

# Initialize FREK Staff PWA
staff_set_db(db)
scan_set_db(db)

# Initialize FREK Audit
audit_set_db(db)

# Initialize FREK Security
security_set_db(db)
security_routes_set_db(db)

# Initialize FREK Passport
passport_set_db(db)

# Initialize FREK DID + VC
did_set_db(db)

# Initialize FREK EUDI plugin (OID4VCI)
eudi_set_db(db)

# Initialize FREK Core (couche evenementielle CC2026)
core_set_db(db)

# Initialize FREK Cultural Fingerprint Layer (Phase 5)
fp_set_db(db)

# Initialize D1 Content Binding (founder decision D1, 2026-09-01)
content_binding_set_db(db)

# Create the main app without a prefix
# Doctrine IP protection : surface d'attaque minimale en production.
# En dev, FREK_PUBLIC_DOCS=true pour reactiver Swagger si necessaire.
_PUBLIC_DOCS = os.environ.get("FREK_PUBLIC_DOCS", "false").lower() == "true"
app = FastAPI(
    title="FREK — Fichier de Referencement et d'Empreinte Kulturelle",
    version="2.0.0",
    docs_url="/docs" if _PUBLIC_DOCS else None,
    redoc_url="/redoc" if _PUBLIC_DOCS else None,
    openapi_url="/openapi.json" if _PUBLIC_DOCS else None,
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

# Include FREK v2 router (legacy)
app.include_router(frek_router, prefix="/api")

# Include FREK v1 API (identity platform)
app.include_router(v1_router, prefix="/api")

# Include CC2026 APIs
app.include_router(badge_router, prefix="/api")
app.include_router(jetons_router, prefix="/api")
app.include_router(email_router, prefix="/api")
app.include_router(event_router, prefix="/api")
app.include_router(stripe_router, prefix="/api")
app.include_router(webhook_router, prefix="/api")

# FREK Notary — Notaire Culturel Tech (Bitcoin)
app.include_router(notary_router, prefix="/api/v1")

# FREK Staff PWA (Scanner terrain : auth PIN + scan QR/NFC)
app.include_router(staff_router, prefix="/api/v1")
app.include_router(scan_router, prefix="/api/v1")

# FREK Audit (timeline humaine consolidee)
app.include_router(audit_router, prefix="/api/v1")

# FREK Spec (standard publique, sans auth)
app.include_router(spec_router, prefix="/api/v1")

# FREK Security audit (admin only)
app.include_router(security_router, prefix="/api/v1")

# FREK Passport (Phase 3 — souverainete porteur, public)
app.include_router(passport_router, prefix="/api/v1")

# FREK DID + VC (Phase 4 — W3C interop, eIDAS 2.0 / EUDI Wallet)
app.include_router(did_router, prefix="/api/v1")
app.include_router(vc_router, prefix="/api/v1")

# FREK EUDI plugin — OID4VCI flow (Phase 4.5)
app.include_router(eudi_router, prefix="/api/v1")
# Well-known endpoints accessibles via /api/.well-known/* (relais ingress documente)
# Note prod : configurer le CDN/edge pour proxifier `.well-known/*` -> `/api/.well-known/*`
app.include_router(eudi_wellknown_router, prefix="/api")

# --- Ecosystem awareness (registry + capabilities + integrations) ---
from ecosystem import ecosystem_router  # noqa: E402
app.include_router(ecosystem_router, prefix="/api/v1")

# FREK Standards — manifest universel + JWKS + DID Configuration (W3C / ID4Africa / ITU)
app.include_router(standards_router, prefix="/api/v1")
app.include_router(standards_wellknown_router, prefix="/api")

# FREK Core — couche evenementielle souveraine CC2026 (additif, namespace /api/core/*)
app.include_router(core_router, prefix="/api")

# FREK Cultural Fingerprint Layer — Phase 5 (additif, namespace /api/core/fingerprint/*)
app.include_router(fp_router, prefix="/api")

# FREK Certified Seal — sert /api/v1/seal.js et /api/v1/seal/demo
# (les partenaires embeddent <script src="https://frekcore.com/api/v1/seal.js">)
app.include_router(seal_router, prefix="/api/v1")

# FREK Geo — Phase 6 Couche geolocalite souveraine (additif, namespace /api/geo/*)
geo_set_db(db)
app.include_router(geo_router, prefix="/api")

# FREK PDF Batch — Batch B (additif, namespace /api/v1/pdf-batch/*)
pdf_batch_set_db(db)
app.include_router(pdf_batch_router, prefix="/api/v1")

# FREK Counter — Batch C (Compteur souverain universel CVLN, namespace /api/core/count*)
from counter.routes import counter_router, set_db as counter_set_db
from counter.service import ensure_indexes as counter_ensure_indexes, seed_rules_if_empty as counter_seed
counter_set_db(db)
app.include_router(counter_router, prefix="/api/core")

# FREK Investor — Pulse cryptographique due diligence (additif, namespace /api/v1/investor/*)
from investor.routes import investor_router, set_db as investor_set_db
investor_set_db(db)
app.include_router(investor_router, prefix="/api/v1")

# FREK Heritage / Transmission (additif, namespace /api/v1/heritage/*)
from heritage.routes import heritage_router, set_db as heritage_set_db
heritage_set_db(db)
app.include_router(heritage_router, prefix="/api/v1")

# FREK Sync — Baserow bi-directional (additif, namespace /api/v1/sync/*)
from sync.routes import sync_router, set_db as sync_set_db
sync_set_db(db)
app.include_router(sync_router, prefix="/api/v1")

# FREK Health & Admin Ops (additif, namespace /api/v1/health/* + /api/v1/admin/*)
from health.routes import health_router, admin_ops_router, set_db as health_set_db
health_set_db(db)
app.include_router(health_router, prefix="/api/v1")
app.include_router(admin_ops_router, prefix="/api/v1")

# FREK Moment — Fenetre d'acces publique #1 (anonyme, un tap)
from moment.routes import moment_router, set_db as moment_set_db
from moment import storage as moment_storage
moment_set_db(db)
app.include_router(moment_router, prefix="/api/v1")

# Init Object Storage pour les medias signes (optionnel, best-effort)
try:
    if moment_storage.init_storage():
        logging.getLogger(__name__).info("FREK Moment Object Storage initialise")
except Exception as _e:
    logging.getLogger(__name__).warning(f"Object Storage init skipped: {_e}")

# FK — Cultural Object Container (Specification v1.0)
from fk.routes import fk_router, set_db as fk_set_db
fk_set_db(db)
app.include_router(fk_router, prefix="/api/v1")

# D1 — Content Binding (founder decision D1, 2026-09-01): binds computed
# exact-hash + signal-fingerprint evidence to an existing .fk Cultural
# Object above — mounted alongside it under the same /api/v1 namespace.
app.include_router(content_binding_router, prefix="/api/v1")

# Identity Engine — Passkey/WebAuthn attache aux FREK-ID
from identity_engine.routes import identity_router, set_db as identity_set_db, ensure_indexes as identity_ensure_indexes
identity_set_db(db)
app.include_router(identity_router, prefix="/api/v1")

# FREK Registry — catalogue des namespaces culturels CVLN (Bloc 1). The
# schema-catalog endpoints stay stateless; /objects/{namespace} (P1, see
# registry/routes.py's module docstring) needs the shared db handle.
from registry.routes import registry_router, set_db as registry_set_db, ensure_indexes as registry_ensure_indexes
registry_set_db(db)
app.include_router(registry_router, prefix="/api/v1")


@app.on_event("startup")
async def _registry_startup():
    try:
        await registry_ensure_indexes()
    except Exception as _e:
        logging.getLogger(__name__).warning(f"Registry instance-store indexes skipped: {_e}")

# Audit Trail (Phase 3 Priority 5) — subscribes to the Event Bus (built
# Phase 2) so any already-published event becomes an append-only
# audit_trail_events record. No new route; no change to any existing
# route's code — event_envelope_to_audit_event() is a generic mapping
# (backend/audit_trail/subscribers.py), not hardcoded to any one event
# type, so extending this list is purely additive.
#
# P1/P2 (2026-08-31): identity.updated, identity.revoked, and
# object.created are all now real producers (reports/FREKCORE_COMPLETION_
# BACKLOG.md P1 #8) that were never subscribed here — closing that gap
# directly improves the freeze assessment's own "Audit trail active for
# sensitive mutations: PARTIAL (1 of 6 categories)" criterion
# (reports/21_FREEZE_ASSESSMENT.md). identity.recovered and
# identity.reconciled added with the MERGE/RENEW/RECOVERY implementation
# (docs/decisions/0003-identity-lifecycle-founder-decisions-implemented.md)
# — both are explicitly named "requires... complete auditability" by the
# founder decision, so both are wired in from the same commit that adds
# their producers, not left as a follow-up gap.
from audit_trail import MongoAuditRecorder, make_audit_trail_subscriber
from eventbus.bus import default_bus as _audit_event_bus

_audit_recorder = MongoAuditRecorder(db)

_AUDIT_TRAIL_EVENT_TYPES = (
    "identity.created",
    "identity.updated",
    "identity.revoked",
    "object.created",
    "identity.recovered",
    "identity.reconciled",
    "content_binding.created",
)


@app.on_event("startup")
async def _audit_trail_startup():
    try:
        await _audit_recorder.ensure_indexes()
        _subscriber = make_audit_trail_subscriber(_audit_recorder)
        for _event_type in _AUDIT_TRAIL_EVENT_TYPES:
            _audit_event_bus.subscribe(_event_type, _subscriber)
        logging.getLogger(__name__).info(
            "Audit Trail: subscribed to %s", ", ".join(_AUDIT_TRAIL_EVENT_TYPES)
        )
    except Exception as _e:
        logging.getLogger(__name__).warning(f"Audit Trail startup skipped: {_e}")


@app.on_event("startup")
async def _identity_engine_startup():
    try:
        await identity_ensure_indexes()
    except Exception as _e:
        logging.getLogger(__name__).warning(f"Identity Engine indexes skipped: {_e}")
    # Verifie explicitement que le RP WebAuthn est bien configure — sinon
    # les Passkeys seraient enregistrees contre un rpId inutilisable.
    try:
        from identity_engine.service import rp_config_status
        status = rp_config_status()
        _log = logging.getLogger(__name__)
        if status.get("configured"):
            _log.info(
                f"Identity Engine RP: rp_id={status['rp_id']} origin={status['origin']}"
            )
        else:
            _log.warning(
                "Identity Engine RP NON CONFIGURE (FREK_RP_ORIGIN manquant). "
                "Les Passkeys ne fonctionneront pas tant que le domaine public "
                "n'est pas defini. Detail: " + status.get("reason", "")
            )
    except Exception as _e:
        logging.getLogger(__name__).warning(f"Identity Engine RP check skipped: {_e}")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins_from_env(),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability (Phase 3 Priority 7, module built in Phase 2) — request/
# correlation ID middleware, added last so it is outermost (present even
# around CORS handling). Only reads/writes X-Request-ID and X-Correlation-ID
# — never Authorization, X-Admin-Key, X-FREK-Session, or any credential
# header (backend/observability/request_id.py has no code path that reads
# them). See reports/18_RUNTIME_VALIDATION.md for the wiring evidence.
from observability.request_id import RequestIdMiddleware
from observability import metrics as _obs_metrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response as _MetricsResponse

app.add_middleware(RequestIdMiddleware)


@app.get("/api/metrics")
async def metrics_endpoint():
    """Prometheus exposition format. No PII: only counters/histograms with
    method/path/status/operation labels — never a header value, a FREK-ID,
    an email, or any other user-identifying value. See
    reports/18_RUNTIME_VALIDATION.md for the label-content audit."""
    return _MetricsResponse(content=generate_latest(_obs_metrics.registry), media_type=CONTENT_TYPE_LATEST)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def _ensure_unique_sparse_index(collection, field: str):
    """Create a unique partial index without destructive startup repair.

    Existing production data is never changed here. A duplicate report or incompatible
    index is an explicit migration concern, not something startup may drop/recreate.
    """
    name = f"{field}_1"
    partial = {field: {"$type": "string"}}
    duplicates = await collection.aggregate([
        {"$match": partial},
        {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$limit": 20},
    ]).to_list(20)
    if duplicates:
        raise RuntimeError(
            f"Cannot create unique index {collection.name}.{name}: duplicate values detected. "
            "Run backend/migrations/20260824_unique_index_preflight.py and resolve them with a documented business migration."
        )

    indexes = await collection.index_information()
    existing = indexes.get(name)
    if existing:
        expected = [(field, 1)]
        is_expected = (
            existing.get("key") == expected
            and existing.get("unique") is True
            and existing.get("partialFilterExpression") == partial
        )
        if not is_expected:
            raise RuntimeError(
                f"Index {collection.name}.{name} has incompatible options; startup will not drop it. "
                "Run the documented preflight migration and apply a reviewed index change."
            )
        return

    await collection.create_index(
        field,
        unique=True,
        partialFilterExpression=partial,
        name=name,
    )

@app.on_event("startup")
async def warmup_infrastructure():
    """Pre-warm : indexes MongoDB + ping DB + charge passport keys AVANT premier request.
    Supprime le cold-start p99 observe sur la premiere requete apres deploy.
    """
    log = logging.getLogger("frek.warmup")
    try:
        # 1. Ping MongoDB pour ouvrir la connexion pool
        await db.command("ping")
        # 2. Force la creation des indexes identity_engine (avant que le premier
        #    /identity/init ne bloque 30s sur la creation du TTL index)
        try:
            from identity_engine.routes import ensure_indexes as _ii
            await _ii()
        except Exception as e:
            log.warning(f"identity_engine index warmup: {e}")
        # 3. Warm passport key (Ed25519 loaded from disk / seeded)
        try:
            from passport import keys as _pk
            _pk.public_key_pem()
        except Exception as e:
            log.warning(f"passport warmup: {e}")
        # 4. Warm notary chain — creation index cle
        try:
            await db.notary_blocks.create_index([("height", -1)])
        except Exception as exc:
            log.warning("notary block warmup index unavailable; continuing without warm index: %s", exc)
        log.info("FREK warmup complete — indexes, mongo pool, passport key preloaded")
    except Exception as e:
        log.warning(f"Warmup skipped: {e}")


@app.on_event("startup")
async def seed_clients():
    """Seed default API clients on startup"""
    clients_to_seed = [
        {
            "client_id": os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026"),
            "name": "Culture Connect 2026",
            "secret": configured_client_secret("FREK_CLIENT_KILTIKONET_SECRET"),
            "secret_env": "FREK_CLIENT_KILTIKONET_SECRET",
            # "registry:write" (P1, 2026-08-31): CC2026's own internal
            # integration client — the natural first ISSUER-authority actor
            # for backend/registry/routes.py's new /objects instance store.
            "permissions": ["emit", "stage", "stats", "registry:write"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "client_id": os.environ.get("FREK_CLIENT_CVLBRAIN_ID", "cvl-brain"),
            "name": "CVL Brain Analytics",
            "secret": configured_client_secret("FREK_CLIENT_CVLBRAIN_SECRET"),
            "secret_env": "FREK_CLIENT_CVLBRAIN_SECRET",
            "permissions": ["stats"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]
    for c in clients_to_seed:
        secret = c.pop("secret")
        secret_env = c.pop("secret_env")
        if not secret:
            logger.error(
                "Client API non initialise: %s requires non-empty %s",
                c["client_id"],
                secret_env,
            )
            continue
        c["secret_hash"] = hash_secret(secret)
        existing = await db.frek_clients.find_one({"client_id": c["client_id"]})
        if not existing:
            await db.frek_clients.insert_one(c)
            logger.info(f"Client API enregistre: {c['client_id']}")

    # Create indexes
    await db.frek_identities.create_index("frek_id", unique=True)
    await db.frek_identities.create_index("email_hash")
    await db.frek_identities.create_index("qr_token")
    await db.frek_identities.create_index("client_id")
    await db.frek_stages.create_index("frek_id")
    await db.frek_stages.create_index([("frek_id", 1), ("sequence", 1)])
    await db.frek_clients.create_index("client_id", unique=True)
    logger.info("FREK v1 indexes crees")

    # CC2026 indexes
    await db.badges.create_index("badge_id", unique=True)
    await db.badges.create_index("frek_id")
    await db.badges.create_index("email_hash")
    await db.badges.create_index("qr_token")
    await db.badges.create_index("event")
    await db.badges.create_index("type_badge")
    await db.transactions.create_index("tx_id")
    await db.transactions.create_index("badge_id")
    await db.transactions.create_index("marchand_id")
    await db.scans.create_index("badge_id")
    await db.scans.create_index("zone")
    await db.scans.create_index("timestamp")
    await db.marchands.create_index("marchand_id", unique=True)
    await db.payment_transactions.create_index("session_id", unique=True)
    await db.payment_transactions.create_index("badge_id")
    await db.email_logs.create_index("badge_id")
    await db.email_campaigns.create_index("timestamp")
    logger.info("CC2026 indexes crees")

    # FREK Notary indexes + start background anchor loop
    await notary_get_chain().ensure_indexes()
    notary_get_anchor().start()
    logger.info("FREK Notary (Bitcoin anchoring) demarre")

    # FREK-Chain integrity watchdog (P1, memory/RESILIENCE_REPORT_v1.0.md
    # Sprint G §5.2/§7#4): periodic verify_chain() pass, reports via
    # security_events (severity critical) on tamper detection — closes
    # the historical gap where corruption was only ever caught if someone
    # happened to call /notary/chain/verify. Opt out with
    # FREK_DISABLE_CHAIN_WATCHDOG=1 (e.g. a short-lived dev/mongomock run
    # where a long-lived background task isn't wanted).
    global _chain_watchdog_task
    if os.environ.get("FREK_DISABLE_CHAIN_WATCHDOG") != "1":
        _chain_watchdog_task = asyncio.create_task(
            notary_watchdog_loop(notary_get_chain(), security_record_anomaly)
        )
        logger.info("FREK-Chain watchdog demarre (verification toutes les 6h)")

    # FREK Staff PWA — seed comptes terrain + indexes
    await db.staff.create_index("agent_id", unique=True)
    # client_uuid idempotency indexes are preflighted and never replaced at startup.
    await _ensure_unique_sparse_index(db.scans, "client_uuid")
    await _ensure_unique_sparse_index(db.transactions, "client_uuid")
    await db.frek_identities.create_index("revoked", sparse=True)
    await db.frek_identities.create_index("expires_at", sparse=True)
    await db.scans.create_index("agent_id", sparse=True)
    await db.transactions.create_index("agent_id", sparse=True)
    await db.badges.create_index("agent_id", sparse=True)
    await db.frek_tokens.create_index("token_hash", sparse=True)
    await db.frek_clients.create_index("active", sparse=True)
    await db.frek_clients.create_index("event", sparse=True)

    # Security indexes (rate-limit + anomaly trail)
    await security_ensure_indexes()
    await eudi_ensure_indexes()
    # FREK Core — indexes + seed regles defaut (idempotent)
    await core_ensure_indexes()
    await core_seed_rules()
    # FREK Cultural Fingerprint Layer — indexes
    await fp_ensure_indexes()
    # D1 Content Binding — indexes (founder decision D1, 2026-09-01)
    await content_binding_ensure_indexes()
    # FREK Geo — indexes Phase 6
    await geo_ensure_indexes()
    # FREK Counter — indexes + seed regles
    await counter_ensure_indexes()
    seeded = await counter_seed()
    if seeded > 0:
        logger.info(f"FREK Counter: {seeded} regles de scoring seedees")
    # FREK Heritage — indexes (additif)
    await db.frek_heritage_declarations.create_index("declaration_id", unique=True)
    await db.frek_heritage_declarations.create_index("frek_id")
    await db.frek_heritage_declarations.create_index([("frek_id", 1), ("active", 1)])
    await db.frek_heritage_transfers.create_index("transfer_id", unique=True)
    await db.frek_heritage_transfers.create_index("frek_id")
    logger.info("FREK Heritage indexes crees")

    # FREK Sync (Baserow) — indexes (additif)
    await db.frek_sync_mapping.create_index([("service", 1), ("frek_id", 1)], unique=True)
    await db.frek_sync_mapping.create_index("baserow_row_id", sparse=True)
    await db.frek_sync_log.create_index([("service", 1), ("at", -1)])
    await db.frek_sync_cursor.create_index("service", unique=True)
    logger.info("FREK Sync (Baserow) indexes crees")
    await db.staff.create_index("locked_until", sparse=True)
    await db.staff.create_index("failed_attempts", sparse=True)
    # Compound index event+timestamp pour requetes audit/event scopees
    await db.scans.create_index([("event", 1), ("timestamp", -1)])
    await db.transactions.create_index([("event", 1), ("timestamp", -1)])
    await db.frek_stages.create_index([("event", 1), ("timestamp", -1)], sparse=True)
    await seed_default_staff()
    logger.info("FREK Staff PWA — comptes seedes")


@app.on_event("shutdown")
async def shutdown_db_client():
    notary_get_anchor().stop()
    if _chain_watchdog_task is not None:
        _chain_watchdog_task.cancel()
    client.close()
