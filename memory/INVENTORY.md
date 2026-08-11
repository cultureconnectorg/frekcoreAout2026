# FREKCORE — Inventaire complet (v1.0 février 2026)

> État de la production au 08/07/2026 — après itérations 22 → 28 (100% verts).
> Doctrine unique : **FREKCORE atteste l'existence, l'intégrité et l'origine déclarée d'un objet numérique.**

---

## 1. IDENTITÉ UNIQUE : FREK-ID

Tout se rattache à **UN** FREK-ID :

```
                       FREK-ID
                          │
   ┌──────────┬───────────┼───────────┬──────────┐
Passkey    Moments        FK       Engagement    Audit
   │          │            │            │           │
   └──────────┴────────────┴────────────┴───────────┘
                          │
                    Mon univers
                          │
                Patrimoine numérique
```

Aucune duplication d'identité, aucun compte parallèle, aucun mot de passe.

---

## 2. BACKEND — 30 modules · ~64 endpoints publics

### Modules cœur
| Module | Rôle |
|---|---|
| `identity_engine/` | FREK-ID + WebAuthn/Passkey (register/authenticate begin+complete, session HMAC 90j, X-FREK-Session) |
| `moment/` | Sign + sign-media + verify + mine + stats + storage médias |
| `fk/` | FK Cultural Object v0.1 (create/verify/detail/download `?compat=zip`/pubkey/stats) |
| `notary/` | FREK-Chain (blocks Ed25519, ancrage OpenTimestamps→Bitcoin) |
| `passport/` | Verifier Python + JS + README (offline, open source) |
| `frek_v1/` | Identity protocol Luciole (11 niveaux) + dashboard + admin |
| `heritage/` | Patrimoine préservé (versions, historique) |
| `sync/` | Baserow bi-directionnel (P2 partiel) |
| `services/` | Stripe checkout, boto3 SES email |

### Modules support
`audit/`, `badges/`, `core/`, `counter/`, `did/`, `email_service/`, `eudi/`, `event/`, `fingerprint/`, `geo/`, `health/`, `investor/`, `jetons/`, `pdf_batch/`, `seal/`, `security/`, `spec/`, `staff/`, `standards/`, `tests/`

### Endpoints clés
```
IDENTITY
  POST /api/v1/identity/init
  GET  /api/v1/identity/me
  POST /api/v1/identity/{id}/register/begin + /complete
  POST /api/v1/identity/authenticate/begin + /complete
  GET  /api/v1/identity/{id}/objects

MOMENT
  POST /api/v1/moment/sign
  POST /api/v1/moment/sign-media (multipart)
  GET  /api/v1/moment/stats
  GET  /api/v1/moment/mine?session_id=

FK
  POST /api/v1/fk/create (multipart, keep=true|false)
  POST /api/v1/fk/verify (upload .fk)
  GET  /api/v1/fk/detail/{id}
  GET  /api/v1/fk/{id}/download[?compat=zip]   ← iOS-friendly
  GET  /api/v1/fk/pubkey
  GET  /api/v1/fk/stats

PASSPORT (Verifier open source)
  GET /api/v1/passport/verifier/python
  GET /api/v1/passport/verifier/js
  GET /api/v1/passport/verifier/readme

HEALTH
  GET /api/v1/health/live
  GET /api/v1/health/deep
```

### Config WebAuthn (production-ready)
- `FREK_RP_ORIGIN` = origin canonique (fail-fast si absent en prod, plus de fallback `localhost` silencieux)
- Log startup : `Identity Engine RP: rp_id=<host> origin=<url>`

---

## 3. FRONTEND — 31 pages · 35 routes

### Portail
| Route | Rôle | Composant |
|---|---|---|
| `/universe` (alias `/create`) | **Porte d'entrée unique** — 4 modes (loading/entrance/create/recover/resume) | Universe.jsx |
| `/` | Signer un moment (avec cadre éthique + engagement session) | Moment.jsx |
| `/mine` | "Mon univers" — moments + FK + journal d'audit engagement | MyMoments.jsx |
| `/identity` | Passkey (register/authenticate) — WebAuthn diag renforcé | Identity.jsx |

