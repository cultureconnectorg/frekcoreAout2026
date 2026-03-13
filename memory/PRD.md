# FREK — Fichier de Referencement et d'Empreinte Kulturelle

## Vision
Plateforme AUTONOME d'identite culturelle. Observatoire culturel, pas un tracker.
Culture Connect 2026 est le premier client — 40 000 FREK-IDs.

## Architecture Luciole — 5 Stages
1. GENESIS — Badge cree + FREK-ID emis
2. WORKSHOP — Participation ateliers
3. METAMORPHOSE — Achat jetons, echanges economiques
4. EMISSION — Scan zone scene/VIP/backstage
5. LEGACY — Empreinte finale archivee

## Tech Stack
- Frontend: React 18, Vite, Tailwind CSS, Framer Motion, Capacitor
- Backend: Python 3, FastAPI, MongoDB (motor), httpx
- Integrations: Baserow (table 865847), Amazon SES (log mode), Stripe (test key)
- Email: frekcore@gmail.com | Domaine: https://frekcore.com

## 4 Composants CC2026 — TOUS IMPLEMENTES

### Composant 1: Email Service
- 8 templates (bienvenue, j-30, j-15, j-7, j-1, j-0, j+1, recharge)
- Campagnes segmentees par type badge
- Mode LOG (dev) / SES (prod avec credentials AWS)
- Endpoints: send, campaign, stats, templates

### Composant 2: Badges Intelligents
- 14 types (ART, INT, STF, BNV, PRS, VIP, OFF, SPO, EXP-B/S/G/P/D/VIP)
- NFC pour badges premium (VIP, OFF, SPO, EXP-G+)
- Lifecycle: INSCRIT -> CONFIRME -> BADGE_EMIS -> ACTIVE -> REVOQUE
- Endpoints: create, batch-create, activate, confirm, emit, print, deliver, stats

### Composant 3: Jetons Digitaux
- 1 Jeton = 1.50 EUR
- 4 packs: Decouverte(10J/13.50EUR), Culture(25J/30EUR), Diaspora(50J/55EUR), VIP(100J/100EUR)
- Wallet, paiement marchand, historique, remboursement SEPA
- Marchands avec solde du

### Composant 4: Evenement J-0
- 7 zones: ENTREE, SCENE, VIP_LOUNGE, BACKSTAGE, EXPOSANTS, PRESSE, ATELIERS
- Matrice acces par type badge
- Scan QR + NFC tap payment
- Dashboard live temps reel
- Export CSV post-evenement

## API Endpoints (40+ total)
### FREK v1 (19): auth, identity, stages, stats, dashboard, admin, RGPD
### Badges (10): types, create, batch-create, get, activate, confirm, emit, print, deliver, stats
### Jetons (9): packs, recharge, paiement, solde, historique, remboursement, stats, marchands CRUD
### Email (4): templates, send, campaign, stats
### Event (5): zones, scan, nfc/tap, stats/live, stats/export

## Tests
- Iteration 9: 24/24 (FREK v1 core API)
- Iteration 10: 15/15 (Dashboard + admin securise)
- Iteration 11: 29/29 (CC2026 4 composants)
- Total: 68/68 — 100%

## Clients API
| client_id | Permissions |
|-----------|-------------|
| kiltikonet-cc2026 | emit, stage, stats |
| cvl-brain | stats |

## Ce qui est fait (2026-03-13)
- [x] FREK v1 API complete (19 endpoints)
- [x] Dashboard CC2026 Monitor temps reel
- [x] 14 types badges + lifecycle
- [x] Wallet jetons (4 packs, paiement marchand)
- [x] Email service (8 templates, campagnes)
- [x] Event J-0 (7 zones, scan, NFC, live stats)
- [x] RGPD droit a l'oubli
- [x] Multi-client isolation
- [x] Tests 100% (68/68)

## Backlog
- [ ] P0: AWS SES credentials pour email en production
- [ ] P0: Stripe integration reelle (recharge CB)
- [ ] P1: Frontend dashboard etendu (badges, jetons, event stats)
- [ ] P1: PWA App Scan Staff
- [ ] P2: Baserow sync bidirectionnelle
- [ ] P2: Webhook notifications
- [ ] P3: NFC UID binding, export PDF badges
