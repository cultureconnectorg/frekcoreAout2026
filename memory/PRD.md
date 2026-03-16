# FREK — CC2026 Ecosysteme Complet

## Vision
Plateforme AUTONOME d'identite culturelle. Observatoire culturel.
CC2026 — 22 Mai 2026 — Parc de La Savane, Fort-de-France.
Objectif: 40 000 FREK-IDs.

## Architecture
- Frontend: React 18, Vite, Tailwind CSS, Framer Motion, Capacitor
- Backend: Python 3, FastAPI, MongoDB, boto3 (SES), Stripe
- Email: frekcore@gmail.com | Domaine: https://frekcore.com

## Status Integrations
- Stripe: OPERATIONNEL (rk_live_, checkout sessions fonctionnelles)
- AWS SES: CONNECTE (sender frekcore@gmail.com a verifier dans SES console)
- Baserow: CONNECTE (table 865847)

## 98 Endpoints API
- FREK v1: 19 (auth, identity, stages, stats, dashboard, admin, RGPD)
- Badges: 11 (14 types, lifecycle, batch)
- Jetons: 9 (packs, wallet, paiement, marchands)
- Email: 4 (send SES, campaigns, stats)
- Payments: 3 (Stripe checkout, status, packs)
- Event: 5 (scan, NFC, zones, live stats, export)
- Webhook: 1 (Stripe)

## Tests: 68/68 (100%)

## Ce qui est fait
- [x] FREK v1 API complete
- [x] Dashboard CC2026 (acces prive /dashboard uniquement)
- [x] 14 types badges + lifecycle
- [x] Wallet jetons (4 packs)
- [x] Stripe LIVE (checkout sessions)
- [x] AWS SES (connecte, fallback log)
- [x] Email templates (8 campagnes)
- [x] Event J-0 (7 zones, scan, NFC, live stats)
- [x] Monitor retire de l'interface publique

## Backlog
- [ ] P0: Verifier frekcore@gmail.com dans AWS SES + sortir du sandbox
- [ ] P1: Frontend page achat jetons
- [ ] P1: PWA App Scan Staff
- [ ] P2: Baserow sync
- [ ] P3: Export PDF badges Twina
