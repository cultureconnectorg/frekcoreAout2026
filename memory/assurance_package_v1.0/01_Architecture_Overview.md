# 01 — Architecture Overview

**FREKCORE Assurance Package v1.0** — Document 01
**Version** : 1.0.0-rc
**Date** : 2026-07-08

---

## 1. Vue en une phrase

**FREKCORE = infrastructure de preuve culturelle souveraine, notarisée sur Bitcoin, vérifiable offline.**

Un notaire technique invisible : chaque événement culturel (billet, scan, stream, vote, présence) devient un objet cryptographique nominatif à vie, exportable, et vérifiable par n'importe quel tiers **sans dépendre de FREKCORE**.

---

## 2. Diagramme d'architecture

```
                ┌──────────────────────────────────────────────┐
                │            UTILISATEURS FINAUX               │
                │  (porteurs, opérateurs, tiers vérificateurs) │
                └──────────────────┬───────────────────────────┘
                                   │ HTTPS
                                   ↓
                ┌──────────────────────────────────────────────┐
                │              FRONTEND (React)                │
                │  /accueil /profil /scan /verify /explorer    │
                └──────────────────┬───────────────────────────┘
                                   │ REST /api/*
                                   ↓
        ┌──────────────────────────────────────────────────────┐
        │                    BACKEND FastAPI                    │
        │    24 modules — 201 endpoints — Python 3.11           │
        │                                                       │
        │   ┌──────────┐  ┌──────────┐  ┌──────────┐            │
        │   │ Identité │  │  Notary  │  │ Passport │            │
        │   │ (Luciole)│  │ (chain)  │  │  Ed25519 │            │
        │   └──────────┘  └──────────┘  └──────────┘            │
        │                                                       │
        │   ┌──────────┐  ┌──────────┐  ┌──────────┐            │
        │   │Fingerprnt│  │   Geo    │  │ Heritage │            │
        │   │ 7 couches│  │ H3+PlusC │  │ Trans-   │            │
        │   └──────────┘  └──────────┘  │ mission  │            │
        │                               └──────────┘            │
        │                                                       │
        │   ┌──────────┐  ┌──────────┐  ┌──────────┐            │
        │   │  Staff   │  │  Badges  │  │  Jetons  │            │
        │   │   PWA    │  │ 14 types │  │  wallet  │            │
        │   └──────────┘  └──────────┘  └──────────┘            │
        └────┬──────────────────┬──────────────────┬───────────┘
             │                  │                  │
             ↓                  ↓                  ↓
     ┌────────────┐     ┌──────────────┐   ┌──────────────┐
     │  MongoDB   │     │ OpenTimestamp│   │   Backup     │
     │   local    │     │  calendars   │   │  daemon      │
     │ (SoT état) │     │ 5 publics    │   │ 03:00 UTC    │
     └────────────┘     └──────┬───────┘   └──────────────┘
                               │
                               ↓
                        ┌─────────────┐
                        │   Bitcoin   │
                        │  blockchain │
                        │  (ancre     │
                        │  définitive)│
                        └─────────────┘
```

---

## 3. Composants principaux

### 3.1 Frontend
- **Stack** : React 18 + Vite + Tailwind + Framer Motion
- **PWA** installable (`/scan`, manifest + service worker + queue IndexedDB)
- **22 pages** publiques (porteur, opérateur, transparency, admin)
- **Théme** : light blanc/bleu dégradé, glassmorphism

### 3.2 Backend
- **Stack** : FastAPI (Python 3.11) + Motor async MongoDB
- **24 modules** distincts, 201 endpoints REST prefixés `/api/*`
- **Router principal** : `/app/backend/server.py`
- **Modules critiques** :
  - `frek_v1/` — protocole identité Luciole (GENESIS → LEGACY)
  - `notary/` — FREK-Chain locale + OpenTimestamps + Bitcoin RPC dual-source
  - `passport/` — Ed25519 + Merkle + verifier standalone
  - `did/` + `eudi/` — W3C DID Core + EUDI Wallet + VC data model 2.0
  - `staff/` — PWA scanner + bcrypt + zones
  - `sync/` — Baserow bi-directional
  - `heritage/` — transmission de FREK-ID (chain of custody)
  - `health/` — probes K8s + admin backup ops

### 3.3 Stockage & backup
- **MongoDB** local (test_database), 30+ collections
- **Backup automatique** quotidien 03:00 UTC via daemon supervisor `frek_backup`
- **Chiffrement GPG AES256** obligatoire (passphrase root-only `/root/.frekcore/backup_passphrase`)
- **Rétention** 30 jours
- **Restore-test** endpoint API `/admin/backup/restore-test/{archive}`

### 3.4 Notarisation
- **FREK-Chain locale** : chaîne SHA-256 chainée (prev_hash / block_hash), 1311 blocks
- **OpenTimestamps** : soumission automatique via loop background (30s)
- **Bitcoin anchor** : upgrade via calendars publics (30 min), 1291 blocks BTC-confirmés sur 1409 anchored
- **Sources d'ancrage double** : calendars OTS publics + option nœud Bitcoin RPC (fallback)

