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

## Tech Stack
- **Frontend:** React 18, Vite, Tailwind CSS, Framer Motion, Capacitor
- **Backend:** Python 3, FastAPI, MongoDB (motor), httpx
- **Integrations:** Baserow (table 865847), Amazon SES (a implementer)
- **Email:** frekcore@gmail.com
- **Domaine:** https://frekcore.com

## API v1 — 19 Endpoints
### Auth: POST /api/v1/auth/token
### Identity: emit, batch-emit, activate, status (public), detail, lookup, qr.png
### Stages: POST stage (append-only), GET stages
### Stats: cc2026, {client_id}
### Dashboard: cc2026 (consolide), cc2026/live (polling 5s)
### Admin: health, clients (CRUD), RGPD gdpr delete

## Frontend Pages
| Route | Description |
|-------|-------------|
| `/` | Certify (page principale) |
| `/dashboard` | Monitor CC2026 temps reel |
| `/verify/:id` | Verification publique |
| `/generate` | Generation attestation |

## Clients API
| client_id | Permissions |
|-----------|-------------|
| kiltikonet-cc2026 | emit, stage, stats |
| cvl-brain | stats |

## CC2026 Specifications (from docx)
- 4 composants: Email SES, Badge Intelligent (14 types), Jetons Digitaux, Evenement
- Baserow table 865847 (badges, participants, jetons, scans)
- 14 types de badges (ART, INT, STF, BNV, PRS, VIP, OFF, SPO, EXP-B/S/G/P/D/VIP)
- Jetons: 1J=1.50EUR, packs 10/25/50/100
- Date: 22 Mai 2026, Parc de La Savane, Fort-de-France, Martinique
- Objectif: 40 000 FREK-IDs

## Ce qui est fait (2026-03-13)
- [x] API v1 complete (19 endpoints)
- [x] Dashboard CC2026 (theme glassmorphism, polling live 5s)
- [x] Navigation Monitor dans le header
- [x] Funnel Luciole 5 stages
- [x] Auth OAuth2, multi-client, RGPD
- [x] Tests 100% (iteration 9: 24/24, iteration 10: 15/15)

## Backlog
- [ ] P0: Integration Baserow table 865847 (badges, participants)
- [ ] P0: Systeme Email SES (campagnes auto J-30 a J+1)
- [ ] P1: Application Scan Staff (PWA QR scan)
- [ ] P1: Systeme Jetons (wallet, paiement, packs)
- [ ] P1: Page verification publique /verify/{frek_id} v1
- [ ] P2: Rate limiting endpoints publics
- [ ] P2: Webhook notifications stage changes
- [ ] P2: 14 types de badges (nomenclature)
- [ ] P3: Export CSV/PDF, NFC integration
