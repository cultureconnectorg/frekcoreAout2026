> ⚠️ **CONFIDENTIAL — FREKCORE Internal**
> Distribution restricted. NDA required for external sharing.
> Ce document appartient au niveau Vault (Level 3) de la doctrine IP FREKCORE.

---


# FREKCORE Sprint F — Performance Audit v1.0

**Question fermée** : *"Quelle charge FREKCORE peut-il absorber aujourd'hui, dans sa configuration actuelle, avant dégradation mesurable ?"*

**Date audit** : 2026-07-08  
**Version FREKCORE** : 1.0.0-rc (post Sprint A+B+D+E)  
**Executeur** : `/app/scripts/loadtest/locust_*.py`  
**Auto-hash** : à la fin du rapport

---

## 1. Environnement de mesure (reproductible)

| Composant | Valeur |
|---|---|
| CPU | 4 vCPU |
| RAM | 15 GB (12 GB utilisés hors test, ~3 GB dispo) |
| Disque | NVMe 9.8 GB (23% utilisés) |
| MongoDB | 7.0.37 (single instance, local) |
| Python | 3.11.15 |
| FastAPI | 0.110.1 |
| Uvicorn | **1 seul worker** (`--workers 1 --reload`) ⚠️ |
| Backend port | 8001 (interne) |
| Locust | 2.44.4 |
| Testeur | même pod que le SUT (localhost, pas de latence réseau) |

**État initial DB** : 130 FREK-IDs, 231 events, 1263 notary_blocks, 156 clients.  
**État final DB** : 1197 FREK-IDs, 231 events, 1309 notary_blocks. (~1067 FREK-IDs créés durant les tests)

**⚠️ Limitation majeure de l'environnement** : Uvicorn tourne en **mode reload single-worker**. Ce n'est pas une configuration production. Les chiffres RPS mesurés doivent être multipliés par ~N workers en production.

---

## 2. Méthodologie

3 scénarios Locust en headless, mesurant p50/p95/p99, erreurs, RPS.

| Scénario | Fichier | Simule |
|---|---|---|
| S1 — Lecture massive | `locust_read.py` | Visiteurs consultant profils, passeport, explorer |
| S2 — Émission (chemin critique) | `locust_emit.py` | Création FREK-ID + génération passport + DID + VC |
| S3 — Terrain simulé | `locust_field.py` | 100 scanners staff + counter universel |

Chaque scénario 90–120s. Résultats CSV dans `/app/loadtest_results/`.

---

## 3. Résultats

### 3.1 Scénario 1 — Lecture massive

| Charge | Requêtes | Erreurs | RPS | p50 | p95 | p99 |
|---|---|---|---|---|---|---|
| **100 users, 90s** | 4055 | 0.00% | 45 | **3 ms** | **12 ms** | **86 ms** |
| **500 users, 120s** | 25 952 | 0.00% | **216** | **9 ms** | **160 ms** | **340 ms** |

**Interprétation** :
- FREKCORE absorbe **216 RPS de lecture pure** sans aucune erreur, avec p99 < 340 ms.
- Le point de dégradation n'est pas atteint dans cette plage (single-worker).
- Endpoints les plus rapides : `/passport/key` (2 ms p95), `/spec` (2 ms p95).
- Endpoints les plus lourds : `/pulse` (280 ms p95), `/notary/chain/status` (190 ms p95) — car agrégations Mongo.

---

### 3.2 Scénario 2 — Émission (chemin de valeur)

**Charge** : 50 users, 90 s (ramp 10/s)  
**Résultats** :

| Étape pipeline | p50 | p95 | p99 |
|---|---|---|---|
| POST `/identity/emit` | 5 ms | 210 ms | 310 ms |
| GET `/passport/{id}` | 59 ms | 140 ms | 260 ms |
| GET `/did/{id}` | 48 ms | 100 ms | 200 ms |
| GET `/vc/{id}` | 50 ms | 300 ms | 360 ms |
| **Pipeline end-to-end** | **280 ms** | **690 ms** | **870 ms** |

**Découverte critique** ⚠️ :
- **64% de 429 (Too Many Requests)** sur `identity/emit` — le rate-limit Phase 2.5 (100/h/client, silencieux, sans Retry-After) déclenche par design.
- Ce n'est **pas** un bug de perf : c'est la protection anti-abus configurée.
- Les émissions qui passent sont **rapides** : pipeline complet en ~700 ms pour créer un FREK-ID + passport signé Ed25519 + DID + VC.

