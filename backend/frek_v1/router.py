"""
FREK v1 — Routeur principal
Assemble tous les sous-routeurs v1
"""
from fastapi import APIRouter

from .auth import auth_router, set_db as auth_set_db
from .identity import identity_router, set_db as identity_set_db
from .stages import stages_router, set_db as stages_set_db
from .stats import stats_router, set_db as stats_set_db
from .admin import admin_router, set_db as admin_set_db


v1_router = APIRouter(prefix="/v1", tags=["FREK v1"])


# Health endpoint
@v1_router.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


# Include sub-routers
v1_router.include_router(auth_router)
v1_router.include_router(identity_router)
v1_router.include_router(stages_router)
v1_router.include_router(stats_router)
v1_router.include_router(admin_router)


def init_v1_db(database):
    """Initialize all v1 modules with the database connection"""
    auth_set_db(database)
    identity_set_db(database)
    stages_set_db(database)
    stats_set_db(database)
    admin_set_db(database)
