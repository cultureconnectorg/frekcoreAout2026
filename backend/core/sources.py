"""FREK Core — Resolution des secrets sources (Bearer token -> source name).

Aucun secret n'est code en dur. Tous lus depuis l'environnement.
La rotation se fait par changement de variable d'env + restart — les evenements
historiques restent intacts.
"""
import hmac
import logging
import os
from typing import Optional

from .models import AUTHORIZED_SOURCES, SOURCE_SECRET_ENV

logger = logging.getLogger("frek.core.sources")


def resolve_source_from_bearer(bearer_token: str) -> Optional[str]:
    """Identifie la source en comparant le bearer aux secrets configures.

    Comparaison en temps constant (hmac.compare_digest) pour eviter les timing attacks.
    Retourne le nom de la source si match, sinon None.
    Une source dont le secret est vide/absent dans l'env est rejetee silencieusement.
    """
    if not bearer_token:
        return None
    for source in AUTHORIZED_SOURCES:
        env_name = SOURCE_SECRET_ENV.get(source)
        if not env_name:
            continue
        expected = os.environ.get(env_name)
        if not expected:
            continue
        if hmac.compare_digest(bearer_token, expected):
            return source
    return None
