# FREK — CC2026 Notaire Culturel Tech

## Vision
Plateforme AUTONOME d'identite culturelle souveraine.
**FREKCORE n'est pas un concurrent de Kiltikonet : c'est sa couche de certification.**

| Couche | Acteur | Responsabilite |
|---|---|---|
| Business / Relation | **Kiltikonet** | CRM, billetterie, transaction commerciale (EUR), experience client |
| Identite & Preuve | **FREKCORE** | FREK-ID culturel, jetons cashless, notariat Bitcoin |

CC2026 — 22 Mai 2026 — Parc de La Savane, Fort-de-France. Objectif : 40 000 FREK-IDs.

## 3 Axes FREKCORE
1. **Notariat Culturel (Preuve)** — empreinte hash quotidienne ancree sur Bitcoin via OpenTimestamps.
2. **Standard d'Identite (FREK-ID)** — passeport culturel 2.5KB, "Legacy" archive sur 5 stages Luciole.
3. **Infrastructure Terrain (Cashless & Acces)** — PWA staff, scan QR/NFC, jetons locaux, controle zones.

## Architecture
- **Frontend** : React 18, Vite, Tailwind, Framer Motion, html5-qrcode, IndexedDB (idb), PWA (manifest + sw)
- **Backend** : Python 3, FastAPI, MongoDB, boto3 (SES), Stripe, OpenTimestamps
- **Email** : frekcore@gmail.com | Domaine : https://frekcore.com

## Couches de souverainete
1. **FREK-Chain locale** (MongoDB, instantane, gratuit) — chaque empreinte = block lie au precedent
2. **Ancrage OpenTimestamps** (5 calendars publics, gratuit) — soumission temps reel
3. **Confirmation Bitcoin** (1-6h) — preuve immuable et publiquement verifiable

## Status Integrations
- Stripe : OPERATIONNEL (rk_live_, checkout sessions)
- AWS SES : CONNECTE (sender frekcore@gmail.com a verifier SES console)
- Baserow : CONNECTE (table 865847)
- OpenTimestamps : OPERATIONNEL (5 calendars publics, ancrage temps reel)

## ~125 Endpoints API
- FREK v1 : 19 (auth, identity, stages, stats, dashboard, admin, RGPD)
- FREK Notary : 11 (notarize, proof, ots-download, anchor, blocks, chain status/verify, health)
- **FREK Staff PWA : 11** (login, me, admin, zones, marchands, badge lookup, access, cashless, emit, sync)
- Badges : 11 (14 types, lifecycle, batch)
- Jetons : 9 (packs, wallet, paiement, marchands)
- Email : 4 (send SES, campaigns, stats)
- Payments : 3 (Stripe checkout, status, packs)
- Event : 5 (scan, NFC, zones, live stats, export)
- Webhook : 1 (Stripe)

## Tests
- FREK v1 + CC2026 : 68/68 (100%)
- FREK Notary : 15/15 (100%) — iteration_12
- **FREK Staff PWA : 19/19 backend + 18/18 frontend (100%)** — iteration_13
- Idempotence replay-safe : valide curl (solde reste correct apres replay)

## Ce qui est fait
- [x] FREK v1 API complete
- [x] Dashboard CC2026 (acces prive /dashboard)
- [x] 14 types badges + lifecycle
- [x] Wallet jetons (4 packs)
- [x] Stripe LIVE (checkout sessions)
- [x] AWS SES (connecte, fallback log)
- [x] Email templates (8 campagnes)
- [x] Event J-0 (7 zones, scan, NFC, live stats)
- [x] FREK Notary — Bitcoin anchoring (FREK-Chain + OpenTimestamps)
- [x] Auto-notarisation sur identity_emit + stage_transition + access_scan + jeton_tx + walkin_emit + revocation + renewal
- [x] Page Verify — preuve Bitcoin + telechargement .ots + statut + timeline humaine
- [x] Dashboard widget Notary
- [x] PWA Scanner Staff — `/scan/*` (login PIN, 3 modes, queue offline IndexedDB, sync replay-safe)
- [x] Idempotence end-to-end via client_uuid (replay-safe)
- [x] PWA installable — manifest + service worker
- [x] **A.1 Revocation immutable** — block CRL-like sur FREK-Chain, idempotent, bloque scan PWA terrain
- [x] **A.2 Cycle de vie** — `expires_at` + endpoint `/renew` (validation date future), bloque scan terrain si expire
- [x] **E.4 Audit trail humain** — `/api/v1/audit/{frek_id}` (public, lisible francais), `/audit/agent/{id}` (auth), `/audit/event/{event}` (perm stats)

