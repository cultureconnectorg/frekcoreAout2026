"""
FREK v2 — NODE 10 · INSTITUTIONNEL
===================================
FREK pour un État c'est un observatoire culturel en temps réel.
Pas du contrôle — de la connaissance.
Des données anonymisées. Une souveraineté culturelle numérique.

OFFRES INSTITUTIONNELLES:
1. MINISTÈRE CULTURE — Observatoire création nationale
2. DROITS D'AUTEUR — SACEM/URADEX, preuve recevable
3. PATRIMOINE — Archives nationales, langues, traditions
4. EXPORT CULTUREL — Diplomatie, soft power
5. FISCAL — Économie créative, subventions
6. SOUVERAINETÉ — Données locales, sans GAFAM

OAPI — 17 pays africains francophones:
Un gouvernement adopte FREK = toute sa filière créative structurée.
Propagation naturelle entre les 17 membres.

CVL BRAIN + FREK = Système nerveux culturel
CVL BRAIN: Analyse, visualise, interprète
FREK: Capte, certifie, stocke
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime, timezone


class InstitutionalClient(Enum):
    """Types de clients institutionnels"""
    MINISTRY_CULTURE = "ministry_culture"
    COPYRIGHT_OFFICE = "copyright_office"
    NATIONAL_ARCHIVES = "national_archives"
    DIPLOMATIC = "diplomatic"
    FISCAL = "fiscal"
    SOVEREIGNTY = "sovereignty"


class DataAccessLevel(Enum):
    """Niveaux d'accès aux données"""
    PUBLIC = "public"           # Statistiques agrégées
    INSTITUTION = "institution" # Données anonymisées détaillées
    RESEARCH = "research"       # Données pour recherche
    AUDIT = "audit"             # Vérification conformité


@dataclass
class InstitutionalOffer:
    """Offre pour un type de client institutionnel"""
    client_type: InstitutionalClient
    name: str
    description: str
    data_provided: List[str]
    benefits: List[str]
    data_access_level: DataAccessLevel
    
    def to_dict(self) -> dict:
        return {
            "client_type": self.client_type.value,
            "name": self.name,
            "description": self.description,
            "data_provided": self.data_provided,
            "benefits": self.benefits,
            "data_access_level": self.data_access_level.value,
        }


@dataclass
class OAPICountry:
    """Pays membre de l'OAPI"""
    name: str
    code: str
    adoption_status: str = "potential"  # potential, piloting, adopted
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "code": self.code,
            "adoption_status": self.adoption_status,
        }


@dataclass
class CulturalObservatoryMetrics:
    """Métriques pour l'observatoire culturel"""
    period_start: int  # timestamp_ms
    period_end: int
    total_emissions: int
    unique_artistes: int
    genres_distribution: Dict[str, int]
    geographic_distribution: Dict[str, int]
    trending_frequencies: List[str]
    
    def to_dict(self) -> dict:
        return {
            "period_start": self.period_start,
            "period_end": self.period_end,
            "total_emissions": self.total_emissions,
            "unique_artistes": self.unique_artistes,
            "genres_distribution": self.genres_distribution,
            "geographic_distribution": self.geographic_distribution,
            "trending_frequencies": self.trending_frequencies,
        }


