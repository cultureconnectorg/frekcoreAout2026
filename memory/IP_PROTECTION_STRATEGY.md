> ⚠️ **CONFIDENTIAL — FREKCORE Internal**
> Distribution restricted. NDA required for external sharing.
> Ce document appartient au niveau Vault (Level 3) de la doctrine IP FREKCORE.

---


# FREKCORE — IP Protection Strategy v1.0

**Date** : 2026-07-08
**Statut** : Doctrine active
**Objet** : gouverner la surface d'exposition de FREKCORE selon 3 niveaux étanches.

---

## Doctrine

> **Montrer la preuve. Cacher la recette.**

Une infrastructure de confiance doit laisser voir assez pour être crédible, sans exposer ce qui permettrait de la répliquer.

## Les 3 niveaux

### 🌍 Niveau 1 — Public

**Objectif** : confiance + compréhension

**Contient** :
- Philosophie et manifeste
- Charte de confiance (5 principes)
- Cas d'usage narrés
- Preuves ponctuelles vérifiables
- Le geste principal (`/`)

**Ne contient PAS** :
- Architecture technique détaillée
- Modèles cryptographiques précis
- Composants internes
- Roadmap
- Métriques opérationnelles brutes

**Routes publiques autorisées** :
- `/` (Signer)
- `/manifeste`, `/philosophy`
- `/mine` (session anonyme locale)
- `/verify/:frek_id` (page publique de vérification)
- `/proof/:hash` (page publique preuve individuelle)
- `/spec` (Charte de confiance uniquement — pas de doc ingénierie)
- `/explorer` (exemples d'usages, pas raw blocks)
- `/api/v1/passport/key` (clé publique — nécessaire pour vérification)
- `/api/.well-known/jwks.json` (standard universel)
- `/api/v1/moment/*` (fenêtre publique #1)

---

### 🤝 Niveau 2 — Partenaire (sous NDA)

**Objectif** : intégration + due diligence

**Contient** :
- Fonctionnement général (sans recette)
- Garanties contractuelles
- Documentation API (endpoints, schémas)
- Modèle d'intégration
- Politique sécurité
- Rapports audit E/F/G (résumés)

**Accès** : header `X-NDA-Key` (émis contre signature NDA)

**Routes prévues (à implémenter)** :
- `/api/v1/spec/full` (full spec versionnée) — X-NDA-Key
- `/api/v1/partners/reports/{sprint}` (rapports audit) — X-NDA-Key

---

### 🔒 Niveau 3 — Vault interne

**Objectif** : opérationnel + IP

**Contient** :
- Architecture complète (module par module)
- Runbooks opérationnels
- Détails cryptographiques (choix, arbitrages)
- Décisions d'architecture historiques
- Roadmap technique complète
- Assurance Package v1.0 (10 documents)
- SOVEREIGNTY_AUDIT, PERFORMANCE_REPORT, RESILIENCE_REPORT
- BUSINESS_MODEL, RUNBOOK

**Accès** : jamais public. Uniquement disque conteneur, backup GPG, password manager.

**Localisation** :
- `/app/memory/` (docs internes)
- `/app/backend/` (code source)
- `/root/.frekcore/` (secrets opérationnels)

---

## Application au codebase actuel

### ✅ Déjà conforme
- `/docs`, `/openapi.json`, `/redoc` fermés en production (flag `FREK_PUBLIC_DOCS=false` par défaut).
- Endpoints admin (`/admin/backup/*`, `/admin/security/*`, `/admin/clients/*`, `/sync/*`) protégés `X-Admin-Key`.
- Endpoints staff (`/staff/*`) protégés PIN bcrypt + JWT.
- Endpoints client B2B (`/identity/emit`, etc.) protégés OAuth2 client_credentials.
- Docs internes `/app/memory/` non exposées via HTTP.

### 🟠 À faire (Phase 2)
1. **`/spec` réécrit** en Charte de confiance (5 principes narratifs, aucune ingénierie).
2. **`/api/v1/spec/`** retourne la Charte uniquement.
3. **`/api/v1/spec/full`** créé, protégé par `X-NDA-Key`.
4. **`/explorer`** réécrit en "exemples d'usages" (compteur + cas anonymisés).
5. **`/admin/explorer`** créé pour la vue raw technique (X-Admin-Key).
6. **Banner CONFIDENTIAL** en tête de chaque `.md` dans `/app/memory/`.

### 🟢 À ne PAS faire
- Ne pas retirer `/verifier/python` et `/verifier/js` : la souveraineté vérificationnelle passe par leur disponibilité publique. C'est un actif de confiance, pas une fuite.
- Ne pas fermer `/api/v1/passport/key` ni `/.well-known/jwks.json` : standards universels, nécessaires à toute vérification tierce.
- Ne pas retirer `/proof/:hash` : chaque preuve individuelle doit être vérifiable par n'importe qui.

---

## Formulation type pour chaque niveau

### Public
> "FREKCORE transforme un moment en preuve durable et vérifiable."

### Partenaire NDA
> "FREKCORE repose sur une infrastructure d'attestation cryptographique indépendante, ancrée sur des calendars publics et vérifiable offline sans dépendance à notre service."

### Interne
> Ed25519 + Merkle SHA-256 + JCS canonicalization + OpenTimestamps + Bitcoin RPC dual-source + chain integrity watchdog 6h.

---

## Gouvernance

- **Chaque nouvelle page frontend** doit préciser explicitement son niveau (Public / NDA / Vault) en commentaire d'en-tête.
- **Chaque nouveau endpoint API** doit préciser son niveau d'accès.
- **Tout doc dans `/app/memory/`** est présumé Vault sauf mention contraire.
- **Toute publication externe** (blog, X, LinkedIn, presse) doit passer par le filtre du niveau Public.

---

## Formule décisionnelle

Avant de publier, exposer, ou communiquer un élément, poser 3 questions :

1. **Cet élément aide-t-il à créer la confiance ?**
   - Oui → considérer Public.
   - Non → passer à Q2.

2. **Cet élément est-il nécessaire à une intégration ou une due diligence ?**
   - Oui → Partenaire NDA.
   - Non → passer à Q3.

3. **Cet élément révèle-t-il la recette ou l'arbitrage architectural ?**
   - Oui → Vault interne.
   - Non → probablement à supprimer entièrement.

---

## Auto-hash

**SHA-256** : à calculer via `sha256sum IP_PROTECTION_STRATEGY.md` — cette stratégie elle-même est un document du Vault.
