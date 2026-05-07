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
- **FREK Passport : 4** (key, export, disclose, verify) — Phase 3
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
- [x] **P0** : **Phase 3 Couche C** — Portabilite passport.json signe Ed25519 + Confidentialite selective (claims partiels) — LIVRE 07/05/2026
- [x] **P1** : **Phase 4 Couche D** — W3C DID + Verifiable Credentials export (`did:frek:{frek_id}`) — LIVRE 07/05/2026
- [x] **P1** : Bcrypt sur PIN staff — LIVRE 07/05/2026 (migration legacy SHA256 transparente)
- [ ] **P0** : Verifier frekcore@gmail.com dans AWS SES + sortir du sandbox
- [ ] **P1** : Embeddable "FREK Certified" Seal (script externe pour partenaires) — LIVRE 07/05/2026
- [ ] **P1** : FREK Card NFC bindings (cartes physiques)
- [ ] **P2** : **Phase 5 Couche A.8** — Heritage / transmission (block transfer + beneficiary)
- [ ] **P2** : **Phase 5 Couche F.10** — Monetisation standard (rate limit + tier paid)
- [ ] **P2** : FREK-Chain block explorer public
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

## Phase 3 Souverainete porteur — Livree (07/05/2026, 13/13 + regression 195/195 OK)
- **Module `passport/`** isole, additif, zero breaking change.
- **Cle Ed25519 serveur** persistee dans `/app/backend/.passport_key.pem` (auto-generee, 0600). `key_id=frek-passport-v1` figee, exposee publiquement (PEM + raw 32 bytes b64).
- **Passeport complet signe** (`GET /api/v1/passport/{frek_id}`) : 12 claims, chacun avec un nonce de 16 bytes frais, racine Merkle SHA-256 binaire, signature Ed25519 sur `canonical_json(envelope)`.
- **Disclosure selective** (`POST /api/v1/passport/disclose`) : le porteur choisit les claims reveles. Les claims caches restent representes uniquement par leur empreinte ; le verificateur valide les chemins Merkle sans connaitre les valeurs cachees.
- **Verification offline** : un tiers a besoin uniquement de la cle publique + lib Ed25519 standard. Aucune dependance reseau a FREKCORE. Recompute des leaves SHA-256, folding via merkle_path, verification de signature.
- **Tampering blinde** : modifier l'envelope invalide la signature ; modifier un claim full invalide la racine Merkle ; modifier un claim partial invalide son chemin. Tests couvrent les 4 vecteurs.
- **Spec mise a jour** : section `passport` + entree changelog `1.0.0+passport`. La spec v1.0.0 reste figee, l'ajout est retrocompatible.

## Verifier offline standalone — Livree (07/05/2026, 10/10 + regression 205/205 OK)
- **Python CLI** (`/app/verifier/python/verify_passport.py`) — single file, dependance unique `cryptography`. Execute en subprocess, exit 0 si valide, 1 sinon. Test pytest reel via `subprocess.run`.
- **JS module** (`/app/verifier/js/verify_passport.js`) — single ES module, zero deps, utilise Web Crypto API native (Node 20+, Chrome 113+, Firefox 130+, Safari 17+). Smoke test Node valide 4 vecteurs (full valid, full tamper, partial valid, partial tamper).
- **Demo HTML navigateur** (`/app/verifier/js/demo.html`) — page autonome qui charge le module ES, accepte cle publique + passport en input texte, retourne le verdict offline. Aucun appel reseau.
- **Endpoints download** : `GET /api/v1/passport/verifier/{python,js,js-demo,readme}` permettent aux partenaires de telecharger les verifiers via curl/wget.
- **README** documente les 3 garanties cles : signature Ed25519, integrite Merkle SHA-256, souverainete (le verifier continue de tourner meme si frecore.com disparait).

## Architecture Bitcoin Souveraine Dual-Source — Livree (07/05/2026, 8/8 + regression 213/213 OK)
- **Module `notary/btc_node.py`** : `BitcoinNodeClient` JSON-RPC (httpx), capture chain tip (height + hash + time + merkleroot) sans wallet ni UTXO. Configurable via `BITCOIN_RPC_URL`, `BITCOIN_RPC_USER`, `BITCOIN_RPC_PASSWORD` (Cloudflare Tunnel ready).
- **Module `notary/source.py`** : `DualSourceManager` avec health cache TTL (defaut 30s), bascule **silencieuse** sur OpenTimestamps si nœud injoignable. Log `info` uniquement sur premiere transition (pas de warning bruyant).
- **`anchor.submit_block`** integre les deux sources : tente le nœud (silencieux si KO) ET soumet a OTS. Champs ajoutes dans MongoDB : `anchor_source` (`node`|`ots`), `btc_node_height`, `btc_node_block_hash`, `btc_node_time`. Zero breaking change sur les blocks existants.
- **Endpoint `GET /api/v1/notary/source/health`** : public, retourne `{configured, source, connected, tip_height?, tip_hash?, reason?}`. Aucun secret expose.
- **Tests dual-source** (8) : node connecte, node KO silencieux, non configure, cache TTL, invariants client, endpoint public — couvre les 2 modes via `unittest.mock.AsyncMock`.

