# FREK — Fichier de Referencement et d'Empreinte Kulturelle

## Identite
Plateforme AUTONOME d'identite culturelle.
FREK est un observatoire culturel, pas un tracker.
Culture Connect 2026 est le premier client.

## Architecture Luciole — 5 Stages
1. **GENESIS** — Naissance identite FREK (inscription evenement)
2. **WORKSHOP** — Participation active (atelier, creation)
3. **METAMORPHOSE** — Echange economique culturel (achat jetons, vente)
4. **EMISSION** — Presence performance (scan zone scene)
5. **LEGACY** — Empreinte finale archivee (fin evenement)

3% visible (stage atteint) / 97% prive (detail chiffre)
Append-only : immuable une fois ecrit

## Principes
- **FREK SOUVERAIN** — Ne depend PAS de kiltikonet.fr
- **FREK_ID UNIVERSEL** — UUID v4 permanent, jamais regenere
- **LEGERETE** — Fingerprint SHA256 uniquement (~2.5KB par empreinte)
- **MULTI-CLIENT** — X-Client-Id isole les donnees par client
- **APPEND-ONLY** — Un stage enregistre ne peut jamais etre supprime
- **FREK_EMAIL_SALT** — CRITIQUE : ne jamais changer apres le premier deploiement

## Tech Stack
- **Frontend:** React 18, Vite, Tailwind CSS, Capacitor (mobile), Framer Motion
- **Backend:** Python 3, FastAPI, MongoDB (motor), httpx
- **Email:** frekcore@gmail.com
- **Domaine:** https://frekcore.com
- **Integrations:** Baserow (token configure)

## API v1 — Endpoints (19 total)
### Auth
- `POST /api/v1/auth/token` — Client credentials OAuth2
### Identity
- `POST /api/v1/identity/emit` — Creer FREK-ID (idempotent par email)
- `POST /api/v1/identity/batch-emit` — Emission par lot (max 500)
- `POST /api/v1/identity/{id}/activate` — Activer (1er scan physique)
- `GET /api/v1/identity/{id}/status` — Stages + progression (PUBLIC)
- `GET /api/v1/identity/{id}/detail` — Detail complet (auth requise)
- `POST /api/v1/identity/lookup` — qr_token → frek_id
- `GET /api/v1/identity/{id}/qr.png` — QR code PNG
### Stages
- `POST /api/v1/identity/{id}/stage` — Enregistrer (append-only)
- `GET /api/v1/identity/{id}/stages` — Historique
### Stats
- `GET /api/v1/stats/cc2026` — Stats CC2026 (objectif 40 000)
- `GET /api/v1/stats/{client_id}` — Stats par client
### Dashboard
- `GET /api/v1/dashboard/cc2026` — Metriques consolidees + funnel + timeline
- `GET /api/v1/dashboard/cc2026/live` — Polling leger temps reel (5s)
### Admin (protege par X-Admin-Key = SECRET_KEY)
- `GET /api/v1/health` — Sante systeme
- `GET /api/v1/admin/clients` — Liste clients API
- `POST /api/v1/admin/clients` — Creer client
- `DELETE /api/v1/admin/clients/{id}` — Supprimer client
- `DELETE /api/v1/admin/identity/{id}/gdpr` — RGPD droit a l'oubli

## Frontend Pages
| Route | Page | Description |
|-------|------|-------------|
| `/` | Certify | Page principale (certification audio) |
| `/dashboard` | Dashboard | Monitor CC2026 temps reel |
| `/verify/:id` | Verify | Verification publique |
| `/generate` | Generate | Generation attestation |
| `/about` | About | A propos |
| `/legal` `/privacy` `/cookies` `/terms` | Legal | Pages legales |

## Clients API enregistres
| client_id | Nom | Permissions |
|-----------|-----|-------------|
| kiltikonet-cc2026 | Culture Connect 2026 | emit, stage, stats |
| cvl-brain | CVL Brain Analytics | stats |

## Objectifs
- **CC2026:** 40 000 FREK-IDs (proof of concept)
- **CC2027:** FREK inter-edition (rollover natif)
- **KORA:** FREK social (identite sur reseau)
- **CVL BRAIN:** OAPI analytique (observatoire culturel)
- **CVLN Holding:** FREK standard d'identite culturelle CVLN

## Collections MongoDB
- `frek_identities` — frek_id, email_hash, client_id, stages_completed, ...
- `frek_stages` — frek_id, stage, fingerprint, sequence (append-only)
- `frek_clients` — client_id, name, secret_hash, permissions
- `frek_tokens` — token_hash, client_id, expires_at, revoked

## Ce qui est fait
### 2026-03-13 (Session actuelle)
- [x] API v1 complete — 19 endpoints
- [x] Auth client_credentials OAuth2
- [x] Multi-client isolation
- [x] Stages append-only (5 stages Luciole)
- [x] RGPD droit a l'oubli
- [x] Admin securise par X-Admin-Key
- [x] Batch emit pour production CC2026
- [x] QR code PNG generation
- [x] Clients pre-enregistres (kiltikonet-cc2026, cvl-brain)
- [x] Dashboard CC2026 backend (metriques consolidees + live polling)
- [x] Dashboard CC2026 frontend (Luciole theme #0C0818/#C9A84C)
- [x] Funnel Luciole 5 stages visualise
- [x] Timeline 30 jours
- [x] Polling temps reel 5s
- [x] Indexes MongoDB
- [x] Tests 100% (iteration 9: 24/24, iteration 10: 15/15)

### Precedent
- [x] Frontend UI/UX (white 3D theme, glassmorphism)
- [x] Pages legales (Privacy, Cookies, Terms, etc.)
- [x] Capacitor (iOS/Android)
- [x] Legacy API /api/frek/ preservee
- [x] QR/PDF attestation (ancien systeme)

## Backlog
- [ ] P1: Page de verification publique /verify/{frek_id} avec nouveau systeme v1
- [ ] P2: Rate limiting sur endpoints publics
- [ ] P2: Token revocation endpoint
- [ ] P2: Webhook notifications pour stage changes
- [ ] P2: Integration Baserow complete (table_id a configurer)
- [ ] P3: Export CSV/PDF des identites
- [ ] P3: Tests d'audit 100%
