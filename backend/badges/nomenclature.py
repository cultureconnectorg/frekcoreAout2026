"""
Badge CC2026 — 14 types de badges avec nomenclature
"""

BADGE_TYPES = {
    "ART": {"name": "Artiste", "nfc": False, "color": "Or/Noir", "desc": "Performers et artistes invites"},
    "INT": {"name": "Intervenant", "nfc": False, "color": "Bleu/Or", "desc": "Conferenciers, tables rondes"},
    "STF": {"name": "Staff", "nfc": False, "color": "Gris/Or", "desc": "Equipe operationnelle"},
    "BNV": {"name": "Benevole", "nfc": False, "color": "Vert/Or", "desc": "Volontaires CC2026"},
    "PRS": {"name": "Presse", "nfc": False, "color": "Blanc/Noir", "desc": "Journalistes accredites"},
    "VIP": {"name": "VIP", "nfc": True, "color": "Violet/Or", "desc": "Partenaires strategiques"},
    "OFF": {"name": "Officiel", "nfc": True, "color": "Navy/Or", "desc": "Institutionnels, elus"},
    "SPO": {"name": "Sponsor", "nfc": True, "color": "Rouge/Or", "desc": "Partenaires commerciaux"},
    "EXP-B": {"name": "Exposant Bronze", "nfc": False, "color": "Bronze", "desc": "Stand 4m2"},
    "EXP-S": {"name": "Exposant Silver", "nfc": False, "color": "Argent", "desc": "Stand 9m2"},
    "EXP-G": {"name": "Exposant Gold", "nfc": True, "color": "Or", "desc": "Stand 16m2 + visibilite"},
    "EXP-P": {"name": "Exposant Platine", "nfc": True, "color": "Platine", "desc": "Stand premium + NFC"},
    "EXP-D": {"name": "Exposant Diaspora", "nfc": True, "color": "Violet", "desc": "Exposants diaspora"},
    "EXP-VIP": {"name": "Exposant VIP", "nfc": True, "color": "Or/Violet", "desc": "Top sponsors exposants"},
}

BADGE_STATUTS = ["INSCRIT", "CONFIRME", "BADGE_EMIS", "ACTIVE", "REVOQUE"]

# Zone access matrix
ZONE_ACCESS = {
    "ENTREE": ["ART", "INT", "STF", "BNV", "PRS", "VIP", "OFF", "SPO", "EXP-B", "EXP-S", "EXP-G", "EXP-P", "EXP-D", "EXP-VIP"],
    "SCENE": ["ART", "OFF", "VIP"],
    "VIP_LOUNGE": ["VIP", "OFF", "SPO"],
    "BACKSTAGE": ["ART", "STF"],
    "EXPOSANTS": ["EXP-B", "EXP-S", "EXP-G", "EXP-P", "EXP-D", "EXP-VIP", "STF"],
    "PRESSE": ["PRS", "OFF"],
    "ATELIERS": ["ART", "INT", "STF", "BNV", "PRS", "VIP", "OFF", "SPO", "EXP-B", "EXP-S", "EXP-G", "EXP-P", "EXP-D", "EXP-VIP"],
}


def generate_badge_id(badge_type: str, sequence: int) -> str:
    """CC26-VIP-K9244 format"""
    import random, string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"CC26-{badge_type}-{code}{sequence % 10}"


def is_nfc_enabled(badge_type: str) -> bool:
    return BADGE_TYPES.get(badge_type, {}).get("nfc", False)


def check_zone_access(badge_type: str, zone: str) -> bool:
    allowed = ZONE_ACCESS.get(zone, [])
    return badge_type in allowed