### 3.5 Cryptographie
- **Clé Ed25519** unique (`/app/backend/.passport_key.pem`, chmod 0600)
- **SHA-256** partout (block chain, Merkle passport, hash email)
- **JCS RFC 8785** (canonicalization pour VC eddsa-jcs-2022)
- **Multibase base58btc + multicodec 0xed01** (Multikey W3C)

### 3.6 Standards implémentés
- W3C DID Core 1.0 ✅
- W3C Verifiable Credentials Data Model 2.0 ✅
- EUDI Wallet OID4VCI Draft 13+ ✅
- SD-JWT VC IETF draft-08+ ✅
- RFC 7517 JSON Web Key ✅
- DIF DID-Configuration v1 ✅
- ISO mDL preparation ✅
- ID4Africa / CARICOM Single ICT Space ✅

### 3.7 Ops & résilience
- **Supervisor** : backend + frontend + mongodb + frek_backup + frek_chain_watchdog
- **Chain watchdog** : vérif intégrité toutes les 6h, écrit `security_events`
- **Motor timeout** : fail-fast 3s (au lieu de 30s hang) sur Mongo indisponible
- **Health probes** : `/api/v1/health/{live,ready,deep}` (K8s + monitoring compatible)

---

## 4. Doctrine architecturale

### 4.1 Racine de confiance unique
Une seule clé Ed25519 signe tous les passeports FREK. La sécurité de tout le système repose sur la préservation de cette clé (backupée GPG hors code).

### 4.2 Souveraineté verticale
- **FREKCORE** = protocole central, autorité de référence.
- **Clients (Kiltikonet, partenaires B2B)** = utilisateurs de l'infrastructure, pas opérateurs de leur propre notariat.
- **Aucune fédération** : pas de sous-chaîne par client, pas de clé par client. Racine unique.

### 4.3 Verification offline garantie
- Verifier Python (`verify_passport.py`) — 0 dépendance réseau
- Verifier JS (`verify_passport.js`) — Web Crypto API standalone
- Clé publique exposée sur 3 canaux : `/api/v1/passport/key`, `/.well-known/jwks.json`, `/api/v1/did/frekcore`
- Preuve OTS `.ots` file — vérifiable via `opentimestamps` PyPI standard

### 4.4 Compteur universel
Tout flux culturel (billet, scan, stream, vote, présence passive) alimente `/api/core/count` → notarisation batch → block FREK-Chain → ancre BTC.

### 4.5 Séparation crypto / opérationnel
- **FREK-Chain (Bitcoin-anchored)** = source de vérité cryptographique.
- **Baserow** (via module `sync/`) = couche opérationnelle CRM, bi-directionnelle.
- **Kiltikonet (externe)** = couche business, gestion des JCC (jamais Stripe direct porteur).

---

## 5. Chiffres vivants (au freeze RC v1.0)

| Métrique | Valeur |
|---|---|
| Endpoints REST | 201 |
| Modules backend | 24 |
| Pages frontend | 22 |
| FREK-IDs actifs | 1197 |
| Blocks FREK-Chain | 1311 (integrity ok) |
| Anchored total | 1496 (1291 BTC-confirmés) |
| Calendars OTS | 5 publics indépendants |
| Collections Mongo | 30+ |
| Daemons supervisor | 5 (backend, frontend, mongodb, frek_backup, frek_chain_watchdog) |

---

## 6. Dépendances externes

| Dépendance | Rôle | Statut si down |
|---|---|---|
| MongoDB | Source of Truth état | Backend fail-fast 3s, /health/ready = 503 |
| OpenTimestamps calendars (5) | Ancrage BTC | Chain locale continue, queue accumule, reprise auto |
| Bitcoin blockchain | Datation universelle | Aucun impact court terme (déjà ancré) |
| Baserow | CRM opérationnel | Sync module en queue, aucun impact FREKCORE core |

**Aucune dépendance n'est critique pour la création de preuves FREK.** Toutes sont uniquement liées à la publication vers le monde extérieur.

---

## 7. Points d'entrée pour un nouvel intégrateur

- **Spec publique** : `GET /api/v1/spec/` (versionnée v1.0.0)
- **JWKS** : `GET /.well-known/jwks.json` (RFC 7517)
- **DID Configuration** : `GET /.well-known/did-configuration.json` (DIF v1)
- **Documentation OpenAPI** : `GET /docs` (Swagger auto-généré)
- **Verifier Python** : `GET /api/v1/passport/verifier/python`
- **Verifier JS** : `GET /api/v1/passport/verifier/js`

---

## 8. Ce document répond à

- *Comment FREKCORE est-il structuré ?* → §3 composants
- *Sur quoi repose la sécurité ?* → §4.1 + doc 02 Security Model
- *Quelles dépendances externes ?* → §6
- *Comment un dev externe s'intègre ?* → §7