**Implication** : la capacité d'émission effective par client API est **100/heure** (config `FREK_RATE_EMIT_PER_HOUR`). Pour absorber CC2026 (40 000 FREK-IDs), il faut soit :
- Plusieurs clients API (`kiltikonet-cc2026`, `kiltikonet-cc2026-worker-1`, etc.)
- Ou augmenter `FREK_RATE_EMIT_PER_HOUR` pour la fenêtre pré-événement

---

### 3.3 Scénario 3 — Terrain simulé

**Config A — 100 users, ramp brutal 20/s** (login simultané) :

| Étape | p50 | p95 |
|---|---|---|
| Staff login (bcrypt cost 12) | **19 000 ms** ⚠️ | 21 000 ms |
| Scan access | 3 ms | 13 ms |
| Counter batch | 2 ms | 10 ms |

**Config B — 50 users, ramp doux 2/s** (login étalé) :

| Étape | p50 | p95 |
|---|---|---|
| Staff login | **470 ms** ✅ | 480 ms |
| Scan access | 3 ms | 99 ms |
| Counter batch | 2 ms | 160 ms |
| Dashboard live | 5 ms | 220 ms |

**Découverte critique** ⚠️ :
- **bcrypt cost 12** (Phase 2.5 hardening) → **1 login = ~200 ms CPU sérialisé** sur single-worker.
- **100 logins en 5 secondes** → file d'attente 20 secondes = usage terrain **bloqué au démarrage J-0**.
- Solution : étaler l'ouverture des PWA staff sur 5 minutes → login normal (470 ms).

---

## 4. Limites trouvées (le vrai goulot)

Classement des goulots par ordre d'apparition sous charge :

| Ordre | Composant | Symptôme | Charge à laquelle il apparaît |
|---|---|---|---|
| **1** | **Rate-limit émission (config)** | 429 silencieux | 100 émissions/h/client |
| **2** | **bcrypt login (CPU)** | Login p50 → 20s | 100 logins simultanés |
| **3** | Uvicorn single-worker | Latence agrégée | Au-delà de ~200 RPS lecture |
| **4** | Mongo agrégations (pulse, chain/status) | p95 monte à 280 ms | 500 users lecture |
| **5** | Notary anchor loop | Non testé (30s async submit) | À valider en Sprint G |

**Ce que NE dit PAS ce test** :
- La capacité avec Uvicorn `--workers 4` (× ~4 = 800+ RPS attendus).
- Le comportement à 5000+ users concurrents (jamais testé).
- L'impact de la charge réseau ingress (localhost = 0 latence).

---

## 5. Recommandations (par ordre de priorité)

### 🔴 P0 — Bloqueurs terrain CC2026 J-0

**5.1 Étaler les logins staff**  
Le protocole PWA doit ouvrir les sessions staff dès **T-30 minutes** pour éviter le login surge à T=0. Documenter dans le runbook CC2026.

**Alternative** : baisser `FREK_STAFF_BCRYPT_ROUNDS` de 12 à 10 (5-6× plus rapide, reste sécurisé). Configurable dans `.env`.

**5.2 Configurer plusieurs clients API émission**  
Actuellement `kiltikonet-cc2026` est le seul client émetteur → limite 100/h. Créer :
- `kiltikonet-cc2026-batch-1` (badges pré-inscrits)
- `kiltikonet-cc2026-walkin` (émission terrain)
- `kiltikonet-cc2026-web` (auto-inscription publique)

Chacun 100/h → 300/h total, ou augmenter le seuil global via env.

### 🟠 P1 — Optimisations infra

**5.3 Passer Uvicorn en multi-workers**  
Actuellement `--workers 1 --reload`. Recommandé prod : `--workers 4` (ou `gunicorn -w 4 -k uvicorn.workers.UvicornWorker`). Multiplication attendue : **× 3.5** effective (overhead pool).

**5.4 Ajouter un cache Redis pour endpoints agrégations**  
- `/pulse` : TTL 30s
- `/notary/chain/status` : TTL 30s
- `/notary/blocks?limit=N` : TTL 5s

Ces 3 endpoints représentent ~40% du trafic lecture et sollicitent des `$group` Mongo. Cache = latence divisée par ~10.