## Verify enrichi + FREK Certified Seal — Livree (07/05/2026, 4 seal + UI live)
- **`/verify/{frek_id}` enrichi** : nouveau composant `PassportPanel.jsx` qui fetche passeport + cle publique, verifie en live cote navigateur (Web Crypto API), affiche signature Ed25519 + racine Merkle + 12 claims certifies (avec checkmarks par claim) + QR de telechargement passport.json + lien direct verifier offline Python. Aucune donnee envoyee a FREKCORE pour la verification.
- **Lib frontend** `/app/frontend/src/lib/passportVerify.js` : mirror exact du verifier offline JS, importe par `PassportPanel`.
- **FREK Certified Seal** : module `seal/` qui sert `GET /api/v1/seal.js` (script standalone, cle publique injectee a la livraison, cache 5 min, CORS *) + `GET /api/v1/seal/demo` (page de test). Le sceau utilise Shadow DOM pour isoler le CSS, est cliquable vers `/verify/{frek_id}` et affiche un SVG vert si valide / rouge si invalide, attributs configurables `data-size`, `data-theme`, `data-link`.
- **Indicateur Dashboard** : badge **"Nœud BTC" (vert)** ou **"Fallback OTS" (orange)** dans le widget Notary, polled toutes les 5s via `/api/v1/notary/source/health`. Visible uniquement sur le Dashboard prive (ops).
- **Tests seal** (4) : sert le JS, injecte la cle publique correctement, contient les helpers crypto + SVG, sert la page demo.

## Phase 4 W3C DID + VC — Livree (07/05/2026, 11/11 + regression 236/236 OK)
- **Module `did/`** : encoding multibase/multikey, document W3C DID Core 1.0, VC W3C Data Model 2.0.
- **Methode `did:frek:{frek_id}`** : deterministe, ne necessite aucun registre (resolution = lookup direct sur FREKCORE).
- **DID Document** : verificationMethod **Multikey** (ed25519-pub multicodec 0xed01 + base58btc) + 3 services (FrekVerificationService, FrekPassportService, VerifiableCredentialService). Marqueur `deactivated=true` si le FREK-ID est revoque.
- **Verifiable Credential** : `@context` v2 + `type` ['VerifiableCredential', 'FrekCulturalIdentityCredential'], `credentialSubject` avec frek_id/stage/event/chain anchor, `proof` **DataIntegrityProof / eddsa-jcs-2022**.
- **Cryptosuite eddsa-jcs-2022** : RFC 8785 JCS canonicalization (lightweight, pas de pyld JSON-LD), SHA-256 + Ed25519, proofValue multibase z<base58btc>.
- **Trust root partage** : la cle Ed25519 du passeport est utilisee pour signer DID + VC. Une seule rotation centrale = renouvellement de toutes les couches.
- **Endpoints** : `GET /api/v1/did/{frek_id}`, `GET /api/v1/did/method/spec`, `GET /api/v1/vc/{frek_id}`, `POST /api/v1/vc/verify`.
- **Compatibilite** : W3C DID Core 1.0, W3C VC Data Model 2.0, **eIDAS 2.0 / EUDI Wallet** (importable comme issuer institutionnel).
- **Tests Phase 4** (11) : DID Document W3C-conforme, VC issued + verifie, tampering subject/proof/missing/unknown, racine de confiance partagee avec passeport.

