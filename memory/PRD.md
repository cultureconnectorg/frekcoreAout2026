# FREK v2.0 - Product Requirements Document

## Project Overview
FREK® est un standard ouvert d'identification cryptographique des DJ mixes et performances musicales composites. Développé par CVLN Group (Bruxelles). Premier déploiement officiel : Culture Connect 2026, Fort-de-France, Martinique.

**Principe fondamental:** *"FREK ne reconnaît pas la musique. FREK reconnaît un fait technique, dans un contexte précis."*

## Architecture v2.0 - 11 Nœuds Complets

### Nœuds Core (1-5) ✅ IMPLÉMENTÉS
```
NODE 01: EXTRACTION — Signal brut → Vecteur 528D (FFT, MFCC, ZCR, etc.)
NODE 02: IDENTITÉ — Vecteur → FREK-ID (triple SHA-256)
NODE 03: CYCLE — 5 stades luciole (Genesis → Legacy)
NODE 04: MÉMOIRE — pgvector, ~2.5KB/œuvre
NODE 05: RÉSONANCE — Similarité, cohérence, tendances
```

### Nœuds Avancés (6-10) ✅ IMPLÉMENTÉS
```
NODE 06: RÉSEAU — Graphe vivant (5 types nœuds, 17 relations)
NODE 07: TRANSMISSION — Multi-protocole (BLE, NFC, WiFi, Ultrasons, 4G/5G)
NODE 08: SYSTÈME — Couche système (entre DSP et reconnaissance)
NODE 09: JURIDIQUE — Notaire de fait, neutralité totale
NODE 10: INSTITUTIONNEL — Observatoire culturel, OAPI 17 pays
```

### NODE 11: INVISIBLE (Frontend simplifié)
```
À IMPLÉMENTER: Interface utilisateur qui cache la complexité
```

## API Endpoints

### Core (NODE 01-05)
- `GET /api/frek/` — Info FREK v2
- `GET /api/frek/stats` — Statistiques globales
- `POST /api/frek/certify` — Certification audio (base64)
- `POST /api/frek/certify/upload` — Certification (multipart)
- `GET /api/frek/verify/{frek_id}` — Vérification FREK-ID
- `POST /api/frek/genesis` — Démarrer cycle GENESIS
- `POST /api/frek/workshop` — Ajouter version WORKSHOP
- `POST /api/frek/extract` — Extraction seule
- `GET /api/frek/resonance/{frek_id}` — Recherche résonance
- `GET /api/frek/coherence/{artiste_id}` — Cohérence artiste

### Avancés (NODE 06-10)
#### NODE 06 - RÉSEAU
- `GET /api/frek/advanced/reseau` — Info graphe
- `GET /api/frek/advanced/reseau/stats` — Stats graphe
- `GET /api/frek/advanced/reseau/node/{id}` — Nœud par ID
- `GET /api/frek/advanced/reseau/neighbors/{id}` — Voisins
- `GET /api/frek/advanced/reseau/artiste/{id}` — Sous-graphe artiste
- `GET /api/frek/advanced/reseau/lieu/{id}` — Activité lieu
- `GET /api/frek/advanced/reseau/path` — Chemin entre nœuds

#### NODE 07 - TRANSMISSION
- `GET /api/frek/advanced/transmission` — Info transmission
- `GET /api/frek/advanced/transmission/protocols` — Liste protocoles
- `POST /api/frek/advanced/transmission/packet` — Créer paquet
- `POST /api/frek/advanced/transmission/watermark` — Créer filigrane
- `POST /api/frek/advanced/transmission/sync` — Sync offline

#### NODE 08 - SYSTÈME
- `GET /api/frek/advanced/systeme` — Info système
- `GET /api/frek/advanced/systeme/position` — Position dans stack
- `GET /api/frek/advanced/systeme/references` — Références (Dolby, Shazam...)
- `GET /api/frek/advanced/systeme/roadmap` — Roadmap adoption
- `GET /api/frek/advanced/systeme/integrations` — Intégrations

