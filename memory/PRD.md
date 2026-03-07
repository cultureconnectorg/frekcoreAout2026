# FREK v2.0 - Product Requirements Document

## Project Overview
FREK® est un standard ouvert d'identification cryptographique des DJ mixes et performances musicales composites. Développé par CVLN Group (Bruxelles). Premier déploiement officiel : Culture Connect 2026, Fort-de-France, Martinique.

**Principe fondamental:** *"FREK ne reconnaît pas la musique. FREK reconnaît un fait technique, dans un contexte précis."*

## Design
- **Couleur principale:** Bleu FREK `#2cc4f5`
- **Interface:** Certify = page principale, 1 bouton, minimaliste
- **Philosophie:** "3% visible, 97% invisible — Comme une luciole"

## Architecture v2.0 — 11 Nœuds Complets ✅

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

## Score Tests Expert: 92/110 (84.1%) ✅

**5 Points Critiques: ✅ TOUS VALIDÉS**
1. ✅ Vecteur 528D exactement
2. ✅ Pas d'audio stocké
3. ✅ Hash chaîné vérifiable  
4. ✅ EMISSION irréversible
5. ✅ Neutralité juridique

## Frontend Routes

| Route | Description |
|-------|-------------|
| `/` | **Certify** — Page principale, 1 bouton |
| `/verify/:frekId` | Vérification publique |
| `/generate` | Wizard génération attestation |
| `/about` | Architecture et documentation |
| `/legal` | Cadre juridique |
| `/spec` | Spécifications techniques |
| `/philosophy` | Philosophie FREK |

## Backend API Endpoints

### Core (NODE 01-05)
```
GET  /api/frek/                           Info FREK v2
GET  /api/frek/stats                      Statistiques (11 nœuds)
POST /api/frek/certify                    Certification base64
POST /api/frek/certify/upload             Certification multipart
GET  /api/frek/verify/{frek_id}           Vérification
GET  /api/frek/verify/{frek_id}/qr.png    QR Code PNG
GET  /api/frek/verify/{frek_id}/certificat.pdf  Certificat PDF
POST /api/frek/genesis                    Démarrer GENESIS
POST /api/frek/workshop                   Ajouter WORKSHOP
GET  /api/frek/resonance/{frek_id}        Recherche résonance
GET  /api/frek/coherence/{artiste_id}     Cohérence artiste
```

### Avancés (NODE 06-10)
```
/api/frek/advanced/reseau/*           Graphe vivant
/api/frek/advanced/transmission/*     Multi-protocole
/api/frek/advanced/systeme/*          Position système
/api/frek/advanced/juridique/*        Framework légal
/api/frek/advanced/institutionnel/*   Observatoire
```

## Implemented Features

### ✅ Backend FREK v2
- [x] 11 nœuds complets
- [x] Vecteur exactement 528D
- [x] QR Code PNG endpoint
- [x] Certificat PDF endpoint
- [x] Message juridique neutre

### ✅ Frontend NODE 11
- [x] Design bleu FREK #2cc4f5
- [x] Certify = page principale
- [x] 1 bouton → 17 opérations
- [x] Page Verify.jsx publique
- [x] Pages Legal, Spec, Philosophy
- [x] UI responsive (mobile/tablet/desktop)

## Technical Notes
- **Vecteur:** 528D = 512 FFT + 1 RMS + 1 ZCR + 12 MFCC + 1 Centroid + 1 Flux
- **Backend:** FastAPI + MongoDB (fallback) / PostgreSQL + pgvector (prod)
- **Frontend:** React 18 + Vite + Tailwind CSS
- **Temps certification:** ~3s

## Backlog

### P0 (Urgent)
- Aucun

### P1 (Important)
- Augmenter le score de 92/110 à 100/110 (corriger les 5 warnings restants)

### P2 (Nice to have)
- Tests d'acceptation utilisateur
- Préparation déploiement production

---
*FREK® — Preuve > Service | Local-First | Anti-Surveillance*
*© 2025–2026 CVLN Group — frekcore.com*

*Last updated: 2025-03-07*
