> ⚠️ **CONFIDENTIAL — FREKCORE Internal**
> Distribution restricted. NDA required for external sharing.
> Ce document appartient au niveau Vault (Level 3) de la doctrine IP FREKCORE.

---


# FREKCORE Reliability Report v1.0

**Statut** : Release Candidate — 3 des 5 axes fermés
**Date freeze** : 2026-07-08
**Version FREKCORE** : 1.0.0-rc
**Baseline chain** : height=1311, integrity ok, notary_blocks=1311

---

## 1. Objet

Ce document est le **chapeau consolidé** de la campagne d'audit FREKCORE v1.0.
Il ne contient pas de nouveaux résultats — il **fige les 3 audits déjà menés** et
définit les 2 audits restants pour la Release Candidate publique.

Chaque audit référencé est un rapport autonome, auto-hashé, reproductible.

---

## 2. Doctrine testée

> FREKCORE est une infrastructure de preuve culturelle souveraine, centrale,
> avec racine de confiance unique, dont les propriétés doivent être vérifiables
> selon 5 dimensions indépendantes.

Chaque dimension = un audit séparé. Aucun ne peut compenser un autre.

| Axe | Question fermée | Métrique clé |
|---|---|---|
| **E — Existence** | Est-ce réel cryptographiquement ? | Vérification offline sans FREKCORE |
| **F — Performance** | Est-ce réel à l'échelle ? | RPS + p95 + saturation |
| **G — Resilience** | Est-ce réel en dégradé ? | MTTR + intégrité post-crash |
| **H — Terrain** | Est-ce réel avec des humains ? | Taux de succès + temps moyen |
| **I — Économie** | Est-ce réel économiquement ? | Coût / preuve + revenus / usage |

---

## 3. Audits fermés

### 3.1 Sprint E — Proof of Existence ✅

**Rapport** : `/app/memory/SOVEREIGNTY_AUDIT.md`
**SHA-256** : `2694d9ded85f74c89b7c01b92126dd9dbf340f71525fe588e9ba7260ff1ad135`
**Date** : 2026-07-08

**Résultat** : Un tiers, avec les artefacts + verifier standalone + clé publique + preuve OTS, peut valider un événement culturel FREK **sans jamais contacter FREKCORE.io**. 4 dimensions cryptographiques validées offline : Ed25519, Merkle SHA-256, DID W3C Multikey, VC eddsa-jcs-2022, OpenTimestamps.

**Verdict** : ✅ FREKCORE tient sa promesse de "notaire culturel tech" **au niveau du protocole**.

### 3.2 Sprint F — Performance Audit ✅

**Rapport** : `/app/memory/PERFORMANCE_REPORT_v1.0.md`
**SHA-256** : `ebd89a8c7a9c169b2e10cfef979759bb1f20c9ef75e177442758b9acdc2737d1`
**Date** : 2026-07-08