### Objets
| Route | Rôle |
|---|---|
| `/fk` | Créer un objet FK + vérifier |
| `/fk/view/:id` | **Lecteur FK en navigateur** — iOS-friendly, JSZip client-side |
| `/fk/view` | Upload local d'un .fk |
| `/verify/:id` | Preuve d'un moment |
| `/verify-moment/:id` | Vérification alternative (MomentVerify.jsx) |
| `/verifier` | Vérificateur offline Python + JS (page interne) |

### Content
| Route | Composant |
|---|---|
| `/manifeste` | Manifeste avec phrase RDV |
| `/spec` | Charte FK v0.1 |
| `/philosophy` | Philosophie |
| `/accueil` | Landing v2 |
| `/atlas` | Atlas culturel |
| `/proof` | Preuve publique |
| `/explorer` | Blocs FREK-Chain |
| `/profil/:id`, `/card`, `/scanner`, `/poste`, `/certify`, `/generate`, `/dashboard` | Modules v2/CC2026 |
| `/legal`, `/privacy`, `/cookies`, `/terms`, `/disclosure`, `/imprint`, `/help` | Content pages |
| `/admin-pdf`, `/scan-app` | Admin & PWA |

### Composants clés partagés
- **`components/BrandLogo.jsx`** — logo cliquable (sans wordmark) → `/universe` sur toutes les pages v1.0
- **`components/PageTransition.jsx`** — transitions cinématiques Framer Motion
- **`lib/engagement.js`** — utility engagement session (SHA-256, TTL 4h, historique 50 sessions)

---

## 4. WORKFLOWS PROFESSIONNELS (Phase 5)

Les 5 profils choisis dans `/universe` orientent l'expérience sans créer de compte parallèle :

| Profil | Question métier | Boutique d'outils actifs |
|---|---|---|
| **Artiste** | *Comment je prouve que cette création est la mienne ?* | `/` (signer) · `/fk` (créer FK) · `/mine` (patrimoine + audit) · téléchargement `.fk.zip` |
| **Label / Industrie** | *Comment je protège mon catalogue ?* | Mêmes outils, orientation multi-artistes (via multi-sessions localStorage) — pas de multi-tenant B2B avant signal réel |
| **Notaire / Juriste** | *Puis-je utiliser cela comme élément de preuve ?* | `/fk` upload + `/fk/view/:id` (lecture claire) + `/verifier` (Python/JS hors-ligne) |
| **Institution culturelle** | *Comment je garantis que cette mémoire ne sera jamais perdue ?* | `/fk` create keep=true + `/heritage/` versions + `/mine` audit |
| **Développeur** | Docs / SDK / pubkey / verify / exemples | `/spec` + `/verifier` + `/api/v1/fk/pubkey` + endpoints publics |

---

## 5. CE QUI A ÉTÉ RÉELLEMENT BRANCHÉ (audit intégration)

### Connexions déjà en place (Phase 0 audit iter22)
- `X-FREK-Session` auto-link sur `/moment/sign`, `/sign-media`, `/fk/create` → moments et FK rattachés à `frek_persons.linked_objects[]`
- `identity_type` (individual/professional/institution) supporté depuis `models.py` Pydantic Literal
- `frek_persons.metadata.profile` dict libre → stocke le profil narratif

### Ce qui a été branché dans cette session (iter22 → 28)
- `/universe` orchestre les briques existantes sans nouvel endpoint
- Engagement session 4h persistée + audit journal `/mine`
- WebAuthn diag renforcé (isUVPAA non-bloquant, messages iOS-specific, errorDetail collapsible)
- FK viewer navigateur `/fk/view/:id` avec JSZip → lit `manifest.fk.json` + layers metadata (identity/creators/timeline) + `proof/frekcore-attestation.json`
- Endpoint `GET /fk/{id}/download?compat=zip` renomme en `.fk.zip` pour iOS
- Verifier Python/JS accessible via `/verifier` (page interne, plus de page blanche)
- BrandLogo cliquable unifié sur toutes les pages v1.0

---

## 6. DOUBLONS SUPPRIMÉS (nettoyage)

