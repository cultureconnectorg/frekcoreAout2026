"""
FREK v2 — NODE 09 · JURIDIQUE
==============================
FREK ne joue pas sur le terrain juridique. Il joue sur le terrain technique.
Un fait technique n'est pas attaquable juridiquement.
FREK est un notaire de fait — jamais un juge de droit.

CE QUE FREK NE DIT JAMAIS:
✗ Cet artiste est l'auteur de cette œuvre
✗ Cette œuvre est originale
✗ Ces droits lui appartiennent
✗ Cette œuvre ne viole aucun droit
✗ Ce dépôt vaut enregistrement légal

CE QUE FREK DIT SEULEMENT:
✓ Ce signal fréquentiel avec ces caractéristiques
✓ A été soumis par cet identifiant
✓ A ce timestamp précis
✓ Depuis cet endroit
✓ Et ce fait technique est reproductible et vérifiable par quiconque

STATE_6 hardening (2026-09-02, docs/architecture/
FREK_HISTORICAL_COMPATIBILITY_MATRIX.md): the "ALWAYS" line above and
`to_legal_text()`'s own closing sentence used to say "mathématiquement
irréfutable" — an unqualified overclaim the founder's D5/STATE_6
instructions explicitly named for removal. Fixed in both places; every
other field/behavior of this module is unchanged.

5 COUCHES DE PROTECTION JURIDIQUE:
1. CGU — Transfert de responsabilité
2. RGPD — Vecteur = donnée technique (pas personnelle)
3. Pas d'audio — Empreinte seulement, zéro droit voisin
4. Open source — Méthodologie publique et vérifiable
5. Juridictions — France + USA + OAPI (triple ancrage)
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime, timezone


class JuridicalStatement(Enum):
    """Types de déclarations juridiques"""
    NEVER = "never"      # Ce que FREK ne dit jamais
    ALWAYS = "always"    # Ce que FREK dit toujours


class ProtectionLayer(Enum):
    """Couches de protection juridique"""
    CGU = "cgu"
    RGPD = "rgpd"
    NO_AUDIO = "no_audio"
    OPEN_SOURCE = "open_source"
    JURISDICTIONS = "jurisdictions"


class Jurisdiction(Enum):
    """Juridictions supportées"""
    FRANCE = "france"
    USA = "usa"
    OAPI = "oapi"  # 17 pays africains francophones


@dataclass
class LegalStatement:
    """Déclaration légale"""
    statement: str
    type: JuridicalStatement
    explanation: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "statement": self.statement,
            "type": self.type.value,
            "explanation": self.explanation,
        }


@dataclass
class ProtectionLayerSpec:
    """Spécification d'une couche de protection"""
    layer: ProtectionLayer
    name: str
    description: str
    legal_basis: str
    compliance_status: str = "compliant"
    
    def to_dict(self) -> dict:
        return {
            "layer": self.layer.value,
            "name": self.name,
            "description": self.description,
            "legal_basis": self.legal_basis,
            "compliance_status": self.compliance_status,
        }


@dataclass
class TechnicalAttestation:
    """Attestation technique (ce que FREK certifie)"""
    sha256_signal: str
    vector_dimensions: int
    artiste_id: str
    timestamp_iso: str
    gps_coordinates: Optional[str]
    
    def to_legal_text(self) -> str:
        """Génère le texte descriptif de l'attestation.

        STATE_6 hardening (2026-09-02, `docs/architecture/
        FREK_HISTORICAL_COMPATIBILITY_MATRIX.md`, D5 legacy
        reconciliation): the historical closing sentence here read "Ce
        fait est mathematiquement certain et temporellement
        irrefutable" — an unqualified overclaim confirmed, by reading
        this exact function, to be produced from caller-supplied,
        unverified values with no independent check against any
        canonical FREKCORE state. Per the founder's explicit D5/STATE_6
        instruction ("Do NOT preserve... 'mathematically irrefutable'
        wording"), this closing sentence is rewritten below to describe
        only what this function actually did — format the caller's own
        submitted values — without asserting their truth. Every other
        field of this dict is unchanged (non-breaking)."""
        gps_part = f" depuis les coordonnées [{self.gps_coordinates}]" if self.gps_coordinates else ""

        return (
            f"Le signal audio portant l'empreinte SHA-256 [{self.sha256_signal[:12]}...] "
            f"et le vecteur fréquentiel [v{self.vector_dimensions}D] "
            f"a été soumis via l'identifiant [{self.artiste_id}] "
            f"le {self.timestamp_iso}{gps_part}. "
            f"Ce texte décrit fidèlement les valeurs soumises par l'appelant ; "
            f"il ne constitue ni une preuve juridique de propriété ou de paternité, "
            f"ni un acte notarié, ni un horodatage électronique qualifié. Pour un "
            f"rapport technique vérifiable, généré uniquement à partir de l'état "
            f"canonique FREKCORE (jamais des seules valeurs de l'appelant), voir "
            f"POST /api/v1/reports/technical-evidence."
        )

    def to_dict(self) -> dict:
        return {
            "sha256_signal": self.sha256_signal,
            "vector_dimensions": self.vector_dimensions,
            "artiste_id": self.artiste_id,
            "timestamp_iso": self.timestamp_iso,
            "gps_coordinates": self.gps_coordinates,
            "legal_text": self.to_legal_text(),
            "canonical_technical_evidence_report_endpoint": "/api/v1/reports/technical-evidence",
        }


