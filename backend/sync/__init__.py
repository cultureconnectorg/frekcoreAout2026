"""
FREK Sync — Baserow bi-directional bridge

- Push FREKCORE -> Baserow : pousse les identites recentes / une identite ciblee.
- Webhook Baserow -> FREKCORE : recoit les modifications operationnelles signees.
- Pull Baserow -> FREKCORE : reconciliation manuelle.

Module additif : aucun hook automatique dans les modules core, declenche
explicitement par l'admin ou par cron externe via X-Admin-Key.
"""
from .routes import sync_router, set_db

__all__ = ["sync_router", "set_db"]
