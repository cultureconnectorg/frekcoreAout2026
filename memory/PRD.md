# FREK v0.4 - Product Requirements Document

## Project Overview
FREK est un protocole ouvert de preuve-de-travail pour les mixes DJ. C'est une infrastructure cryptographique qui permet de certifier l'authenticité des performances musicales.

**Principe fondamental:** *"FREK ne reconnaît pas la musique. FREK reconnaît un fait technique, dans un contexte précis."*

## Architecture

```
/app/frontend/
├── public/
│   ├── logo.svg                    # Official FREK logo
│   └── examples/                   # Test vectors (.frek.json files)
├── src/
│   ├── core/
│   │   ├── frek-core.js           # Core verification module
│   │   └── frek-core.test.js      # Conformance tests
│   ├── components/
│   │   ├── Navigation.jsx         # Main nav with logo + language selector
│   │   ├── Footer.jsx             # Site footer
│   │   └── LanguageSelector.jsx   # Language dropdown (FR/EN/ES/AR)
│   ├── lib/
│   │   ├── i18n.js                # Translation strings (4 languages)
│   │   ├── LanguageContext.jsx    # React context for i18n + RTL
│   │   ├── crypto.js              # Cryptographic utilities
│   │   ├── frek-schema.js         # Zod schema validation
│   │   ├── domains.js             # Domain URL configuration
│   │   └── utils.js               # Helper functions
│   └── pages/
│       ├── PublicLanding.jsx      # Landing page
│       ├── PublicVerify.jsx       # Verification tool
│       ├── Standard.jsx           # Standard explanation
│       ├── Manifesto.jsx          # Vision & principles
│       ├── Industry.jsx           # Industry solutions
│       └── docs/                   # Developer portal
```

## Implemented Features

### ✅ Phase 1 - Foundations (COMPLETED 2024-12-19)

#### i18n System
- [x] 4 languages: French (primary), English, Spanish, Arabic
- [x] RTL support for Arabic with automatic `dir="rtl"` on document
- [x] Language persistence via localStorage (`frek-lang`)
- [x] LanguageProvider React context

#### Logo Integration
- [x] FREK logo (`/public/logo.svg`) - cyan F on black background
- [x] Logo in Navigation header
- [x] Logo in Footer

#### Accessibility
- [x] ARIA labels on navigation, buttons, language selector
- [x] Keyboard navigation support (`:focus-visible` states)
- [x] High contrast mode support
- [x] Screen reader compatible

### ✅ Phase 2 - Core Module (COMPLETED 2024-12-19)

#### frek-core.js Module
- [x] `canonicalize(metadata)` - Deterministic JSON canonicalization
- [x] `verifySignature(message, signature, publicKey)` - Ed25519 verification
- [x] `validateSchema(data)` - Zod-based FREK JSON validation
- [x] `hashAudio(audioBuffer, options)` - FFT-based audio fingerprinting
- [x] `sha256(data)` - SHA-256 hashing via Web Crypto API
- [x] `generateReport(results)` - Verification report generation
- [x] `verifyFrek(frekData, audioBuffer)` - Complete verification pipeline

#### Test Vectors
- [x] `valid-signed.frek.json` - Valid signed attestation
- [x] `invalid.frek.json` - Invalid schema
- [x] `invalid-signature.frek.json` - Valid structure, bad signature
- [x] `corrupted-metadata.frek.json` - Corrupted metadata fields
- [x] `demo-studio.frek.json` - Demo studio attestation

#### Conformance Tests
- [x] Schema validation tests
- [x] Canonicalization tests
- [x] Hashing tests (SHA-256 golden vectors)
- [x] Signature verification tests
- [x] Failure mode tests

### ✅ Phase 3 - Verification UX (COMPLETED 2024-12-19)

- [x] Drag & drop audio upload
- [x] Progress indicator with percentage
- [x] Clear status states (VERIFIED, MODIFIED, NOT VERIFIED, INCONCLUSIVE)
- [x] Export verification report as JSON
- [x] Developer mode toggle for FREK JSON uploads

### ✅ Audio Fingerprinting (COMPLETED 2024-12-19)

Implemented FFT-based fingerprinting:
1. Decode audio to PCM via Web Audio API
2. Downsample to mono 22050Hz
3. Apply windowed FFT analysis (2048-sample Hann window)
4. Extract 32 spectral band energies
5. Generate segment hashes (5-second windows)
6. Compute final fingerprint hash

## Remaining Tasks

### 🔶 P1 - Polish
- [ ] Add loading states/spinners during FFT computation
- [ ] Improve error messages for audio decode failures
- [ ] Add example audio file for demo

### 🔶 P2 - Enhancements
- [ ] Generate FREK attestation wizard (sign your own mixes)
- [ ] Visual fingerprint comparison (waveform/spectrogram view)
- [ ] Batch verification mode

### 🔶 P3 - Future
- [ ] Reference SDK (JS/Python/Rust)
- [ ] CLI tool for attestation generation
- [ ] Integration guides for DAWs (Ableton, Traktor)

## Technical Specifications

### FREK v0.4 JSON Schema
```json
{
  "frek_version": "0.4",
  "fingerprint": "sha256:<64 hex chars>",
  "segments": [{ "t0": 0, "t1": 5, "h": "sha256:..." }],
  "metadata": {
    "timestamp": "ISO 8601",
    "duration": 3600,
    "source_type": "live|studio|rehearsal|dispute"
  },
  "signature": "ed25519:<base64>",
  "public_key": "<base64>"
}
```

### Cryptographic Primitives
- **Hash:** SHA-256
- **Signature:** Ed25519
- **Fingerprint:** FFT spectral analysis + SHA-256

### Domain Configuration
- Public site: `frekcore.com`
- Developer portal: `{preview-url}/docs`
- Configured via `.env` variables

## Deployment Notes
- Local-first: No backend required for verification
- Offline-capable: All verification runs in browser
- Zero tracking: No analytics, no data collection
- Anti-surveillance: Proof without monitoring

---

*Last updated: 2024-12-19*
