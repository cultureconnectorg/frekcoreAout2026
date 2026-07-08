"""FREKCORE FK — Cultural Object Container v0.1

Module qui cree, signe, valide et exporte des objets .fk conformes a la
FK Specification v1.0.

Doctrine :
- .fk = ZIP renomme, 7 couches, extension .fk, MIME application/vnd.frek.culture+zip
- Signature Ed25519 embarquee (verifiable OFFLINE, sans DB, sans reseau)
- Test de survie : ouvrir un .fk sur une machine vierge doit reveler l'identite intacte
"""
from .routes import fk_router, set_db

__all__ = ["fk_router", "set_db"]