**Résultat** : Sur single-worker (config actuelle), 216 RPS lecture pure sans erreur, p95=160ms, p99=340ms. 2 goulots identifiés (par ordre d'apparition) : rate-limit émission (protection Phase 2.5, par design), et bcrypt login-surge (100 logins simultanés → 20s de file).

**Verdict** : ✅ FREKCORE peut tenir CC2026 J-0 **sous 3 conditions opérationnelles** : plusieurs clients API émetteurs, staff staggered T-30min, Uvicorn multi-worker en prod.

### 3.3 Sprint G — Resilience Audit ✅

**Rapport** : `/app/memory/RESILIENCE_REPORT_v1.0.md`
**SHA-256** : `7c3ec9d6c1815250e3efcc0093e7d4e0f9f633db4ade7d94bdac945a7911695f`
**Date** : 2026-07-08

**Résultat** : 3 tests chaos — coupure Mongo, coupure OTS, corruption block volontaire — tous **PASS**. Chain integrity préservée dans les 3 scénarios. Souveraineté locale confirmée (notarisation continue de fonctionner sans OTS). Corruption détectée immédiatement avec localisation précise (block #654 identifié en 200ms).

**Verdict** : ✅ FREKCORE reste **lisible, sûr et récupérable** face aux 3 pannes courantes. 4 P1 fixes identifiés (à appliquer après ce freeze).

---

## 4. Audits restants

### 4.1 Sprint H — Terrain (Field Audit)

**Question** : Un humain peut-il utiliser FREKCORE dans le monde réel ?

**Approche recommandée par le fondateur** :

**H1 — Laboratoire** (5 personnes, 1 session courte)
- 1 organisateur
- 2 opérateurs (staff PWA)
- 2 utilisateurs finaux (porteurs)

Parcours mesurés :
1. Création FREK-ID
2. Scan badge / QR
3. Validation d'accès
4. Récupération et vérification de la preuve (passport)

Métriques :
- Temps moyen par parcours
- Nombre d'erreurs humaines
- Points de blocage UX
- Compréhension par un utilisateur non-formé

**H2 — Pilote** (50-100 utilisateurs, 1 événement contrôlé)
- Extension progressive après H1
- Instrumentation temps réel via `/api/v1/dashboard/cc2026/live`
- Rapport incidents

**Livrable attendu** : `FIELD_REPORT_v1.0.md` + `FIELD_CHECKLIST.md` (protocole opérationnel).

### 4.2 Sprint I — Business viability

**Question** : Quelqu'un a-t-il une raison économique d'utiliser FREKCORE ?

**Pas besoin de grosse traction — juste prouver les fondamentaux** :
1. Qui paie ?
2. Pour quel service ?
3. Combien coûte techniquement une preuve (infrastructure marginale) ?
4. Combien rapporte un usage (facturation JCC, contrat B2B, licence) ?

**Exemple à modéliser** :
- 1 organisation culturelle = 10 000 participants
- X FREK-ID émis (avec ou sans passeport signé)
- Coût infra marginal (Mongo + OTS + hosting)
- Prix facturé partenaire
- Marge brute

**Livrable attendu** : `BUSINESS_MODEL_v1.0.md` + endpoints de metering (`/api/v1/admin/metering/{client_id}`).

---

## 5. Progression Reliability Report v1.0

```
[E] Proof of Existence   ✅  hash 2694d9de...
[F] Performance          ✅  hash ebd89a8c...
[G] Resilience           ✅  hash 7c3ec9d6...
[H] Terrain              ⏭️  attend action fondateur
[I] Business viability   ⏭️  après H
```

**3/5 audits fermés**. FREKCORE est **cryptographiquement souverain** (E), **capable en régime nominal** (F), et **résilient face aux pannes courantes** (G).

**Encore à démontrer** : la réalité humaine (H) et la viabilité économique (I).

---

## 6. Position stratégique atteinte

Aujourd'hui, FREKCORE peut être présenté à :

- **Un régulateur / notariat** → montrer E + G (souveraineté + résilience)
- **Un investisseur due diligence** → montrer E + F + G (technique complète)
- **Un partenaire institutionnel** → nécessite H + I en complément (usage + économie)
- **Un utilisateur grand public** → nécessite H (UX validée)

Le triptyque E+F+G est **suffisant pour convaincre un audit technique**.
H+I sont nécessaires pour un **lancement commercial**.

---

## 7. Actions immédiates recommandées

Dans l'ordre proposé par le fondateur :

1. ✅ **Ce document — freeze RC v1.0** (fait à l'instant)
2. ✅ **4 P1 Sprint G corriges** (fait le 2026-07-08 12:10 UTC) :
   - ✅ Motor `serverSelectionTimeoutMS=3000` (server.py) — verifie : `/pulse` fail-fast en 3.2s au lieu de 30s
   - ✅ `/health/deep` catch timeouts Mongo — retourne HTTP 200 avec `status: degraded, mongo.ok: false`
   - ✅ Endpoints `POST /notary/anchor/sweep` et `/anchor/upgrade` deja presents (auth client emit)
   - ✅ `chain_watchdog.py` daemon supervise (`frek_chain_watchdog`), verifie toutes les 6h, ecrit `security_events`
3. 🟠 **Sprint H1 — Labo 5 personnes** (action fondateur + instrumentation code)
4. 🟠 **Sprint I — Modèle économique** (analyse + endpoints metering)

---

## 8. Preuves de reproductibilité

Chaque audit peut être re-exécuté à partir de scripts versionnés :

```bash
# Sprint E — Proof of Existence
/app/scripts/proof_of_existence.sh

# Sprint F — Performance
FREK_API=http://localhost:8001 locust -f /app/scripts/loadtest/locust_read.py \
  --headless -u 500 -r 50 -t 120s --csv=/tmp/read

# Sprint G — Resilience
/app/scripts/chaos/test_block_corruption.sh
/app/scripts/chaos/test_ots_cut.sh
/app/scripts/chaos/test_mongo_cut.sh
```

Toutes les données brutes sont conservées dans `/app/loadtest_results/`.

---

## 9. Baseline immuable au freeze

- MongoDB : test_database v7.0.37
- FREK-Chain height : **1311**
- Notary blocks : 1311 (integrity ok)
- Anchored : 1496 (dont 1291 BTC-confirmés)
- FREK-IDs actifs : 1197
- Clé Ed25519 : sha256 `496a69437acd86d5dcc42f79c59fa951786c47ad8fb84e21b9028fd28f6e9088`
- Backup GPG : présent (`/app/backups/frekcore-2026-07-08T*.tar.gz.gpg`)

**Cette baseline est le point de référence pour tous les audits ultérieurs.**
Toute divergence future doit être justifiée par une transition documentée
(nouveau block, rotation de clé, migration, etc.).

---

**SHA-256 auto-hash chapeau** : `f3b2da828f026be6dab28b881e7128453599a8d8ee5f03639be0ad366c7bbf32`
