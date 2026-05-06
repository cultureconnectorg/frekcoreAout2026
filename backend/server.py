from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
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

# Import FREK Staff PWA (Scanner terrain)
from staff.routes import staff_router, set_db as staff_set_db, seed_default_staff
from staff.scan_routes import scan_router, set_db as scan_set_db

# Import FREK Audit (timeline humaine consolidee)
from audit.routes import audit_router, set_db as audit_set_db

# Import FREK Spec (documentation standard publique)
from spec.routes import spec_router

# Import FREK Security (rate limiting silencieux + audit trail)
from security.policies import set_db as security_set_db, ensure_indexes as security_ensure_indexes
from security.routes import security_router, set_db as security_routes_set_db


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
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

# Initialize FREK Staff PWA
staff_set_db(db)
scan_set_db(db)

# Initialize FREK Audit
audit_set_db(db)

# Initialize FREK Security
security_set_db(db)
security_routes_set_db(db)

# Create the main app without a prefix
app = FastAPI(title="FREK — Fichier de Referencement et d'Empreinte Kulturelle", version="2.0.0")

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

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def _ensure_unique_sparse_index(collection, field: str):
    """Cree un index unique partiel sur `field` (uniquement quand non-null/present).

    Utilise partialFilterExpression au lieu de sparse pour eviter les conflits sur null.
    Resout IndexKeySpecsConflict + DuplicateKeyError sur valeurs null pre-existantes.
    """
    name = f"{field}_1"
    partial = {field: {"$type": "string"}}
    try:
        await collection.create_index(
            field,
            unique=True,
            partialFilterExpression=partial,
            name=name,
        )
    except Exception as e:
        msg = str(e)
        if any(s in msg for s in ["IndexKeySpecsConflict", "already exists with different options", "'code': 86", "code\": 86"]):
            try:
                await collection.drop_index(name)
            except Exception:
                pass
            await collection.create_index(
                field,
                unique=True,
                partialFilterExpression=partial,
                name=name,
            )
        else:
            raise

@app.on_event("startup")
async def seed_clients():
    """Seed default API clients on startup"""
    clients_to_seed = [
        {
            "client_id": os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026"),
            "name": "Culture Connect 2026",
            "secret_hash": hash_secret(os.environ.get("FREK_CLIENT_KILTIKONET_SECRET", "")),
            "permissions": ["emit", "stage", "stats"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "client_id": os.environ.get("FREK_CLIENT_CVLBRAIN_ID", "cvl-brain"),
            "name": "CVL Brain Analytics",
            "secret_hash": hash_secret(os.environ.get("FREK_CLIENT_CVLBRAIN_SECRET", "")),
            "permissions": ["stats"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]
    for c in clients_to_seed:
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

    # FREK Staff PWA — seed comptes terrain + indexes
    await db.staff.create_index("agent_id", unique=True)
    # client_uuid: index pre-existant peut avoir ete cree sans unique=True ;
    # on le drop si les specs different pour eviter IndexKeySpecsConflict
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
    client.close()