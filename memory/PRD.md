# FREK — CC2026 Ecosysteme Complet (Notaire Culturel Tech)

## Vision
Plateforme AUTONOME d'identite culturelle. Observatoire culturel.
**FREK est le Notaire Culturel Tech** : ancrage immuable des empreintes culturelles sur Bitcoin via OpenTimestamps.
CC2026 — 22 Mai 2026 — Parc de La Savane, Fort-de-France.
Objectif: 40 000 FREK-IDs.

## Architecture
- **Frontend** : React 18, Vite, Tailwind CSS, Framer Motion, Capacitor
- **Backend** : Python 3, FastAPI, MongoDB, boto3 (SES), Stripe, OpenTimestamps
- **Email** : frekcore@gmail.com | Domaine : https://frekcore.com
- **Notaire** : FREK-Chain locale (SHA256 hash chain) + OpenTimestamps -> Bitcoin

## Couches de souverainete
1. **FREK-Chain locale** (MongoDB, instantane, gratuit) — chaque empreinte = block lie au precedent (tamper-evident)
2. **Ancrage OpenTimestamps** (5 calendars publics, gratuit) — soumission temps reel
3. **Confirmation Bitcoin** (1-6h apres soumission) — preuve immuable et publiquement verifiable

## Status Integrations
- Stripe : OPERATIONNEL (rk_live_, checkout sessions fonctionnelles)
- AWS SES : CONNECTE (sender frekcore@gmail.com a verifier dans SES console)
- Baserow : CONNECTE (table 865847)
- **OpenTimestamps : OPERATIONNEL** (5 calendars publics, ancrage temps reel BTC)

## ~110 Endpoints API
- FREK v1 : 19 (auth, identity, stages, stats, dashboard, admin, RGPD)
- **FREK Notary : 11** (notarize, proof, ots-download, anchor, blocks, chain status/verify, health)
- Badges : 11 (14 types, lifecycle, batch)
- Jetons : 9 (packs, wallet, paiement, marchands)
- Email : 4 (send SES, campaigns, stats)
- Payments : 3 (Stripe checkout, status, packs)
- Event : 5 (scan, NFC, zones, live stats, export)
- Webhook : 1 (Stripe)

## Tests
- FREK v1 + CC2026 : 68/68 (100%)
- **FREK Notary : 15/15 (100%)** — iteration_12

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
- [x] **FREK Notary** — Couche notaire Bitcoin (FREK-Chain locale + OpenTimestamps)
- [x] **Auto-notarisation** sur identity_emit + stage_transition (background async)
- [x] **Page Verify** — affichage preuve Bitcoin + telechargement fichier .ots
- [x] **Dashboard widget Notary** — hauteur chaine, OTS ancres, BTC confirmes, integrite

## Backlog
- [ ] **P0** : Frontend page achat jetons (Stripe Checkout UI publique pour 4 packs)
- [ ] **P0** : PWA App Scan Staff (interface scan QR/NFC J-0)
- [ ] **P0** : Verifier frekcore@gmail.com dans AWS SES + sortir du sandbox
- [ ] **P1** : Open API "FREK Certified" (expansion API publique)
- [ ] **P1** : FREK Card NFC bindings (cartes physiques)
- [ ] **P1** : Auto-notarisation Badges + Jetons transactions
- [ ] **P2** : Baserow bi-directional sync
- [ ] **P2** : Export PDF batch Twina (J-15)
- [ ] **P2** : FREK-Chain block explorer (UI publique)

## Notes operationnelles
- Background loop ancrage OTS : submit toutes les 30s (jusqu'a 50 blocks/sweep), upgrade BTC toutes les 30 min
- BTC confirmation typique : 1-6h apres soumission (gratuit, frais payes par calendar servers OTS)
- Calendars OTS configurables via env `OTS_CALENDARS` (defaut : 5 calendars publics)
- Verification publique : `GET /api/v1/notary/proof/{frek_id}` + telechargement `.ots` verifiable hors-ligne
