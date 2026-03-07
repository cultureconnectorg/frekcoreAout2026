# FREK v2.0 - Product Requirements Document

## Project Overview
FREK® est un standard ouvert d'identification cryptographique des DJ mixes et performances musicales composites. Développé par CVLN Group (Bruxelles). Premier déploiement officiel : Culture Connect 2026, Fort-de-France, Martinique.

**Principe fondamental:** *"FREK ne reconnaît pas la musique. FREK reconnaît un fait technique, dans un contexte précis."*

## Architecture v2.0 - 11 Nœuds Complets ✅

```
┌─────────────────────────────────────────────────────────────────┐
│                    FREK v2.0 — 11 NŒUDS                         │
├─────────────────────────────────────────────────────────────────┤
│ NODE 01: EXTRACTION     │ Audio → Vecteur 528D (FFT, MFCC...)   │
│ NODE 02: IDENTITÉ       │ Triple SHA-256 → FREK-ID unique       │
│ NODE 03: CYCLE          │ 5 stades luciole (Genesis → Legacy)   │
│ NODE 04: MÉMOIRE        │ pgvector ~2.5KB/œuvre                 │
│ NODE 05: RÉSONANCE      │ Similarité, cohérence, tendances      │
├─────────────────────────────────────────────────────────────────┤
│ NODE 06: RÉSEAU         │ Graphe 5 nœuds, 17 relations          │
│ NODE 07: TRANSMISSION   │ BLE/NFC/WiFi/Ultrasons/4G             │
│ NODE 08: SYSTÈME        │ Couche entre DSP et reconnaissance    │
│ NODE 09: JURIDIQUE      │ Notaire de fait, neutralité totale    │
│ NODE 10: INSTITUTIONNEL │ CVL BRAIN, observatoire culturel      │
├─────────────────────────────────────────────────────────────────┤
│ NODE 11: INVISIBLE      │ 3% visible · 1 bouton · 3 secondes    │
└─────────────────────────────────────────────────────────────────┘
```

## Frontend Routes

| Route | Description |
|-------|-------------|
| `/` | Page d'accueil marketing |
| `/generate` | Wizard génération attestation (client-side) |
| `/certify` | **NODE 11** — Interface 1 bouton (backend API) |

## Backend API Endpoints

### Core (NODE 01-05)
```
GET  /api/frek/                      Info FREK v2
GET  /api/frek/stats                 Statistiques globales (11 nœuds)
POST /api/frek/certify               Certification audio (base64)
POST /api/frek/certify/upload        Certification (multipart)
GET  /api/frek/verify/{frek_id}      Vérification FREK-ID
POST /api/frek/genesis               Démarrer cycle GENESIS
POST /api/frek/workshop              Ajouter version WORKSHOP
POST /api/frek/extract               Extraction seule
GET  /api/frek/resonance/{frek_id}   Recherche résonance
GET  /api/frek/coherence/{artiste_id} Cohérence artiste
```

### Avancés (NODE 06-10)
```
GET  /api/frek/advanced/reseau/*           Graphe vivant
GET  /api/frek/advanced/transmission/*     Multi-protocole
GET  /api/frek/advanced/systeme/*          Position système
GET  /api/frek/advanced/juridique/*        Framework légal
GET  /api/frek/advanced/institutionnel/*   Observatoire
```

## Code Architecture
```
/app/
├── backend/
│   ├── frek/
│   │   ├── pipeline.py              # Orchestration 11 nœuds
│   │   ├── routes.py                # API core (NODE 01-05)
│   │   ├── routes_advanced.py       # API avancée (NODE 06-10)
│   │   └── nodes/
│   │       ├── node01_extraction.py  # FFT, MFCC, ZCR...
│   │       ├── node02_identity.py    # Triple SHA-256
│   │       ├── node03_cycle.py       # 5 stades luciole
│   │       ├── node04_memory.py      # pgvector storage
│   │       ├── node05_resonance.py   # Similarité engine
│   │       ├── node06_reseau.py      # Graphe vivant
│   │       ├── node07_transmission.py # BLE/NFC/WiFi/...
│   │       ├── node08_systeme.py     # Couche système
│   │       ├── node09_juridique.py   # Framework légal
│   │       └── node10_institutionnel.py # Observatoire
│   ├── server.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.jsx
        └── pages/
            ├── Generate.jsx          # Wizard client-side
            └── Certify.jsx           # NODE 11 — 1 bouton
```

## Implemented Features

### ✅ Backend FREK v2 (2025-03-07)
- [x] NODE 01-05: Core certification pipeline
- [x] NODE 06-10: Advanced features (graph, transmission, legal, institutional)
- [x] 30+ API endpoints testés et fonctionnels
- [x] Graphe auto-rempli à chaque certification

### ✅ Frontend NODE 11 (2025-03-07)
- [x] Interface ultra-minimaliste "3% visible"
- [x] 1 bouton → 17 opérations invisibles → FREK-ID
- [x] Barre de progression temps réel
- [x] QR Code scannable
- [x] Détails techniques en accordéon
- [x] Support upload + enregistrement micro

### ✅ Frontend Existant
- [x] Site marketing complet
- [x] Wizard génération attestation
- [x] Vérificateur de mix
- [x] i18n (FR, EN, ES, AR)
- [x] Tests Vitest (45/45)

## Stats Actuelles
```
Version: 2.0
Nœuds actifs: 10/11 (11 avec frontend)
Attestations: 2+
Taille par œuvre: ~2.5 KB
Graphe: Auto-alimenté
Backend: Memory (prod: PostgreSQL + pgvector)
```

## Upcoming Tasks
- [ ] Tests d'intégration complets (testing agent)
- [ ] PostgreSQL + pgvector en production
- [ ] Page de vérification publique `/verify/{frek_id}`

## Technical Notes
- **NODE 11**: L'utilisateur fait 1 geste. FREK fait 17 opérations.
- **Principe**: La confiance vient de ce qu'on ne montre pas.
- **Philosophie**: Comme une luciole — elle s'allume. C'est tout.

---
*FREK® — Preuve > Service | Local-First | Anti-Surveillance*
*© 2025–2026 CVLN Group — frekcore.com*

*Last updated: 2025-03-07*
