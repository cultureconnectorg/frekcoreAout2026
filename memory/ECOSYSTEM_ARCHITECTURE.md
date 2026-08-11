# FREKCORE — Ecosystem Architecture Alignment v1.0

> Date : 08/07/2026 · Statut : **Livré et testé (13/13 pytest verts)**

## 1. Doctrine (inchangée)

> **FREKCORE atteste l'existence, l'intégrité et l'origine déclarée d'un objet numérique.**

FREKCORE devient le **Core Integration / Trust Layer** de l'écosystème FREK — sans absorber les responsabilités des autres branches.

---

## 2. Cartographie AVANT / APRÈS

### AVANT
FREKCORE fonctionnait mais ne connaissait pas explicitement son écosystème.
- Backend riche (30 modules, ~64 endpoints)
- FREK V3 ajouté isolé à `/app/frek_v3/`
- **Aucune conscience** de FREKRAW, FREKANSLA
- **Aucun endpoint** pour interroger l'état de l'écosystème

### APRÈS
- **`/app/ecosystem/`** — registry + capabilities + contrats
- **`/app/backend/ecosystem/`** — router `/api/v1/ecosystem/*` (5 endpoints)
- **10 composants** déclarés avec leur vrai statut (7 actifs + 1 isolé + 2 externes)
- **13 tests d'intégration** verts
- **0 régression** — tous les endpoints existants intacts

---

## 3. Classification des 10 composants

| Composant | Statut | Localisation | Endpoints backend |
|---|---|---|---|
| FREKCORE | `active` | `/app/backend/` | `/api/v1/*` |
| FREK-ID | `active` | `/app/backend/identity_engine/` | `/api/v1/identity/*` |
| FK | `active` | `/app/backend/fk/` | `/api/v1/fk/*` |
| FREK-Chain | `active` | `/app/backend/notary/` | `/api/v1/notary/*` |
| Passport | `active` | `/app/backend/passport/` | `/api/v1/passport/*` |
| Heritage | `active` | `/app/backend/heritage/` | `/api/v1/heritage/*` |
| DID/VC | `active` | `/app/backend/did/` | `/api/v1/did/*`, `/vc/*`, `/eudi/*` |
| **FREK V3** | `specified_isolated` | `/app/frek_v3/` | **aucun** (Rust/FPGA future) |
| **FREKRAW** | `external_specified` | néant | **aucun** (contrat seul) |
| **FREKANSLA** | `external_specified` | néant | **aucun** (contrat seul) |

---

## 4. Contrats d'intégration écrits

Trois branches non-implémentées ont un contrat formel dans `/app/ecosystem/contracts/` :

- **`frekraw.md`** — record certification protocol. **Explicitement PAS un langage de programmation.**
- **`frekansla.md`** — audio DSP / perceptual fingerprint.
- **`frek_v3.md`** — hardware root of trust (référence Python 16/16 pytests OK).

Chaque contrat définit : purpose, integration flow, request/response shape, errors, current status.

---

## 5. Nouveaux endpoints (5)

```
GET /api/v1/ecosystem                            → registry global (doctrine + composants)
GET /api/v1/ecosystem/components                 → liste tous les composants
GET /api/v1/ecosystem/components/{id}            → détail d'un composant
GET /api/v1/ecosystem/capabilities               → capabilities registry
GET /api/v1/ecosystem/integrations               → branches non-actives (external/isolated)
GET /api/v1/ecosystem/integrations/{id}/status   → statut ponctuel (NOT_INSTALLED / ACTIVE / …)
```

Une branche **absente** ou **inconnue** répond `NOT_INSTALLED` proprement, jamais 500.

---

## 6. Règles absolues respectées

- ❌ **Zéro invention** — versions/protocoles null pour branches absentes (vérifié par `test_registry_json_valid`)
- ❌ **Zéro simulation** — pas de fake FREKRAW ni FREKANSLA
- ❌ **Zéro fusion** — FREK V3 reste à `/app/frek_v3/`, hors backend
- ❌ **FREKRAW ≠ langage de programmation** (vérifié par `test_frekraw_contract_forbids_programming_language_interpretation`)
- ✅ **Non-régression** — `test_regression_health_still_alive` + endpoints `/fk/stats`, `/moment/stats`, `/identity/*` intacts
- ✅ **Contract-first** — chaque branche externe a un `.md` avec input/output/errors/verification_method

---

## 7. Vérifications live

- `GET /api/v1/ecosystem` → 10 composants, doctrine ok
- `GET /api/v1/ecosystem/integrations/frekraw/status` → `{"status": "NOT_INSTALLED"}`
- `pytest tests/test_ecosystem.py` → **13 passed en 1.13s**
- `curl /api/v1/fk/stats` → toujours 13 FK servis (non-régression)

---

## 8. Restant hors périmètre (par doctrine)

- Implémentation FREKRAW (branche spécialisée externe, à écrire par une autre équipe/repo)
- Implémentation FREKANSLA (branche audio DSP, à écrire quand signal)
- Adapter Rust FREK V3 (Phase 2, hors périmètre actuel)
- Endpoints `/frekraw/*` ou `/frekansla/*` — **volontairement absents**

---

## 9. Fichiers créés / modifiés

**Créés (11) :**
- `/app/ecosystem/registry.json`
- `/app/ecosystem/capabilities.json`
- `/app/ecosystem/contracts/frekraw.md`
- `/app/ecosystem/contracts/frekansla.md`
- `/app/ecosystem/contracts/frek_v3.md`
- `/app/backend/ecosystem/__init__.py`
- `/app/backend/ecosystem/routes.py`
- `/app/backend/tests/test_ecosystem.py`
- `/app/memory/ECOSYSTEM_ARCHITECTURE.md` (ce document)

**Modifiés (1) :**
- `/app/backend/server.py` — 2 lignes ajoutées (import + include_router ecosystem)

**Intouchés :**
- Tout le reste du backend, du frontend, `/app/frek_v3/`
