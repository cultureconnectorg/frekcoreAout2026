"""FREKCORE Identity Engine — souverainete d'identite culturelle.

Doctrine :
- FREK-ID = identite culturelle (souveraine).
- Passkey (WebAuthn) = preuve de controle multi-appareils.
- FREKCORE ne cree pas des comptes. FREKCORE protege des identites culturelles.
"""
from .routes import identity_router, set_db

__all__ = ["identity_router", "set_db"]
