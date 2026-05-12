"""FREK Core — Modeles pydantic + constantes."""
from typing import Optional
from pydantic import BaseModel, Field

# Sources autorisees a ingerer des evenements
AUTHORIZED_SOURCES = ["kiltikonet", "fms", "kora"]

# Mapping source -> nom de variable d'env contenant le secret
SOURCE_SECRET_ENV = {
    "kiltikonet": "FREKCORE_SECRET_KILTIKONET",
    "fms": "FREKCORE_SECRET_FMS",
    "kora": "FREKCORE_SECRET_KORA",
}


class IngestEvent(BaseModel):
    frek_id: str = Field(..., min_length=1, max_length=128)
    event_id: str = Field(..., min_length=1, max_length=64)
    action: str = Field(..., min_length=1, max_length=64)
    badge_type: Optional[str] = Field(default=None, max_length=32)
    timestamp: str = Field(..., description="ISO 8601 horodatage cote source")
    source: str = Field(..., description="Identifiant logique de la source")


# Reglet de scoring par defaut — seed unique a l'initialisation si la collection
# frek_scoring_rules est vide. Modifiables ensuite a chaud via MongoDB sans deploiement.
DEFAULT_SCORING_RULES = [
    {"event_type": "ACTIVATION", "context": "CC2026", "base_score": 10},
    {"badge_type": "CC26-ART", "bonus_score": 20},
    {"badge_type": "CC26-INT", "bonus_score": 12},
    {"badge_type": "CC26-STF", "bonus_score": 10},
    {"badge_type": "CC26-BNV", "bonus_score": 10},
    {"badge_type": "CC26-PRS", "bonus_score": 10},
    {"badge_type": "CC26-VIP", "bonus_score": 15},
    {"badge_type": "CC26-OFF", "bonus_score": 12},
    {"badge_type": "CC26-SPO", "bonus_score": 8},
    {"badge_type": "CC26-EXP1", "bonus_score": 6},
    {"badge_type": "CC26-EXP2", "bonus_score": 6},
    {"badge_type": "CC26-EXP3", "bonus_score": 7},
    {"badge_type": "CC26-EXP4", "bonus_score": 7},
    {"badge_type": "CC26-EXP5", "bonus_score": 8},
    {"badge_type": "CC26-EXP6", "bonus_score": 8},
    {"badge_type": "CC26-EXP7", "bonus_score": 9},
]

# Squelette enrichment — tous les champs futurs poses en null des la naissance
# du frek_subject pour ne jamais avoir a faire de migration.
INITIAL_ENRICHMENT = {
    "frek_subject_did": None,    # Phase 5 — did:frek:{frek_id}
    "nominatif": None,            # Phase 2 — prenom/email volontaire
    "jeton_cc_linked": None,      # Phase 3 — Jeton CC associe
    "nfc_badge_written": None,    # Phase 2 — badge NFC physique
    "eudi_vc_issued": None,       # Phase 5 — VC EUDI emis
}
