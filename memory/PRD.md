# FREK v0.4 — Product Requirements Document

## Original Problem Statement
Construire FREK v0.4: une infrastructure de preuve pour DJ mixes.
- Application web local-first avec documentation + démo de vérification
- Sans plateforme, sans tracking, sans cloud obligatoire
- Principes non négociables: pas de comptes, pas d'analytics, pas de réseau social

## Architecture

### Frontend (React + Tailwind)
- Pages: /, /docs, /architecture, /spec, /governance, /changelog, /verify
- Module de vérification: validation JSON (Zod), signature Ed25519 (tweetnacl)
- Tout fonctionne dans le navigateur, aucune donnée ne sort

### Backend (FastAPI - optionnel, désactivé par défaut)
- Non utilisé pour les fonctionnalités core
- Disponible pour extensions futures

## User Personas
1. **DJs professionnels** — Besoin de prouver l'authenticité de leurs mixes
2. **Développeurs d'outils audio** — Intégration du standard FREK
3. **Organismes de standardisation** — Référence technique

## Core Requirements (Implémenté)
- [x] Site FREK Standard (docs) public
- [x] Module FREK Verify (demo) local
- [x] Schéma JSON officiel (.frek.json) + validateurs Zod
- [x] README avec installation et limites
- [x] Changelog v0.4

## What's Been Implemented (Jan 2026)
1. Landing page sobre avec accès Docs/Verify
2. Manifeste complet (principes, philosophie)
3. Architecture pipeline (4 étapes visuelles)
4. Spécification .frek.json détaillée
5. Modèle de gouvernance anti-capture
6. Changelog avec roadmap v0.5
7. Module de vérification fonctionnel:
   - Validation JSON schema v0.4
   - Vérification signature Ed25519
   - Comparaison fingerprint (demo mode)
   - Export rapport JSON

## Prioritized Backlog

### P0 (Critical) - Done
- [x] Module verify fonctionnel
- [x] Validation signature Ed25519

### P1 (High)
- [ ] Fingerprint audio avancé (spectral analysis)
- [ ] SDK de référence (Python, JavaScript)
- [ ] Tests automatisés complets

### P2 (Medium)
- [ ] Mode offline PWA
- [ ] Extension navigateur
- [ ] Plugin VST/AU pour DAW

### P3 (Low)
- [ ] Intégration blockchain optionnelle
- [ ] API volontaire
- [ ] Multilingue (EN, ES, DE)

## Technical Constraints
- Local-first: tout doit fonctionner hors-ligne
- Pas de tracking/analytics
- Ed25519 pour signatures
- SHA-256 pour fingerprints
- JSON comme format d'échange

## Next Tasks
1. Améliorer le fingerprint audio (FFT réel au lieu de hash simple)
2. Ajouter tests unitaires pour crypto
3. Créer un générateur de fichiers .frek.json
4. Documentation CLI pour intégrations