## Bcrypt PIN staff — Livre (07/05/2026, 8/8 + regression 19/19 staff OK)
- **`_hash_pin`** retourne maintenant un hash bcrypt cost 12 (configurable via `FREK_STAFF_BCRYPT_ROUNDS`). Format autoporteur `$2b$12$...`, sel inclus dans le hash.
- **`_verify_pin(pin, stored)`** detecte automatiquement le format (bcrypt vs SHA256 legacy) et retourne `(is_valid, needs_rehash)`.
- **Migration silencieuse** : a la premiere connexion reussie d'un compte legacy (SHA256), le PIN est re-hashe en bcrypt et `pin_migrated_at` est enregistre. Aucun downtime, aucun reset force.
- **Logs** : la migration est silencieuse (info uniquement en cas d'echec), pas de bruit operationnel.
- **Tests bcrypt** (8) : hash format, verify ok/ko, legacy ok declenche rehash, legacy ko ne touche rien, migration end-to-end via API.

## Phase 4.5 EUDI Wallet + Standards Manifest — Livree (07/05/2026, 20/20 + regression 256/256 OK)

### Plugin EUDI Wallet (OID4VCI)
- **Module `eudi/`** : metadata + service (pre-auth code state) + routes.
- **`/.well-known/openid-credential-issuer`** : OID4VCI Draft 13+, declare FREKCORE comme issuer compatible EUDI.
- **`/.well-known/oauth-authorization-server`** : RFC 8414 minimal, pre-authorized_code grant uniquement.
- **Flow complet** : POST `/api/v1/eudi/credential-offer/{frek_id}` -> QR `openid-credential-offer://...` -> POST `/token` (single-use code, TTL 5 min) -> POST `/credential` (Bearer token, TTL 5 min) -> recoit le VC W3C signe.
- **Format `ldp_vc`** : reuse complet du module `did/vc.py` existant, racine de confiance partagee.
- **Index TTL Mongo** : `eudi_offers` + `eudi_tokens` auto-effaces a expiration (pas de purge cron necessaire).
- **Tests EUDI** (10) : metadata, offer, flow E2E, single-use, grant invalide, token invalide, format invalide, VC issu validable sur `/api/v1/vc/verify`.

### Standards Manifest universel
- **Module `standards/`** : JWK Set + DID Configuration + manifest declaratif global.
- **`/.well-known/jwks.json`** : RFC 7517, kty=OKP / crv=Ed25519 / kid stable derive du hash de la cle. Universellement consommable (OIDC, OAuth2, mobile money, ITU).
- **`/.well-known/did-configuration.json`** : DIF Well-Known DID Configuration v1, signe en eddsa-jcs-2022 — prouve cryptographiquement que `frekcore.com` controle `did:frek:frekcore`.
- **`/api/v1/standards/manifest`** : declare la conformite avec W3C DID 1.0, W3C VC 2.0, EUDI/OID4VCI, ID4Africa (verification offline cruciale Afrique, AfCFTA), ITU-T X.1252/X.509, ISO mDL (preparation US), CARICOM Single ICT Space.
- **`/api/v1/standards/{ecosystem}`** : mapping detaille par ecosysteme (interop facile pour tiers).
- **Roadmap geographique** explicitement publiee : CC2026 -> CARICOM -> ID4Africa -> EUDI -> USA mDL -> IPO 2028.
- **Tests standards** (10) : JWK match passport, DID Config signature verifiable, ecosystemes listes, well-known URLs, racine de confiance unique pour passport/did/jwks/eudi.

### ~145 Endpoints API
- FREK v1 : 19 (auth, identity, stages, stats, dashboard, admin, RGPD)
- FREK Notary : 12 (notarize, proof, ots-download, anchor, blocks, chain status/verify, source/health, health)
- **FREK Staff PWA** : 11 (login, me, admin, zones, marchands, badge lookup, access, cashless, emit, sync)
- **FREK Passport** : 4 (key, export, disclose, verify) + 4 download verifier (python, js, demo, readme)
- **FREK DID + VC** : 4 (did/{id}, did/method/spec, vc/{id}, vc/verify)
- **FREK EUDI** : 5 (well-known issuer/oauth, credential-offer, token, credential)
- **FREK Standards** : 4 (well-known jwks/did-config, standards/manifest, standards/{eco})
- **FREK Seal** : 2 (seal.js, seal/demo)
- Badges : 11 (14 types, lifecycle, batch)

## Notes operationnelles
- Background loop ancrage OTS : submit toutes les 30s, upgrade BTC toutes les 30 min
- BTC confirmation : 1-6h apres soumission (gratuit)
- Calendars OTS configurables via env `OTS_CALENDARS` (defaut : 5)
- PWA offline-first : si reseau coupe, actions mises en file IndexedDB et rejouees au retour online
- Idempotence : `client_uuid` UUIDv4 genere cote client, persiste sur scans + transactions

## Audit technique — Test suite verte (06/05/2026)
- **pytest backend : 182/182 passed, 2 skipped, 0 failed (2:30)**
- Migration tests vers `localhost:8001` (in-cluster) via `conftest.py` (purge `rate_limits` par session + per-test sauf TestRateLimit)
- Helper `_ensure_unique_sparse_index` resout IndexKeySpecsConflict + DuplicateKeyError sur null en utilisant `partialFilterExpression` au lieu de sparse
- Endpoints `/api/email/templates` et `/api/email/stats` exposent `ses_mode` + `total_sent` (alias)
- Tests admin passent maintenant le header `X-Admin-Key` (verifie SECRET_KEY)
- Tests PWA assets ciblent `localhost:3000` (frontend) au lieu du backend
- Test `anchor/upgrade` borne a `max_blocks=1` pour eviter timeouts CI