## Backlog (Phase 3+)
- [ ] **P0** : **Phase 3 Couche C** — Portabilite passport.json signe Ed25519 + Confidentialite selective (claims partiels)
- [ ] **P0** : Verifier frekcore@gmail.com dans AWS SES + sortir du sandbox
- [ ] **P1** : **Phase 4 Couche D** — W3C DID + Verifiable Credentials export (`did:frek:{frek_id}`)
- [ ] **P1** : Bcrypt sur PIN staff
- [ ] **P1** : FREK Card NFC bindings (cartes physiques)
- [ ] **P2** : **Phase 5 Couche A.8** — Heritage / transmission (block transfer + beneficiary)
- [ ] **P2** : **Phase 5 Couche F.10** — Monetisation standard (rate limit + tier paid)
- [ ] **P2** : FREK-Chain block explorer public · Embeddable seal (script externalisable)
- [ ] **P2** : Baserow bi-directional sync · Export PDF batch Twina (J-15)

## Frontiere Kiltikonet ↔ FREKCORE (ne pas confondre)
- **Kiltikonet** = couche business : page publique d'achat jetons en EUR (Stripe), CRM, billetterie, relation client. Site : kiltikonet.com.
- **FREKCORE** = couche certification + infra terrain : API `/api/jetons/*` consommee par Kiltikonet pour crediter le wallet, PWA Scanner Staff pour debits cashless on-site, notariat Bitcoin de chaque mouvement. Site : frekcore.com (autorite silencieuse).
- L'achat public de jetons en EUR n'est JAMAIS exposee sur frekcore.com.

## Phase 2 Governance — Livree (iteration_15, 26/26 backend, 83/83 regression complete)
- **B.3 Multi-tenant strict** : `event_id` + `spec_version` sur chaque block FREK-Chain (compute_block_hash inclut, sparse-indexed). Backwards-compat sur les ~99 blocs legacy (fallback hash sans event_id).
- **B.3 Filtrage** : `GET /notary/blocks?event_id=&payload_type=` · `GET /notary/chain/events` (resume agrege par event)
- **B.5 Spec versionnee** : module `spec/` expose publiquement (sans auth) `GET /spec/`, `/spec/v1.0.0`, `/spec/changelog` — contrat protocolaire fige pour reimplementation independante
- **B.3 Self-service `/admin/clients`** : POST create + POST `/{id}/rotate` (revoque tokens en cours via token_hash lookup) + PATCH (name/permissions/active/event) + DELETE soft (active=false, tokens revoques)
- **Auth durcie** : `get_current_client` rejette client `active=false` (401 'Client desactive') ET token revoque (401 'Token revoque')
- **Index** : token_hash, frek_clients.active, frek_clients.event
- **Frontend** : Dashboard widget Multi-event affiche events agreges + spec_version sur Notary panel

## Phase 2.5 Security Hardening — Livree (iteration_16, 16/16 + regression 57/57 OK)
- **Rate limit silencieux** : sliding window MongoDB (scope, action). Defaut 100/h emit, 500/h stage, 5000/h scan. **HTTP 429 sans Retry-After, sans detail explicatif**. Anomaly enregistre `kind=rate_limit_hit` severity=warning. Configurable via env FREK_RATE_*_PER_HOUR.
- **Brute-force PIN lockout** : 5 echecs en 15min => locked_until=+15min. 401 generique 'Agent ou PIN invalide' (pas de differentiation attaquant). Anomaly `kind=staff_lockout`. Unlock auto OU manuel.
- **Anomaly trail interne** : collection `security_events` + endpoints `/admin/security/{events,lockouts,staff/{id}/unlock}` (X-Admin-Key only). Aucune fuite vers public. Webhook optionnel `FREK_SECURITY_WEBHOOK_URL`.
- **Secret rotation sans downtime** : `POST /admin/clients/{id}/rotate` (deja Phase 2) revoque vraiment les tokens en cours via `token_hash` lookup. 401 immediate sur ancien JWT.
- **Spec ouverture sectorielle** (sans changer la nature de FREK) : 10 secteurs documentes (culture, education, health, justice, finance, telecom, media, phygital, tech, identity) + extension_model + sector_examples + section security_policies. Spec reste figee a v1.0.0 (ajout retrocompatible).
- **Migration tests stales** : 3 tests dashboard_v2 mis a jour (422 -> 403 conforme Phase 2.5)

## Notes operationnelles
- Background loop ancrage OTS : submit toutes les 30s, upgrade BTC toutes les 30 min
- BTC confirmation : 1-6h apres soumission (gratuit)
- Calendars OTS configurables via env `OTS_CALENDARS` (defaut : 5)
- PWA offline-first : si reseau coupe, actions mises en file IndexedDB et rejouees au retour online
- Idempotence : `client_uuid` UUIDv4 genere cote client, persiste sur scans + transactions