class Node10Institutionnel:
    """
    Offres institutionnelles FREK — Observatoire culturel
    
    Valeur pour l'État:
    - Connaissance, pas contrôle
    - Données anonymisées
    - Souveraineté numérique
    - Démocratique et transparent
    """
    
    # Offres par type de client
    INSTITUTIONAL_OFFERS = [
        InstitutionalOffer(
            client_type=InstitutionalClient.MINISTRY_CULTURE,
            name="Observatoire",
            description="Cartographie temps réel de la production nationale",
            data_provided=[
                "Combien d'œuvres créées ce mois ?",
                "Quels genres dominent ?",
                "Quels artistes émergent ?",
                "Données pour politiques culturelles",
            ],
            benefits=[
                "Vision en temps réel",
                "Aide à la décision",
                "Mesure d'impact des politiques",
            ],
            data_access_level=DataAccessLevel.INSTITUTION,
        ),
        InstitutionalOffer(
            client_type=InstitutionalClient.COPYRIGHT_OFFICE,
            name="SACEM / URADEX",
            description="FREK-ID comme preuve recevable",
            data_provided=[
                "Antériorité prouvée automatiquement",
                "Chaîne de dérivation traçable",
                "Simplification administrative",
            ],
            benefits=[
                "Réduction fraude aux droits",
                "Automatisation vérifications",
                "Preuves irréfutables",
            ],
            data_access_level=DataAccessLevel.AUDIT,
        ),
        InstitutionalOffer(
            client_type=InstitutionalClient.NATIONAL_ARCHIVES,
            name="Patrimoine",
            description="Archives nationales création nationale",
            data_provided=[
                "Langues créoles certifiées",
                "Musiques traditionnelles préservées",
                "Contes, poésies, patrimoine oral",
                "Bibliothèque fréquentielle perpétuelle",
            ],
            benefits=[
                "Préservation automatique",
                "Catalogage systématique",
                "Accès facilité",
            ],
            data_access_level=DataAccessLevel.RESEARCH,
        ),
        InstitutionalOffer(
            client_type=InstitutionalClient.DIPLOMATIC,
            name="Export culturel",
            description="Diplomatie culturelle basée sur des faits",
            data_provided=[
                "FREK-ID reconnu = crédibilité internationale",
                "Artistes certifiés = représentants officiels",
            ],
            benefits=[
                "Levier diplomatique culturel",
                "Soft power basé sur des faits",
                "Rayonnement international",
            ],
            data_access_level=DataAccessLevel.PUBLIC,
        ),
        InstitutionalOffer(
            client_type=InstitutionalClient.FISCAL,
            name="Économie créative",
            description="Mesure de la filière créative nationale",
            data_provided=[
                "Base de données pour subventions",
                "Justification aides sectorielles",
                "Retour sur investissement culturel",
            ],
            benefits=[
                "Données objectives",
                "Allocation optimisée",
                "Transparence",
            ],
            data_access_level=DataAccessLevel.INSTITUTION,
        ),
        InstitutionalOffer(
            client_type=InstitutionalClient.SOVEREIGNTY,
            name="Souveraineté données",
            description="Données culturelles hébergées localement",
            data_provided=[
                "Pas de dépendance GAFAM",
                "Standard ouvert = indépendance totale",
                "Exportable vers d'autres nations",
            ],
            benefits=[
                "Contrôle total",
                "Interopérabilité",
                "Pérennité",
            ],
            data_access_level=DataAccessLevel.INSTITUTION,
        ),
    ]
    
    # Pays OAPI
    OAPI_COUNTRIES = [
        OAPICountry("Bénin", "BJ"),
        OAPICountry("Burkina Faso", "BF"),
        OAPICountry("Cameroun", "CM"),
        OAPICountry("Centrafrique", "CF"),
        OAPICountry("Comores", "KM"),
        OAPICountry("Congo", "CG"),
        OAPICountry("Côte d'Ivoire", "CI"),
        OAPICountry("Gabon", "GA"),
        OAPICountry("Guinée", "GN"),
        OAPICountry("Guinée-Bissau", "GW"),
        OAPICountry("Guinée équatoriale", "GQ"),
        OAPICountry("Mali", "ML"),
        OAPICountry("Mauritanie", "MR"),
        OAPICountry("Niger", "NE"),
        OAPICountry("Sénégal", "SN"),
        OAPICountry("Tchad", "TD"),
        OAPICountry("Togo", "TG"),
    ]
    
    def __init__(self, memory_node=None):
        self._memory = memory_node
        self._cvl_brain_active = True
    
    def set_memory_node(self, memory_node):
        """Injecte le NODE 04 pour accès aux données"""
        self._memory = memory_node
    
    def get_offers(
        self,
        client_type: Optional[InstitutionalClient] = None,
    ) -> List[Dict]:
        """Retourne les offres institutionnelles"""
        result = []
        for offer in self.INSTITUTIONAL_OFFERS:
            if client_type is None or offer.client_type == client_type:
                result.append(offer.to_dict())
        return result
    
    def get_offer_for_client(self, client_type: InstitutionalClient) -> Optional[Dict]:
        """Retourne l'offre pour un type de client spécifique"""
        for offer in self.INSTITUTIONAL_OFFERS:
            if offer.client_type == client_type:
                return offer.to_dict()
        return None
    
    def get_oapi_info(self) -> Dict:
        """Informations sur l'OAPI"""
        return {
            "name": "Organisation Africaine de la Propriété Intellectuelle",
            "countries": [c.to_dict() for c in self.OAPI_COUNTRIES],
            "total_countries": len(self.OAPI_COUNTRIES),
            "adoption_strategy": (
                "Un seul gouvernement membre adopte FREK comme standard de certification "
                "des œuvres — toute sa filière créative est structurée instantanément. "
                "La propagation est naturelle entre les 17 membres partageant le même cadre juridique."
            ),
            "potential_reach": "17 pays africains francophones",
        }
    
    def get_cvl_brain_info(self) -> Dict:
        """Informations sur l'intégration CVL BRAIN"""
        return {
            "cvl_brain": {
                "role": "Analyse, visualise et interprète les données culturelles",
                "outputs": "Tableaux de bord, tendances, indicateurs sectoriels",
            },
            "frek": {
                "role": "Capte, certifie et stocke les données sources",
                "outputs": "Chaque émission FREK est un point de donnée pour CVL BRAIN",
            },
            "ensemble": {
                "description": "L'observatoire culturel le plus précis jamais construit",
                "properties": [
                    "Données anonymisées",
                    "Souveraineté garantie",
                    "Temps réel",
                ],
            },
            "for_state": (
                "Un dashboard ministériel qui répond en temps réel : "
                "combien d'œuvres, quels genres, quels artistes, quels lieux, quelle évolution."
            ),
        }
    
    async def generate_observatory_metrics(
        self,
        period_start_ms: int,
        period_end_ms: int,
    ) -> CulturalObservatoryMetrics:
        """Génère les métriques pour l'observatoire culturel"""
        # En prod: requête vers NODE 04 pour récupérer les données
        # Ici: données simulées pour démonstration
        
        total_emissions = 0
        unique_artistes = set()
        genres = {}
        locations = {}
        
        if self._memory:
            # Récupérer les données réelles
            attestations = await self._memory.get_latest(10000)
            for att in attestations:
                if period_start_ms <= att.timestamp_ms <= period_end_ms:
                    total_emissions += 1
                    unique_artistes.add(att.artiste_id)
                    
                    # Agréger par lieu
                    if att.gps_lat and att.gps_lon:
                        loc_key = f"{att.gps_lat:.0f},{att.gps_lon:.0f}"
                        locations[loc_key] = locations.get(loc_key, 0) + 1
        
        return CulturalObservatoryMetrics(
            period_start=period_start_ms,
            period_end=period_end_ms,
            total_emissions=total_emissions,
            unique_artistes=len(unique_artistes),
            genres_distribution=genres,
            geographic_distribution=locations,
            trending_frequencies=[],
        )
    
    def get_sovereignty_benefits(self) -> Dict:
        """Retourne les bénéfices de souveraineté"""
        return {
            "data_location": "Hébergement local garanti",
            "no_gafam": True,
            "open_standard": True,
            "exportable": True,
            "benefits": [
                "Contrôle total des données culturelles nationales",
                "Pas de dépendance aux géants technologiques",
                "Standard ouvert = indépendance technologique totale",
                "Données exportables vers d'autres nations partenaires",
            ],
            "philosophy": "Connaissance, pas contrôle. Démocratique et transparent.",
        }
    
    async def get_stats(self) -> Dict:
        """Statistiques institutionnelles"""
        return {
            "offers_count": len(self.INSTITUTIONAL_OFFERS),
            "client_types": len(InstitutionalClient),
            "oapi_countries": len(self.OAPI_COUNTRIES),
            "cvl_brain_active": self._cvl_brain_active,
            "data_sovereignty": True,
            "no_gafam": True,
            "access_levels": [level.value for level in DataAccessLevel],
        }


# Instance globale
node10 = Node10Institutionnel()
