# FREK — CC2026 Ecosysteme Complet

## Vision
Plateforme AUTONOME d'identite culturelle. Observatoire culturel.
Culture Connect 2026 — 22 Mai 2026 — Parc de La Savane, Fort-de-France.
Objectif: 40 000 FREK-IDs (proof of concept Seed Round CVLN Group).

## Architecture
- Frontend: React 18, Vite, Tailwind CSS, Framer Motion, Capacitor
- Backend: Python 3, FastAPI, MongoDB (motor), boto3 (SES), Stripe
- Integrations: Baserow (table 865847), Amazon SES, Stripe
- Email: frekcore@gmail.com | Domaine: https://frekcore.com

## 98 Endpoints API

### FREK v1 (19 endpoints)
Auth, Identity, Stages, Stats, Dashboard, Admin, RGPD

### Badges (11 endpoints)
14 types, lifecycle INSCRIT→REVOQUE, NFC premium, batch create

### Jetons (9 endpoints)
4 packs, wallet, paiement marchand, historique, stats float

### Email (4 endpoints)
8 templates SES, campagnes segmentees, fallback log

### Payments/Stripe (3 endpoints)
Checkout session, status polling, packs listing

### Event J-0 (5 endpoints)
7 zones, scan QR, NFC tap, live stats, export CSV

### Webhook (1 endpoint)
Stripe webhook handler

## Status Integrations
- AWS SES: CONNECTE (credentials valides, email sender a verifier dans console SES)
- Stripe: CLE INVALIDE (mk_ prefix non reconnu, besoin sk_test_ ou sk_live_)
- Baserow: CONNECTE (token valide, table 865847 accessible)

## Tests
- Iteration 9: 24/24 (FREK v1)
- Iteration 10: 15/15 (Dashboard)
- Iteration 11: 29/29 (CC2026 composants)
- Total: 68/68 — 100%

## Actions utilisateur requises
1. Verifier frekcore@gmail.com dans AWS SES Console (eu-west-1)
2. Demander sortie sandbox SES (24-48h)
3. Fournir cle Stripe correcte (sk_test_ ou sk_live_)
