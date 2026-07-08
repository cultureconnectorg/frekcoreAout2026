"""
FREK Health & Ops — endpoints de sante approfondie et gestion backups.

- /api/v1/health/deep     : sante complete (Mongo, Ed25519, OTS, disk, memory)
- /api/v1/health/live     : liveness (K8s probe)
- /api/v1/health/ready    : readiness (K8s probe, verifie Mongo)
- /api/v1/admin/backup/*  : status + trigger + list (X-Admin-Key)
"""
from .routes import health_router, admin_ops_router, set_db

__all__ = ["health_router", "admin_ops_router", "set_db"]