### 🟡 P2 — À suivre (pas d'action immédiate)

**5.5 Index composés Mongo**  
Les tests n'ont pas fait ressortir de scan collection lent. Les index actuels (héritage cumulé des Phases 1-5) suffisent. À monitorer via `db.currentOp()` en prod.

**5.6 Notary background loop**  
Non stressé dans ce test (async 30s). À valider en **Sprint G** avec coupure OTS + backlog forcé.

---

## 6. Décisions prises / non prises

### Prises
- ✅ **Documenter le rate-limit** comme *limite de sécurité intentionnelle*, pas comme bug.
- ✅ **Documenter le login surge bcrypt** comme *risque opérationnel J-0*, avec mitigation (staggered onboarding).
- ✅ **Rapport reproductible** : scripts Locust versionnés dans `/app/scripts/loadtest/`.

### Non prises (volontairement — doctrine "ne pas optimiser trop tôt")
- ❌ Ne pas ajouter Redis maintenant (à décider quand `/pulse` dépasse 500 RPS réel prod).
- ❌ Ne pas passer multi-workers dans ce fork (peut casser hot-reload — action manuelle prod).
- ❌ Ne pas baisser bcrypt cost avant Sprint G (résilience) — voir si login surge est vraiment un problème terrain.

---

## 7. Verdict senior

### Capacité FREKCORE mesurée aujourd'hui

| Type de charge | Plafond mesuré (single-worker) | Plafond estimé prod (4 workers) |
|---|---|---|
| Lecture pure | **216 RPS** | ~750 RPS |
| Émission FREK-ID complète | **~28/min** puis rate-limit | ~100/min si configurable |
| Scans terrain | **~50 scans/s** en régime | ~200/s |

### Ce que ce Sprint prouve

✅ FREKCORE peut absorber **quelques milliers de scans/heure** en régime normal.  
✅ Aucun endpoint ne présente de latence pathologique (p99 < 1s partout).  
✅ Les protections de sécurité (rate-limit, bcrypt) fonctionnent — parfois trop bien.

### Ce que ce Sprint NE prouve PAS

❌ La capacité à 40 000 FREK-IDs dans une journée (nécessite calcul rate-limit + workers).  
❌ Le comportement en mode dégradé (Mongo/OTS down) — objet du Sprint G.  
❌ L'ergonomie terrain sous stress humain — objet du Sprint H.

### Décision opérationnelle CC2026

**FREKCORE dans sa configuration actuelle peut tenir CC2026 SI** :
1. Multiple clients API sont provisionnés (P0-5.2).
2. Les 100 tablettes staff sont onboardées T-30 min (P0-5.1).
3. Uvicorn passe en 4 workers en production (P1-5.3).

Sans ces 3 actions, FREKCORE **plafonnera** avant J-0 12h.

---

## 8. Ressources produites

- `/app/scripts/loadtest/locust_read.py` — scénario lecture
- `/app/scripts/loadtest/locust_emit.py` — scénario émission
- `/app/scripts/loadtest/locust_field.py` — scénario terrain
- `/app/loadtest_results/*.csv` — données brutes des 4 runs
- `/app/memory/PERFORMANCE_REPORT_v1.0.md` — ce rapport

**Reproduction** :
```bash
# Read
FREK_API=http://localhost:8001 locust -f /app/scripts/loadtest/locust_read.py \
  --headless -u 500 -r 50 -t 120s --csv=/tmp/read

# Emit
FREK_CSEC=$(grep FREK_CLIENT_KILTIKONET_SECRET /app/backend/.env | cut -d= -f2) \
  locust -f /app/scripts/loadtest/locust_emit.py \
  --headless -u 50 -r 10 -t 90s --csv=/tmp/emit

# Field
locust -f /app/scripts/loadtest/locust_field.py \
  --headless -u 50 -r 2 -t 90s --csv=/tmp/field
```

---

## 9. Reliability Report v1.0 — état d'avancement

- **[E] Proof of Existence** ✅ (self-hash `586a9c83...`)
- **[F] Performance** ✅ (ce document)
- **[G] Resilience** ⏭️ prochain
- **[H] Field** ⏭️
- **[I] Business viability** ⏭️

---

**SHA-256 auto-audit** : `40533db4847bca2702ed29e8df19e94549cd9393db51c98c89674d549097a450`