#### NODE 09 - JURIDIQUE
- `GET /api/frek/advanced/juridique` — Info juridique
- `GET /api/frek/advanced/juridique/principle` — Principe fondamental
- `GET /api/frek/advanced/juridique/protection` — Couches protection
- `GET /api/frek/advanced/juridique/jurisdictions` — Juridictions
- `GET /api/frek/advanced/juridique/compliance` — Conformité
- `POST /api/frek/advanced/juridique/attestation` — Attestation légale

#### NODE 10 - INSTITUTIONNEL
- `GET /api/frek/advanced/institutionnel` — Info institutionnel
- `GET /api/frek/advanced/institutionnel/offers` — Offres clients
- `GET /api/frek/advanced/institutionnel/oapi` — Info OAPI (17 pays)
- `GET /api/frek/advanced/institutionnel/cvl-brain` — Info CVL BRAIN
- `GET /api/frek/advanced/institutionnel/sovereignty` — Souveraineté
- `GET /api/frek/advanced/institutionnel/observatory` — Métriques observatoire

## Code Architecture
```
/app/
├── backend/
│   ├── frek/
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Orchestration 11 nœuds
│   │   ├── routes.py           # API core (NODE 01-05)
│   │   ├── routes_advanced.py  # API avancée (NODE 06-10)
│   │   ├── nodes/
│   │   │   ├── node01_extraction.py
│   │   │   ├── node02_identity.py
│   │   │   ├── node03_cycle.py
│   │   │   ├── node04_memory.py
│   │   │   ├── node05_resonance.py
│   │   │   ├── node06_reseau.py
│   │   │   ├── node07_transmission.py
│   │   │   ├── node08_systeme.py
│   │   │   ├── node09_juridique.py
│   │   │   └── node10_institutionnel.py
│   │   ├── models/
│   │   └── utils/
│   ├── server.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    └── ... (React frontend existant)
```

## Implemented Features

### ✅ Backend FREK v2 Core (2025-03-07)
- [x] NODE 01: Extraction 528D (FFT, MFCC, ZCR, Centroid, Flux, RMS)
- [x] NODE 02: Triple SHA-256, FREK-ID format FREK-YYYY-NNNN-xxxx-yyyy
- [x] NODE 03: 5 stades luciole (Genesis → Legacy)
- [x] NODE 04: Stockage mémoire avec fallback pgvector
- [x] NODE 05: Similarité cosine, cohérence artiste, alertes plagiat

### ✅ Backend FREK v2 Avancé (2025-03-07)
- [x] NODE 06: Graphe vivant (5 types nœuds, 17 relations bidirectionnelles)
- [x] NODE 07: Multi-protocole (BLE, NFC, WiFi, Ultrasons, 4G/5G)
- [x] NODE 08: Position système (entre DSP et reconnaissance)
- [x] NODE 09: Framework juridique (notaire de fait, RGPD, triple juridiction)
- [x] NODE 10: Offres institutionnelles (6 types clients, OAPI 17 pays)

### ✅ Frontend Existant
- [x] Wizard générateur d'attestation
- [x] QR Code scannable
- [x] Vérificateur de mix
- [x] i18n (FR, EN, ES, AR)
- [x] Accessibilité WCAG 2.1 AA
- [x] Tests Vitest (45/45)

## Upcoming Tasks
- [ ] NODE 11: Interface utilisateur simplifiée (frontend v2)
- [ ] Intégration Frontend ↔ Backend API v2
- [ ] Pages UI des 5 fichiers HTML spécifiés
- [ ] Tests intégration complets
- [ ] PostgreSQL + pgvector en production

## Technical Notes
- **10 nœuds actifs** sur 11
- **Backend**: FastAPI + MongoDB (fallback) / PostgreSQL + pgvector (production)
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Stockage**: ~2.5 KB par œuvre certifiée
- **Temps certification**: ~3s (première) / ~10ms (suivantes)

---
*FREK® — Preuve > Service | Local-First | Anti-Surveillance*
*© 2025–2026 CVLN Group — frekcore.com*

*Last updated: 2025-03-07*