class Node09Juridique:
    """
    Framework juridique FREK — Notaire de fait
    
    Principe fondamental: FREK certifie des FAITS TECHNIQUES,
    pas des DROITS JURIDIQUES.
    
    Neutralité totale:
    - Jamais juge de droit
    - Toujours notaire de fait
    - Zéro stockage audio = zéro droit voisin
    - Triple ancrage juridictionnel
    """
    
    # Ce que FREK ne dit JAMAIS
    NEVER_STATEMENTS = [
        LegalStatement(
            statement="Cet artiste est l'auteur de cette œuvre",
            type=JuridicalStatement.NEVER,
            explanation="FREK certifie un identifiant, pas une identité",
        ),
        LegalStatement(
            statement="Cette œuvre est originale",
            type=JuridicalStatement.NEVER,
            explanation="FREK certifie l'unicité du signal, pas l'originalité créative",
        ),
        LegalStatement(
            statement="Ces droits lui appartiennent",
            type=JuridicalStatement.NEVER,
            explanation="FREK ne traite pas de propriété intellectuelle",
        ),
        LegalStatement(
            statement="Cette œuvre ne viole aucun droit",
            type=JuridicalStatement.NEVER,
            explanation="FREK ne fait pas d'analyse juridique",
        ),
        LegalStatement(
            statement="Ce dépôt vaut enregistrement légal",
            type=JuridicalStatement.NEVER,
            explanation="FREK est une preuve technique, pas un registre officiel",
        ),
    ]
    
    # Ce que FREK dit TOUJOURS
    ALWAYS_STATEMENTS = [
        LegalStatement(
            statement="Ce signal fréquentiel avec ces caractéristiques",
            type=JuridicalStatement.ALWAYS,
            explanation="Vecteur 528D extrait mathématiquement",
        ),
        LegalStatement(
            statement="A été soumis par cet identifiant",
            type=JuridicalStatement.ALWAYS,
            explanation="Artiste_id anonyme et vérifiable",
        ),
        LegalStatement(
            statement="A ce timestamp précis",
            type=JuridicalStatement.ALWAYS,
            explanation="Horodatage milliseconde UTC",
        ),
        LegalStatement(
            statement="Depuis cet endroit",
            type=JuridicalStatement.ALWAYS,
            explanation="GPS condensé si fourni",
        ),
        LegalStatement(
            statement="Et ce fait technique est reproductible et vérifiable par quiconque",
            type=JuridicalStatement.ALWAYS,
            explanation=(
                "SHA-256 chaîné, recalculable par quiconque à partir des mêmes "
                "données — une propriété technique de vérifiabilité, jamais une "
                "conclusion juridique (voir to_legal_text() et le module "
                "docstring pour le contexte de durcissement STATE_6)."
            ),
        ),
    ]
    
    # Couches de protection
    PROTECTION_LAYERS = [
        ProtectionLayerSpec(
            layer=ProtectionLayer.CGU,
            name="Conditions Générales d'Utilisation",
            description="L'utilisateur déclare être titulaire des droits sur le fichier soumis. FREK prend acte. La responsabilité est transférée contractuellement.",
            legal_basis="Droit des contrats - Article 1103 Code Civil FR",
        ),
        ProtectionLayerSpec(
            layer=ProtectionLayer.RGPD,
            name="Protection des données personnelles",
            description="Le vecteur spectral n'est pas une donnée personnelle — c'est une donnée technique. Les données personnelles sont séparées et minimes. Conformité totale.",
            legal_basis="RGPD Article 4 - Définition données personnelles",
        ),
        ProtectionLayerSpec(
            layer=ProtectionLayer.NO_AUDIO,
            name="Pas de stockage audio",
            description="FREK ne stocke jamais le fichier audio. Il stocke l'empreinte. Comme une empreinte digitale — pas le doigt. Aucun droit voisin déclenché. Aucune redevance due.",
            legal_basis="Code PI L.211-1 et suivants - Droits voisins",
        ),
        ProtectionLayerSpec(
            layer=ProtectionLayer.OPEN_SOURCE,
            name="Méthodologie publique",
            description="FREK publie en open source. La méthodologie est publique et vérifiable. Personne ne peut attaquer un standard ouvert sans attaquer la communauté entière.",
            legal_basis="Licence MIT / Apache 2.0",
        ),
        ProtectionLayerSpec(
            layer=ProtectionLayer.JURISDICTIONS,
            name="Triple ancrage juridictionnel",
            description="FREK opère depuis une structure compatible droit français + droit américain + OAPI. Triple ancrage juridictionnel. Inattaquable depuis une seule juridiction.",
            legal_basis="Droit international privé - Forum shopping défensif",
        ),
    ]
    
    # Juridictions OAPI (17 pays)
    OAPI_COUNTRIES = [
        "Bénin", "Burkina Faso", "Cameroun", "Centrafrique", "Comores",
        "Congo", "Côte d'Ivoire", "Gabon", "Guinée", "Guinée-Bissau",
        "Guinée équatoriale", "Mali", "Mauritanie", "Niger", "Sénégal",
        "Tchad", "Togo"
    ]
    
    def __init__(self):
        self._jurisdictions = [Jurisdiction.FRANCE, Jurisdiction.USA, Jurisdiction.OAPI]
    
    def get_principle(self) -> Dict:
        """Retourne le principe juridique fondamental"""
        return {
            "principle": "notaire_de_fait",
            "not": "juge_de_droit",
            "explanation": "FREK certifie des faits techniques, pas des droits juridiques",
            "core_statements": {
                "never": [s.to_dict() for s in self.NEVER_STATEMENTS],
                "always": [s.to_dict() for s in self.ALWAYS_STATEMENTS],
            },
        }
    
    def get_protection_layers(self) -> List[Dict]:
        """Retourne les couches de protection juridique"""
        return [layer.to_dict() for layer in self.PROTECTION_LAYERS]
    
    def get_jurisdictions(self) -> Dict:
        """Retourne les juridictions supportées"""
        return {
            "jurisdictions": [j.value for j in self._jurisdictions],
            "triple_anchor": True,
            "oapi_countries": self.OAPI_COUNTRIES,
            "oapi_count": len(self.OAPI_COUNTRIES),
            "strategy": "Inattaquable depuis une seule juridiction",
        }
    
    def create_attestation(
        self,
        sha256_signal: str,
        vector_dimensions: int,
        artiste_id: str,
        timestamp_ms: int,
        gps_lat: Optional[float] = None,
        gps_lon: Optional[float] = None,
    ) -> TechnicalAttestation:
        """Crée une attestation technique"""
        timestamp_iso = datetime.fromtimestamp(
            timestamp_ms / 1000, tz=timezone.utc
        ).strftime("%d.%m.%Y à %H:%M:%S.%f")[:-3]
        
        gps_coordinates = None
        if gps_lat is not None and gps_lon is not None:
            gps_coordinates = f"{gps_lat:.2f}, {gps_lon:.2f}"
        
        return TechnicalAttestation(
            sha256_signal=sha256_signal,
            vector_dimensions=vector_dimensions,
            artiste_id=artiste_id,
            timestamp_iso=timestamp_iso,
            gps_coordinates=gps_coordinates,
        )
    
    def get_what_frek_never_says(self) -> List[str]:
        """Liste ce que FREK ne dit jamais"""
        return [s.statement for s in self.NEVER_STATEMENTS]
    
    def get_what_frek_always_says(self) -> List[str]:
        """Liste ce que FREK dit toujours"""
        return [s.statement for s in self.ALWAYS_STATEMENTS]
    
    def check_compliance(self) -> Dict:
        """Vérifie la conformité juridique"""
        all_compliant = all(
            layer.compliance_status == "compliant"
            for layer in self.PROTECTION_LAYERS
        )
        
        return {
            "overall_status": "compliant" if all_compliant else "review_needed",
            "layers_checked": len(self.PROTECTION_LAYERS),
            "all_compliant": all_compliant,
            "audio_stored": False,
            "personal_data_stored": False,
            "rgpd_compliant": True,
            "open_source": True,
            "jurisdictions_count": len(self._jurisdictions),
        }
    
    async def get_stats(self) -> Dict:
        """Statistiques juridiques"""
        return {
            "principle": "notaire_de_fait",
            "never_statements": len(self.NEVER_STATEMENTS),
            "always_statements": len(self.ALWAYS_STATEMENTS),
            "protection_layers": len(self.PROTECTION_LAYERS),
            "jurisdictions": len(self._jurisdictions),
            "oapi_countries": len(self.OAPI_COUNTRIES),
            "audio_stored": "JAMAIS",
            "rgpd_status": "conforme",
            "open_source": True,
        }


# Instance globale
node09 = Node09Juridique()
