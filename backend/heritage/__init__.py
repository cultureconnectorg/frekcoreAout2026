"""
FREK Heritage / Transmission Module

Permet a un porteur de declarer un beneficiaire pour son FREK-ID.
Lors du deces / revocation / transmission manuelle, le FREK-ID conserve
sa lignee cryptographique : nouveau detenteur, mais historique immuable
et chaine de custody ancree sur Bitcoin.

Invariants :
- Aucune PII en clair : seul un hash sha256(email_beneficiary) + claim_secret hash sont stockes.
- Chaque action est notarisee sur FREK-Chain (payload_type=heritage_*).
- L'historique des detenteurs est public et verifiable.
"""
from .routes import heritage_router, set_db

__all__ = ["heritage_router", "set_db"]