- Ancien "Ton univers" → "Mon univers" (langue unifiée)
- Ancien "SIGNER" libre → cadre éthique obligatoire (titre requis + engagement)
- Ancien lien "accessible ici" → `text/x-python` raw → page interne `/verifier`
- Ancien "Passkey annulée" opaque → messages contextualisés iOS/Windows/hybrid
- Ancien fallback `rp_id=localhost` → `WebAuthnConfigError` fail-fast en prod
- 11 dépendances backend obsolètes (librosa, pgvector, sqlalchemy…) purgées

---

## 7. POINTS D'EXTENSION DISPONIBLES (open ecosystem — préparés, pas activés)

Le moteur est prêt à recevoir des acteurs externes SANS modifier le cœur :

| Point d'extension | Statut | Comment activer |
|---|---|---|
| **API tierces** | Publique dès aujourd'hui | Endpoints `/api/v1/fk/verify`, `/moment/detail`, `/fk/detail`, `/passport/verifier/*` sont anonymes et vérifiables sans compte |
| **Verifier open source** | Prêt et servi | Python + JS accessibles via `/verifier`, code lisible + téléchargeable + copiable |
| **Public key** | Prête | `GET /api/v1/fk/pubkey` retourne Ed25519 publique — un tiers peut vérifier une signature sans nous contacter |
| **DAW / DSP / labels** | Points d'extension prêts | Peuvent poster sur `/fk/create` avec `keep=true` + récupérer `frek_id` + partager URL `/fk/view/{id}` |
| **Notaires / juristes** | UX prête | `/verifier` + `/fk/view` = duo lecture + validation hors-ligne |
| **Institutions / musées / archives** | Structure prête | `heritage/` module + `object_type=heritage` dans FK |
| **SDK client** | À écrire quand signal | Squelette prêt via schémas Pydantic exposés dans `/spec` |

---

## 8. HORS PÉRIMÈTRE VOLONTAIRE (doctrine "signal réel")

Ces éléments existent en concept mais NE SONT PAS construits — attendent un signal utilisateur concret :

- **Community Graph** inter FREK-ID (relations, collaborations)
- **Trust Bridge OAuth / SSO externe** (Google, Apple, DID)
- **Multi-tenant B2B** (organizational spaces multi-membres)
- **Institutional API keys** avec quotas et facturation
- **CLI FK** autonome (create/verify en ligne de commande)
- **FREKANSLA fingerprint** perceptual audio
- **Backend notarié pour engagement session** (option b — actuellement local seulement)

---

## 9. INTÉGRATIONS EXTERNES (état au 08/07/2026)

| Service | Statut | Bloquant |
|---|---|---|
| Stripe (checkout live) | ✅ Actif | – |
| OpenTimestamps (ancrage Bitcoin) | ✅ Actif | – |
| AWS SES (email) | 🟠 Configuré, `ses_mode=ses` | Verifier `frekcore@gmail.com` dans console AWS + sortir du Sandbox |
| Baserow (DB sync) | 🟠 Token expiré | Régénérer token dans `/settings/tokens` puis update `.env` |
| Resend | ⏳ Pending API key | Optionnel |

---

## 10. AUDIT "Coming Soon" — aucune promesse non tenue

Passe grep sur `frontend/src/**/*.jsx` : **0 occurrence** de "coming soon", "à venir", "bientôt", "placeholder" côté production visible.

---

## 11. TESTS

- 28 itérations testing_agent (backend + frontend)
- Dernière : **iteration_28 = 100%**
- pytest backend : **9/9 régression Univers + 6/6 régression engagement + 8/8 FK iOS + 6/6 identity + …**
- Testing agent auto-lance à chaque bug remonté par le fondateur (system_reminder respect)

---

## 12. ENVIRONNEMENT

- Kubernetes cloud container (preview `https://culture-chain.preview.emergentagent.com`)
- Frontend : React 18 + Vite + Tailwind + Framer Motion + JSZip
- Backend : FastAPI + MongoDB + boto3 + Stripe + cryptography (Ed25519) + webauthn
- Prod : `FREK_RP_ORIGIN=https://frekcore.com` à définir (fail-fast confirmé si absent)

---

*Fin d'inventaire — architecture de production cohérente, aucune philosophie ajoutée.*
