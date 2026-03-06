# FREK v2.0 - Product Requirements Document

## Project Overview
FREK® est un standard ouvert d'identification cryptographique des DJ mixes et performances musicales composites. Développé par CVLN Group (Bruxelles). Premier déploiement officiel : Culture Connect 2026, Fort-de-France, Martinique.

**Principe fondamental:** *"FREK ne reconnaît pas la musique. FREK reconnaît un fait technique, dans un contexte précis."*

## Architecture v2.0

```
/app/frontend/
├── index.html
├── vite.config.js
├── tailwind.config.js
├── netlify.toml
├── public/
│   └── favicon.svg
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── index.css
    ├── i18n/                       # 🆕 Internationalization
    │   ├── index.js
    │   └── locales/
    │       ├── fr.json
    │       ├── en.json
    │       ├── es.json
    │       └── ar.json
    ├── components/
    │   ├── layout/
    │   │   ├── Nav.jsx            # + LanguageSwitcher
    │   │   └── Footer.jsx
    │   ├── sections/
    │   │   ├── Hero.jsx
    │   │   ├── Philosophie.jsx
    │   │   ├── Architecture.jsx
    │   │   ├── Produits.jsx
    │   │   ├── Verifier.jsx       # + Export Report
    │   │   ├── Spec.jsx
    │   │   ├── FrekId.jsx
    │   │   ├── CultureConnect.jsx
    │   │   ├── Ecosysteme.jsx
    │   │   └── Roadmap.jsx
    │   ├── ui/
    │   │   ├── LanguageSwitcher.jsx  # 🆕
    │   │   ├── RevealWrapper.jsx
    │   │   ├── SectionTag.jsx
    │   │   ├── Divider.jsx
    │   │   └── JsonBlock.jsx
    │   └── wizard/
    │       ├── FrekJsonPreview.jsx
    │       ├── Step1Identity.jsx
    │       ├── Step2Tracklist.jsx
    │       ├── Step3Fingerprint.jsx
    │       ├── Step4Review.jsx       # + QR Code
    │       └── WizardStepper.jsx     # + ARIA
    ├── hooks/
    │   ├── useAudioFingerprint.js
    │   ├── useJsonVerify.js
    │   ├── useScrollReveal.js
    │   └── useWizardState.js
    ├── utils/
    │   ├── crypto.js
    │   ├── frek-generator.js
    │   ├── frek-id.js
    │   └── frek-schema.js
    ├── pages/
    │   └── Generate.jsx
    ├── data/
    │   ├── spec-fields.js
    │   ├── roadmap.js
    │   └── ecosystem.js
    └── test/                        # 🆕 Vitest tests
        ├── setup.js
        ├── vectors.js
        ├── frek-id.test.js
        ├── frek-generator.test.js
        └── useJsonVerify.test.js
```

## Design System

### Couleurs
- **terra:** `#C4714A` — Couleur principale
- **gold:** `#D4A84B` — Accents secondaires
- **dark:** `#080808` — Background principal
- **navy:** `#0D1B2A` — Sections alternées
- **fgreen:** `#1A4A2A` — Succès/Valide
- **light/mid/dim:** Niveaux de texte

### Typographie
- **Bebas Neue** — Titres
- **DM Mono** — Code, labels
- **DM Sans** — Corps de texte

## Implemented Features

### ✅ P0: Wizard Générateur d'Attestation (2025-03-06)
- [x] Navigation 4 étapes avec stepper
- [x] Formulaire artiste + événement avec validation
- [x] Tracklist CRUD avec réorganisation
- [x] Upload audio ou saisie manuelle SHA-256
- [x] Génération FREK-ID format FREK-YYYY-XX-NNN
- [x] Signature SHA-256 auto-calculée
- [x] Téléchargement fichier .frek.json
- [x] QR Code scannable (qrcode.react)
- [x] **5/5 tests du cahier des charges passés**

### ✅ P1: Tests de conformité Vitest (2025-03-06)
- [x] Suite de tests automatisés (45 tests)
- [x] Test vectors valides/invalides
- [x] Tests useJsonVerify (18 tests)
- [x] Tests frek-generator (16 tests)
- [x] Tests frek-id (11 tests)

### ✅ P2: Internationalisation i18n (2025-03-06)
- [x] Framework i18next + react-i18next
- [x] 4 langues: FR, EN, ES, AR
- [x] Détection automatique de langue
- [x] Sélecteur de langue dans navigation
- [x] Support RTL pour l'arabe

### ✅ P2: Accessibilité WCAG (2025-03-06)
- [x] Focus visible styles
- [x] ARIA labels et rôles
- [x] Keyboard navigation
- [x] Skip link
- [x] Reduced motion support
- [x] High contrast mode support

### ✅ P3: Export rapport Verifier (2025-03-06)
- [x] Bouton "Télécharger le rapport"
- [x] Export JSON pour fingerprint audio
- [x] Export JSON pour vérification attestation

## Test Results (2025-03-06)

```
✓ src/test/frek-id.test.js (11 tests)
✓ src/test/frek-generator.test.js (16 tests)
✓ src/test/useJsonVerify.test.js (18 tests)

Test Files  3 passed (3)
Tests       45 passed (45)
```

## Contraintes respectées
- ✅ 100% client-side
- ✅ Aucune donnée collectée
- ✅ Aucun cookie
- ✅ Local-First
- ✅ Anti-Surveillance
- ✅ WCAG 2.1 AA

## Deployment Notes
- **Preview URL:** Ne supporte pas les domaines personnalisés
- **Pour frekcore.com:** Déployer l'application (50 crédits/mois), puis Link domain → Entri

---

*FREK® — Preuve > Service | Local-First | Anti-Surveillance*
*© 2025–2026 CVLN Group — frekcore.com*

*Last updated: 2025-03-06*
