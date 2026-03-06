# FREK v2.0 - Product Requirements Document

## Project Overview
FREK® est un standard ouvert d'identification cryptographique des DJ mixes et performances musicales composites. Développé par CVLN Group (Bruxelles). Premier déploiement officiel : Culture Connect 2026, Fort-de-France, Martinique.

**Principe fondamental:** *"FREK ne reconnaît pas la musique. FREK reconnaît un fait technique, dans un contexte précis."*

## Architecture v2.0

```
/app/frontend/
├── index.html                     # Point d'entrée Vite
├── vite.config.js                 # Configuration Vite
├── tailwind.config.js             # Design system (terra/gold/navy)
├── netlify.toml                   # Déploiement Netlify
├── public/
│   └── favicon.svg
└── src/
    ├── main.jsx                   # Bootstrap React
    ├── App.jsx                    # Assemblage sections
    ├── index.css                  # Styles globaux + noise overlay
    ├── components/
    │   ├── layout/
    │   │   ├── Nav.jsx           # Navigation fixe backdrop blur
    │   │   └── Footer.jsx        # Footer 3 colonnes + pills
    │   ├── sections/
    │   │   ├── Hero.jsx          # Hero 2 colonnes + JSON animé
    │   │   ├── Philosophie.jsx   # 3 piliers + citation
    │   │   ├── Architecture.jsx  # Flow 4 étapes
    │   │   ├── Produits.jsx      # FREK Go vs FREK Node
    │   │   ├── Verifier.jsx      # Outil vérification (CRITIQUE)
    │   │   ├── Spec.jsx          # Champs + code sticky
    │   │   ├── FrekId.jsx        # Décomposition FREK-ID
    │   │   ├── CultureConnect.jsx# CC2026 + cartes attestation
    │   │   ├── Ecosysteme.jsx    # 6 cartes intégrations
    │   │   └── Roadmap.jsx       # 4 jalons
    │   └── ui/
    │       ├── RevealWrapper.jsx # Intersection Observer
    │       ├── SectionTag.jsx    # Label section
    │       ├── Divider.jsx       # Séparateur gradient
    │       └── JsonBlock.jsx     # Code coloré
    ├── hooks/
    │   ├── useAudioFingerprint.js # FFT + SHA-256 Web Audio API
    │   ├── useJsonVerify.js       # Validation schéma .frek.json
    │   └── useScrollReveal.js     # Intersection Observer
    └── data/
        ├── spec-fields.js        # 15 champs schéma
        ├── roadmap.js            # Données jalons
        └── ecosystem.js          # Données cartes
```

## Design System

### Couleurs
- **terra:** `#C4714A` — Couleur principale, accents, CTA
- **gold:** `#D4A84B` — Accents secondaires, highlights
- **dark:** `#080808` — Background principal
- **navy:** `#0D1B2A` — Sections alternées
- **teal:** `#0A4A4A` — Accent FREK Go
- **fgreen:** `#1A4A2A` — Niveaux de preuve "fort"
- **light:** `#F2EDE4` — Texte principal
- **mid:** `#C8C0B0` — Texte secondaire
- **dim:** `#6A6258` — Texte tertiaire

### Typographie
- **Bebas Neue** — Titres, logo FREK, grands nombres
- **DM Mono** — Labels, tags, code, UI technique
- **DM Sans** — Corps de texte, paragraphes

## Implemented Features (2024-12-19)

### ✅ Stack Migration
- [x] Migration CRA → Vite 5
- [x] React 18 + Framer Motion
- [x] Tailwind CSS avec config étendue
- [x] Netlify config prêt

### ✅ Sections complètes
- [x] **Nav:** Navigation fixe + backdrop blur + CTA
- [x] **Hero:** 2 colonnes + JSON animé + badge VÉRIFIÉ
- [x] **Philosophie:** 3 piliers + citation encadrée
- [x] **Architecture:** Flow 4 étapes + responsabilités
- [x] **Produits:** FREK Go vs FREK Node comparaison
- [x] **Verifier:** Tabs Audio/JSON (fonctionnel)
- [x] **Spec:** 15 champs + code sticky coloré
- [x] **FrekId:** Décomposition visuelle FREK-2026-MQ-001
- [x] **Culture Connect 2026:** Cartes attestations animées
- [x] **Ecosystème:** 6 cartes intégrations
- [x] **Roadmap:** v0.4 → v1.0
- [x] **Footer:** 3 colonnes + pills

### ✅ Outils fonctionnels
- [x] **Audio Fingerprint:** FFT + RMS + Zero Crossing Rate + SHA-256
- [x] **JSON Verification:** Validation schéma .frek.json complet
- [x] Drop zone drag & drop
- [x] Progress bar animée
- [x] Résultats avec checks colorés

### ✅ Animations
- [x] Framer Motion scroll reveal
- [x] Stagger animation hero
- [x] Tab transitions AnimatePresence
- [x] Hover effects cartes
- [x] Badge pulse CC2026

### ✅ Responsive
- [x] Mobile: JSON preview masqué, nav collapsée
- [x] Tablet: Layout adaptatif
- [x] Desktop: Full 2 colonnes

## Technical Specifications

### Audio Fingerprinting Algorithm
```javascript
// 1. Decode audio → PCM 44.1kHz
// 2. Segment → 3 secondes (max 10 segments)
// 3. Pour chaque segment:
//    - RMS (Root Mean Square)
//    - ZCR (Zero Crossing Rate)
// 4. Hash features → SHA-256
// 5. Combiner hashes → fingerprint final
// Format: frek:fp:<sha256_hex>
```

### JSON Schema (v0.4)
- frek_version, mix_id, created_at (obligatoires)
- artist, event, tracklist (obligatoires)
- audio_fingerprint, signature, public_key (obligatoires)
- proof_level, rfc3161_token, bitcoin_anchor (optionnels)

## Contraintes respectées
- ✅ 100% client-side (aucun appel serveur)
- ✅ Aucune donnée collectée
- ✅ Aucun cookie
- ✅ Local-First
- ✅ Anti-Surveillance

## Test Results
- Frontend: 100%
- Navigation: 100%
- Verifier: 100%
- Mobile: 100%
- Animations: 100%

---

*FREK® — Preuve > Service | Local-First | Anti-Surveillance*
*© 2025–2026 CVLN Group — frekcore.com*

*Last updated: 2024-12-19*
