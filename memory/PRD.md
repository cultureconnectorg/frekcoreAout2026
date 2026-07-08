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
- **FREK EUDI** : 6 (well-known issuer/oauth, credential-offer, token, credential, credential/verify-sdjwt)
- **FREK Standards** : 4 (well-known jwks/did-config, standards/manifest, standards/{eco})
- **FREK Core** : 5 (ingest, frek/{id}, event/{id}/stats, ecosystem/pulse, admin/reload-rules) — phase d'amorcage CC2026
- **FREK Seal** : 2 (seal.js, seal/demo)
- Badges : 11 (14 types, lifecycle, batch)

## Phase amorcage CC2026 — Systeme nerveux souverain CVLN (12/05/2026, 18/18 + regression 274/274 OK)
- **Audit chirurgical prealable** : aucune collection ou route conflictuelle, clé Ed25519 verifiee inchangee post-livraison.
- **Module `core/`** isole, additif, namespace `/api/core/*` separe de `/api/v1/*`.
- **3 nouvelles collections** : `frek_subjects` (un doc/FREK-ID vivant), `frek_events` (timeline horodatable, idempotency_key unique), `frek_scoring_rules` (16 regles seedees a l'init, editables a chaud).
- **`POST /api/core/ingest`** : receveur souverain idempotent (sha256 frek_id|event_id|action|timestamp). Bearer token resout la source (kiltikonet/fms/kora) en temps constant via hmac.compare_digest. Defense-in-depth : body.source doit matcher le bearer. Badge inconnu = 422.
- **Cultural Impact Score** = `base_score(action, context=event_id)` + `bonus_score(badge_type)` — TOUJOURS lu depuis Mongo, **jamais hardcode**. Cache 60s + endpoint admin `/admin/reload-rules` (X-Admin-Key) pour rafraichissement immediat.
- **Squelette enrichment** : 5 champs (frek_subject_did, nominatif, jeton_cc_linked, nfc_badge_written, eudi_vc_issued) poses en `null` des la naissance — aucune migration future necessaire.
- **Idempotence forte** : Race condition Mongo geree (unique index + compensation atomique si double insert).
- **Endpoints lecture** : `GET /frek/{frek_id}` (profile + 100 derniers events, _id et idempotency_key filtres), `GET /event/{event_id}/stats` (agregations by_badge_type/by_source/avg_score/first&last_activation), `GET /ecosystem/pulse` (status ALIVE/DORMANT, sources actives 24h).
- **Tests Core** (12 directive + 6 supplementaires) : creation subject, idempotence, sources rejetees, bearer invalide, score from rules not hardcoded (verifie en modifiant une regle en live), score base+bonus, profile, 404, stats by_badge, pulse structure, badge inconnu 422, no regression ldp_vc, SD-JWT issuance/verify/partial/tamper, metadata declare 2 formats, Ed25519 inchangee.

## Phase 5 Cultural Fingerprint Layer — Livree (12/05/2026, 17/17 + regression 291/291 OK)
- **Module `fingerprint/`** isole, additif, namespace `/api/core/fingerprint/*`. Propriete exclusive CVLN Group.
- **7 couches** : cadence, affinity, device, social, anomaly, coupling, linguistic (stub).
- **Consentement segmente** : opt-in granulaire par couche. Revocation = purge effective des donnees (RGPD/AfCFTA).
- **Couche cadence** : statistiques sur frek_events (mean/median/stddev inter-event, histograms heure/jour, velocity 24h). Aucun stockage additionnel.
- **Couche affinity** : vecteur 64-dim par feature hashing deterministe (sign hashing trick). Cosinus pour matching. Aucune dependance ML lourde.
- **Couche device** : empreinte serveur (canvas/fonts/WebGL hash fourni par le client) avec pepper serveur. Detection automatique de collisions multi-FREK.
- **Couche social** : graphe de co-presence via event_id. Top-5 peers, centrality_score.
- **Couche anomaly** : detection bot (CV cadence) + collisions device. Seuils explicites (alert 0.5, block 0.85).
- **Couche coupling** : enregistrement NFC scan + verification web. Taux de couplage online/offline.
- **Couche linguistic** : stub propre (`available: false, reason: no_text_corpus_yet`).
- **Endpoints** : `/consent/{frek_id}` (GET/POST), `/observe/{device,nfc,web-verify}`, `/{frek_id}` (admin), `/match` (cosinus, admin, double consent), `/export/{frek_id}` (RGPD).
- **Tests** (17) : default opt-out, grant subset, revoke triggers purge, observe sans consent, observe avec consent, NFC -> web couples, admin gate, consent gates par couche, cadence computed, affinity vector normalise, match similar, match exige double consent, anomaly bot signal high (deterministe via Mongo direct), device collision, social copresence, export RGPD complet.
- **Invariants respectes** : zero PII civile, zero cookie tiers, zero ML lourd, Ed25519 inchangee, _id Mongo jamais expose, FREK ne connait pas l'identite civile, scoring autoritaire CVLN.

## Phase 4.6 SD-JWT VC — Livre (12/05/2026)
- **Module `eudi/sdjwt.py`** : format `vc+sd-jwt` (IETF draft-ietf-oauth-sd-jwt-vc-08+), **complement** de `ldp_vc` (jamais en remplacement).
- **Structure** : `<JWT>~<disclosure>~<disclosure>~...~`. JWT signe Ed25519 (alg=EdDSA, typ=vc+sd-jwt, kid=did:frek:frekcore#frek-passport-v1).
- **Disclosure selective native** : 6+ claims (currentStage, eventId, source, expiresAt, revoked, chainAnchor) chacun avec son nonce 16-bytes. Holder envoie un sous-ensemble — la signature reste valide, mode=`partial`.
- **Issuer metadata** declare les 2 configurations : `FrekCulturalIdentityCredential_jsonld` (ldp_vc) et `FrekCulturalIdentityCredential_sdjwt` (vc+sd-jwt) — wallets EUDI/Microsoft Authenticator decouvrent automatiquement.
- **POST /api/v1/eudi/credential/verify-sdjwt** : utilitaire serveur (la verif tourne aussi 100% offline avec la cle publique exposee dans /.well-known/jwks.json).
- **Cle Ed25519 reutilisee** : INVARIANT respecte, aucune regeneration, test dedie `test_ed25519_key_unchanged` qui compare le bytes du fichier `.passport_key.pem` avant/apres operations.

## Notes operationnelles
- Background loop ancrage OTS : submit toutes les 30s, upgrade BTC toutes les 30 min
- BTC confirmation : 1-6h apres soumission (gratuit)
- Calendars OTS configurables via env `OTS_CALENDARS` (defaut : 5)
- PWA offline-first : si reseau coupe, actions mises en file IndexedDB et rejouees au retour online
- Idempotence : `client_uuid` UUIDv4 genere cote client, persiste sur scans + transactions

## Audit technique — Test suite verte (06/05/2026)
- **pytest backend : 182/182 passed, 2 skipped, 0 failed (2:30)**

## Phase porteur — 3 pages utilisateur livrees (01/06/2026, frontend uniquement, 100% critical flows OK iteration_17)
- **Directive stricte respectee** : aucun fichier backend touche, aucune collection Mongo modifiee, aucune page existante alteree (App.jsx : ajout additif de 3 routes uniquement).
- **`/accueil`** (`pages/Accueil.jsx`) : vitrine plateforme (compteur anime total_events via `/api/core/ecosystem/pulse`, 3 chiffres CVLN evenements/oeuvres/participants, refresh 30s) + entree compte personnel (input FREK-ID -> redirige `/profil/{id}`, lien "Creer mon profil FREK" -> `/`). Statut pulse Plateforme active/dormante. Aucun melange avec donnees personnelles.
- **`/profil/:frek_id`** (`pages/Profil.jsx`) : compte neutre/personnel. Fetch parallele `/api/core/frek/{id}` + `/api/v1/identity/{id}/status` + `/api/core/fingerprint/consent/{id}`. Etat vide = sections lisibles ("Aucune presence encore — scannez votre premier badge", etc.). Etat rempli = 3 timelines classees FREK-P (presences) / FREK-O (oeuvres) / FREK-X (croisements). Badge "Profil culturel certifie" si au moins une couche fingerprint consentie. Boutons : telecharger passport.json (Ed25519) + ouvrir /verify. Compteurs strictement personnels. Aucun chiffre plateforme (40k, CC2026, masse) n'apparait.
- **`/scanner`** (`pages/Scanner.jsx`) : pointeuse FREK-P plein ecran, input auto-focus (compatible HID scanner). Resolution badge_id via `GET /api/badges/{badge_id}` public quand applicable, sinon traite l'entree comme FREK-ID brut. Queue localStorage `frek_offline_queue` (sync au retour reseau). Indicateur reseau en ligne/hors ligne. Confirmation "Presence enregistree" + compteur session locale + compteur plateforme separe (chiffres CVLN, jamais melanges aux personnels). Bouton vider la file.
- **Tests frontend** (iteration_17) : 100% flux critiques, 1 soft-violation corrigee (mention "CC2026" retiree de la copie /profil). Aucun bug UI, aucune regression sur /, /verify/:frekId, /dashboard, /scan/*. Tous les data-testids presents et uniques.
- **Endpoints consommes** (lecture seule, publics) : `/api/core/ecosystem/pulse`, `/api/core/event/CC2026/stats`, `/api/core/frek/{id}`, `/api/v1/identity/{id}/status`, `/api/core/fingerprint/consent/{id}`, `/api/v1/passport/{id}`, `/api/badges/{badge_id}`.

## Batch A — Visibilité & cohérence (07/06/2026, doctrine recadrée intégrée)
- **Liens nav `/atlas`** ajoutés aux footers Accueil, Profil, Scanner (additif, aucun fichier existant cassé).
- **Notarisation geo-située Bitcoin** — nouvel endpoint `POST /api/geo/notarize`. Crée un payload `{frek_id, geo:{plus_code, h3_9, h3_12, geohash_8, lat, lon}, satellite_witness:{eox_s2, nasa_gibs}, observation_at}` puis appelle `notarize_event(payload_type="geo_anchor")` du module notary existant (zero modification). Respecte le consent (403 si level=none). **Preuve curl : block #1260 ancré, hash `2d568ae60da877e1...`, payload réel sauvé en FREK-Chain et soumis à OTS Bitcoin.**
- **FREK Card v2** — tier visuel derivé du `cultural_impact_score` :
  - Bronze (0-49) · Argent (50-199) · Or (200-499) · Platine (500+) · Neuve (score null)
  - Gradient personnalisé par tier (cuivre / argent métallique / or doré / platine froide / cyan neuve)
  - `data-tier` exposé sur la carte pour test
  - Badge "Impact N" + badge "dernière activité" (relatif : "il y a 3 h", "à l'instant", "inactive")
  - Pulse emerald si activité < 24h (la carte "respire" sur le terrain, "dort" en sommeil)
  - Score & last_event_at calculés depuis `/api/core/frek/{id}` existant — aucun nouveau endpoint
- **Doctrine intégrée** :
  - Porteur = gratuit à vie, mécanique invisible
  - Pro = JCC uniquement, jamais Stripe direct
  - Comptage universel pour tout flux humain (présence, stream, formation, vote, NFC tap)
  - Batch C recadré : monétisation JCC tiers (pas free/pro/enterprise visible porteur)

## Phase 6 — Geo Layer souveraine (02/06/2026, backend + frontend, 13 preuves curl + ecran Atlas)
- **Module `geo/`** isole, additif, namespace `/api/geo/*`. Aucune cle, aucune dependance commerciale.
- **Stack souveraine** :
  - **Plus Code** (Open Location Code Apache 2.0, lib `openlocationcode==1.0.1`) — encodage 10/11 chars local.
  - **H3** (Uber Apache 2.0, lib `h3==4.5.0`) — hex spatial indexing res 9 (~175m) + res 12 (~7m).
  - **Geohash** (public domain, implementation locale) — precision 8 chars.
  - **Nominatim OSM** (free public, 1 req/s, User-Agent FrekCore declare) — reverse-geocoding avec cache H3 (5000 entrees).
  - **NASA GIBS** (MODIS Terra true color, gratuit no-auth, tuiles JPEG WMTS) — imagerie quotidienne 250m.
  - **EOX Sentinel-2 cloudless 2023** (gratuit, attribution CC-BY 4.0, WMS) — mosaique 10m.
  - **OpenStreetMap** (free public, attribution) — basemap.
- **Consentement segmente 4 niveaux** (`none` | `country` | `city` | `precise`) — opt-in par defaut, revocation = purge effective (RGPD/AfCFTA compliant).
- **Endpoints** (~9) : `POST /encode` (zero call externe), `GET/POST /consent/{frek_id}`, `POST /observe` (idempotent par hash sha256(frek_id|h3_12|minute)), `GET /trail/{frek_id}`, `GET /heatmap` (agregation H3 anonyme), `GET /satellite` (URL tuile gratuite), `GET /satellite/sources`.
- **Indexes Mongo** : `frek_geo_consent.frek_id` unique, `frek_geo_observations.idempotency_key` unique, `(frek_id, observed_at desc)`, `h3_9`.
- **Frontend** : nouvelle page `/atlas` (heatmap H3 + classement pays + imagerie satellite reelle Fort-de-France / Paris / Tokyo via boutons). `/scanner` enrichi avec toggle "Geo activee" (opt-in localStorage `frek_geo_enabled`), `navigator.geolocation.watchPosition` en arriere-plan, observation envoyee automatiquement avec chaque scan reussi.
- **Preuves curl reelles** (iteration en cours) :
  - Plus Code Fort-de-France `776WJW3R+F6` calcule en local
  - Nominatim reel : `{country:'France', region:'Martinique'}` pour (14.6037, -61.0594)
  - Nominatim reel : `{country:'France', region:'Île-de-France', city:'Paris'}` pour (48.8566, 2.3522)
  - EOX Sentinel-2 URL HTTP 200, JPEG 30KB reel
  - NASA GIBS URL HTTP 200, JPEG 12KB reel
  - Heatmap retourne 2 cellules + 1 pays + 2 observations 24h
- **Roadmap geo etendue** : ce module porte la **carte chaude mondiale** des presences FrekCore — fondation pour Atlas mondial, anchrage geo-situe sur FREK-Chain, et future certification par temoin satellite (couple `(plus_code, sentinel_tile, capture_date)` ancrable Bitcoin).

## Phase porteur v2 — FREK Card + Poste Staff + Theme clair (01/06/2026, frontend, iteration_19 100%)
- **Theme clair Certify-style applique partout** (`#f8fafc` + blobs cyan + cartes verre blanc) : Accueil, Profil, Scanner, Poste, Card. Coherence visuelle stricte avec page `/`.
- **FREK Card virtuelle nominative et individuelle a vie** (`components/FrekCard.jsx`) :
  - Carte premium gradient cyan, puce NFC visuelle, QR code (en plein ecran), horloge live (mise a jour seconde).
  - Nominative : prenom + nom recuperes de `/api/badges/?event=CC2026` (public) + type badge (BNV/VIP/ART...).
  - Classification IA-style : 3 compteurs FREK-P / FREK-O / FREK-X calcules a partir de `/api/core/frek/{id}.events`.
  - Status badge (ACTIF/REVOQUE/EXPIRE) + stage Luciole, lies a vie au FREK-ID immuable.
  - Integree dans `/profil/:frek_id` + page plein ecran dediee `/card/:frek_id` (partageable, accessible via QR).
- **Poste Staff `/poste`** (`pages/Poste.jsx`) :
  - Auth PIN staff via `POST /api/v1/staff/login` (reuse 100% infra existante).
  - Selecteur de zone unique pour toute la session (ENTREE par defaut, 7 zones).
  - Affichage temps reel de la file localStorage `frek_offline_queue` (refresh 5s).
  - Replay batch via `POST /api/v1/staff/scan/access` avec Bearer staff. Idempotent par `client_uuid` (le backend deduplique). Resultats OK / Skip / Erreur affiches en live, file purgee des entrees rejouees.
  - Bouton Stop pour interrompre, gestion 401 (session expiree -> auto-logout).
- **Scanner multi-modes universel** (`pages/Scanner.jsx`) :
  - **HID/clavier** : pistolets USB/Bluetooth, lecteurs RFID, USB-NFC (par defaut, auto-focus).
  - **Camera** : telephone QR/DataMatrix via `html5-qrcode` (dynamic import, lib deja en deps).
  - **Web NFC** : NDEFReader natif (Android Chrome). Bouton disabled "(indispo)" si non supporte.
  - Couvre ~100% de l'ecosysteme scanner mondial sans verrou materiel.
- **Pulse banner injecte dans `/` (Certify)** (`components/PulseBanner.jsx`) : indicateur "Plateforme vivante · X presences · Y FREK-IDs" cliquable, navigue vers `/accueil`. Aucune autre modification de Certify.jsx.
- **Endpoints supplementaires consommes** : `POST /api/v1/staff/login`, `POST /api/v1/staff/scan/access`. Aucun nouvel endpoint cree.
- **Tests frontend** (iteration_18 + iteration_19) : 100% des flux critiques apres correction d'un path endpoint (`/api/v1/scan/access` -> `/api/v1/staff/scan/access`). Aucune regression sur les pages existantes.

## Audit technique — Test suite verte (06/05/2026)
- **pytest backend : 182/182 passed, 2 skipped, 0 failed (2:30)**
- Migration tests vers `localhost:8001` (in-cluster) via `conftest.py` (purge `rate_limits` par session + per-test sauf TestRateLimit)
- Helper `_ensure_unique_sparse_index` resout IndexKeySpecsConflict + DuplicateKeyError sur null en utilisant `partialFilterExpression` au lieu de sparse
- Endpoints `/api/email/templates` et `/api/email/stats` exposent `ses_mode` + `total_sent` (alias)
- Tests admin passent maintenant le header `X-Admin-Key` (verifie SECRET_KEY)
- Tests PWA assets ciblent `localhost:3000` (frontend) au lieu du backend
- Test `anchor/upgrade` borne a `max_blocks=1` pour eviter timeouts CI


## Batch D — Heritage + Sync Baserow (21/06/2026)

### D.1 — FREK Heritage / Transmission (LIVRE)
- Module `heritage/` isole, additif, namespace `/api/v1/heritage/*`. Aucune modification des modules core.
- **Doctrine** : un FREK-ID est NOMINATIF et a vie. Lors d'un transfert (deces, donation, retraite, revocation), la lignee cryptographique est conservee — nouveau detenteur, mais historique immuable ancre sur FREK-Chain.
- **Securite** : zero PII en clair. Seul `sha256(email_beneficiaire)` + `sha256(claim_secret)` sont stockes. Le `claim_secret` (24 bytes urlsafe) est genere et retourne UNE seule fois au declarant.
- **Endpoints (6)** :
  - `POST /heritage/{frek_id}/declare` — declare un beneficiaire (auth client emit), retourne `claim_secret` a transmettre hors-bande.
  - `GET /heritage/{frek_id}` — affiche la declaration active (sans secret).
  - `DELETE /heritage/{frek_id}` — revoque la declaration.
  - `POST /heritage/claim` — le beneficiaire revendique (public, email + secret hors-bande). Transfere la propriete.
  - `POST /heritage/{frek_id}/transfer` — transfert force par le client (deces atteste, donation), conditionnel sur `manual` dans conditions.
  - `GET /heritage/lineage/{frek_id}` — lignee complete et publique (hash only), chain of custody.
- **Notarisation Bitcoin** : chaque `declare`, `revoke`, `transfer` = nouveau block sur FREK-Chain (payload_type=`heritage_declare`/`heritage_revoke`/`heritage_transfer`), automatiquement ancre via OpenTimestamps.
- **Preuves curl** (testees end-to-end) :
  - emit -> declare -> claim -> lineage : OK
  - bad claim_secret : rejete (403/404)
  - re-claim sur declaration deja consommee : rejete
  - blocks #1262 (declare) + #1263 (transfer) avec chain integrity (prev_hash) confirmes
- **Indexes Mongo** : `frek_heritage_declarations.declaration_id` unique, `(frek_id, active)`, `frek_heritage_transfers.transfer_id` unique.

### D.3 — Sync Baserow bi-directional (LIVRE, attente token utilisateur)
- Module `sync/` isole, additif, namespace `/api/v1/sync/*`. Aucune modification des modules core.
- **Doctrine** : FREKCORE est SOURCE OF TRUTH. Baserow est la couche operationnelle/CRM. Sync explicite (cron externe ou admin manuel), aucun hook auto sur les modules core.
- **Endpoints (5)** :
  - `GET /sync/baserow/status` — admin, cursor + compteurs.
  - `POST /sync/baserow/push/{frek_id}` — push une identite (create or update via mapping).
  - `POST /sync/baserow/push?limit=N&since=ISO` — push batch depuis cursor.
  - `POST /sync/baserow/pull?size=N` — pull rows Baserow, reconcilie le mapping.
  - `POST /sync/baserow/webhook` — webhook receiver Baserow, signature HMAC-SHA256 verifiee si `BASEROW_WEBHOOK_SECRET` defini.
  - `GET /sync/baserow/log` — admin, log des syncs.
- **Auth** : `X-Admin-Key: $SECRET_KEY` requis sur tous les endpoints sauf webhook (signature HMAC).
- **Collections** : `frek_sync_mapping` (frek_id <-> baserow_row_id), `frek_sync_log`, `frek_sync_cursor`.
- **Statut actuel** : code 100% pret. Le token Baserow actuel `BASEROW_TOKEN` retourne `401 ERROR_TOKEN_DOES_NOT_EXIST` — a regenerer cote utilisateur sur baserow.io (Account > Tokens).

### D.2 — SMTP frekcore.com (PARKED)
- Decision : option (c) SMTP direct via hebergeur du domaine frekcore.com (souverain, aucune dependance AWS/Resend).
- **En attente** : creds SMTP utilisateur (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM).
- **Plan a la reprise** : refactor `email_service/routes.py` SES -> `aiosmtplib`, conserver les templates Jinja2 et le mode fallback `logged`.


## RC v1.0 Sprint A+B — Vital security (08/07/2026)

### Sprint A — Backup + Persistence cle Ed25519 (LIVRE)
- **`/app/scripts/backup_frekcore.sh`** : mongodump + copie `.passport_key.pem` + `.env` + manifest.json + tar.gz + chiffrement GPG AES256 optionnel + retention 30j auto.
- **`/app/scripts/restore_test.sh`** : dechiffrement + extract + verif hash Ed25519 (MATCH avec live) + restore dans DB temporaire (`{DB_NAME}_restore_test_{ts}`) + verif 4 collections critiques + auto-cleanup.
- **`/app/scripts/backup_scheduler.py`** : daemon Python leger, execute par supervisor `frek_backup`. 03:00 UTC quotidien par defaut, configurable via `FREK_BACKUP_HOUR_UTC`.
- **`/etc/supervisor/conf.d/frek_backup.conf`** : autostart=true, autorestart=true.
- **Preuve E2E** : 1.8MB archive GPG AES256, restore complete 1097 frek_identities + 1446 frek_stages + 1263 notary_blocks + 156 frek_clients + Ed25519 sha256 MATCH.

### Sprint B — Health probes + Admin backup ops (LIVRE)
- **Module `health/`** additif, namespace `/api/v1/health/*` + `/api/v1/admin/backup/*`.
- **`GET /health/live`** : liveness K8s probe (repond toujours).
- **`GET /health/ready`** : readiness K8s (verifie Mongo ping).
- **`GET /health/deep`** : sante complete 6 checks (Mongo count, Ed25519 sha256/mode/size, disk, memory RSS, notary chain integrity, last backup) + uptime + status agrege.
- **`GET /admin/backup/status`** (X-Admin-Key) : liste archives + last backup metadata + script presence.
- **`POST /admin/backup/trigger`** (X-Admin-Key, optional `gpg_passphrase`) : declenche backup a la demande.
- **`POST /admin/backup/restore-test/{archive}`** (X-Admin-Key) : verifie qu'une archive est reellement restaurable.
- **Preuve HTTP** : trigger backup -> restore-test -> Ed25519 MATCH -> 1263 blocks OK, tout via curl HTTP end-to-end.

### Documentation
- **`/app/memory/RUNBOOK.md`** : procedure complete backup + restore + urgence + monitoring externe (UptimeRobot, Better Stack, cronjob.org) + alertes critiques + checklist RC v1.0.

### Reste Semaine 1 (action user)
- 🟠 Configurer `BACKUP_GPG_PASSPHRASE` dans supervisor conf (recommande prod).
- 🟠 Configurer UptimeRobot / Better Stack sur `/api/v1/health/live` + `/health/deep`.
- 🟢 (Optionnel) Sentry FastAPI pour auto-capture exceptions.


---

## PHASE 9 — Production Live (08/07/2026)

### Fin des phases "prototype" et "MVP"
Doctrine actee par le fondateur : FREKCORE est desormais en **production live**.
Tout nouveau developpement suit un standard production (audit, tests, monitoring, backup).
Aucun ajout futur ne sera qualifie de "prototype" ou de "MVP".

### Fenetre d'acces publique #1 — "Signer le moment present" (LIVRE)

**Doctrine** : le bouton est **la porte**, pas le batiment.
Le cœur FREKCORE reste inchange (E/F/G valides). On revele la puissance existante via une porte grand public simple.

**Backend** — module `moment/` additif :
- `POST /api/v1/moment/sign` : anonyme, sans auth, un tap. Cree FREK-ID + block notarise (payload_type=`moment_signed`) + passport recuperable. Multi-couches (timestamp defaut / geo opt-in / audio / image / titre / temoins).
- `GET /api/v1/moment/mine?session_id=X` : liste les moments d'une session anonyme.
- `GET /api/v1/moment/stats` : compteur public.
- Rate limit **20 signatures/h/IP** (hash IP+day, aucune IP stockee).
- Session anonyme cote client : `localStorage.frek_moment_session` (UUID v4).
- Identifiants "moment" prefixes : `m-{6hex}-{4hex}` (distinguable des FREK-IDs classiques).

**Frontend** — 2 pages production :
- `/` : `Moment.jsx` — landing radicale, 1 bouton "SIGNER", options discretes (titre / geo checkbox), ecran preuve avec block_hash + passport + QR.
- `/mine` : `MyMoments.jsx` — historique local + prompt "conserver ton univers" apres 3 moments.
- Ancienne landing accessible sur `/certify` et `/manifeste`.

**Identite progressive** (3 paliers) :
- Palier 1 : FREK-ID anonyme, session localStorage LIVE
- Palier 2 : attach email/passkey (bouton "bientot" visible, deblocage a la demande)
- Palier 3 : espace pro (a construire quand un partenaire le demande)

**Preuves E2E** :
- Backend curl OK : `POST /moment/sign` retourne frek_id + block_hash + proof_url + passport_url + verify_url + layers_captured
- Frontend E2E OK : click SIGNER → ecran preuve visible + 3 boutons
- Chain integrity : height=1313, valid=True
- 8/8 endpoints critiques HTTP 200


---

## PHASE 10 — Multimédia réel minimal (08/07/2026)

### Étape 2 de la cascade "signal réel → décision → construction"
Suite à P0 (validation visuelle blanc/bleu ✅), livraison de l'étape 2 : le premier moment
signable avec un vrai fichier (photo prioritaire, audio en secondaire).

### Bug fixé
- **Routage `/manifeste`** : `App.jsx` routait `/manifeste` vers `<Certify />` (ancienne UI cyan/dark)
  au lieu de `<Manifeste />` (v1.0 blanc/bleu). Corrigé, page importée et route mise à jour.

### Backend — module `moment/` étendu

**Nouveaux endpoints** :
- `POST /api/v1/moment/sign-media` (multipart) : signe un moment avec fichier joint (photo ou audio).
  - `store=false` → hash SHA-256 seul, aucun binaire conservé (pur notaire).
  - `store=true` → hash + fichier stocké dans Object Storage (encrypté au transit), récupérable via `/moment/media/{frek_id}`.
  - Types autorisés : `image/{jpeg,png,webp,gif}`, `audio/{mp3,wav,webm,ogg,mp4,aac,flac}`.
  - Taille max : 15 MB.
- `GET /api/v1/moment/media/{frek_id}` : récupère le binaire stocké (404 si `store` était `false` ou expiré).
- `GET /api/v1/moment/detail/{frek_id}` : renvoie metadata publique safe (titre, hash, kind, layers, block).

**Modifications** :
- `_sign_moment_core()` extrait comme helper partagé entre `/sign` (JSON) et `/sign-media` (multipart) — refacto sans changement de comportement pour la route JSON existante.
- `SignMomentResponse` étendue avec `media_hash`, `media_kind`, `media_stored`, `media_url`.
- Layer `media_kept` ajoutée quand fichier stocké.

**Intégration Object Storage Emergent** :
- Module `moment/storage.py` : wrapper minimal (`init_storage`, `put_object`, `get_object`, `validate_media`).
- Init au startup best-effort, mode dégradé silencieux si `EMERGENT_LLM_KEY` absent (le hash reste ancré).
- Path convention : `frekcore/moments/{frek_id}.{ext}`.

### Frontend

**Refonte `Moment.jsx` (`/`)** :
- Boutons `+ Photo` et `+ Son` sous le hero.
- Preview miniature dès sélection (thumbnail image OU icône audio + nom + taille).
- Choix explicite après sélection :
  - **Signer seul · hash uniquement** (bouton discret) — ton fichier reste chez toi.
  - **Signer et conserver** (bouton principal, sombre) — fichier chiffré stocké, récupérable via ta preuve.
- Ecran de preuve enrichi : ligne "Empreinte photo/audio" + message conservation.
- Erreurs inline (fichier trop lourd, format non supporté).

**Nouvelle page `MomentVerify.jsx`** (route `/verify/m-*`) :
- Détection automatique dans `Verify.jsx` : les IDs préfixés `m-` (public window) sont routés vers cette UI blanc/bleu ; les IDs stage-based FREK-v1 restent sur l'ancienne UI dark.
- Structure exacte demandée par le fondateur :
  - Badge `✓ Moment attesté`
  - FREK-ID (mono)
  - Titre (optionnel, entre guillemets français)
  - Date de signature
  - Lieu (si geo capturée)
  - Empreinte vérifiable (block Bitcoin)
  - Empreinte photo/audio (media_hash)
  - Couches capturées (badges)
  - Actions : `[Voir aperçu]` (fetch blob, affiche image OU `<audio controls>`) + `[Télécharger l'original]`
- Aucun lecteur riche : structure "page de preuve avant page média".

### Tests E2E validés (curl + Playwright)
| Test | Résultat |
|---|---|
| Regression `/sign` JSON | ✅ 200 OK, media_hash null |
| `/sign-media` hash-only PNG | ✅ 200, layer=[timestamp,image,context], stored=false |
| `/sign-media` store=true PNG | ✅ 200, layer includes media_kept, stored=true |
| `GET /media/{id}` | ✅ 200, binaire identique à l'upload (diff -q OK) |
| `POST /sign-media` avec text/plain | ✅ 400 "Type non supporte" |
| `GET /detail/{id}` | ✅ block_hash lié, media metadata complète |
| Frontend `/` : Photo picker → preview → sign+keep → done | ✅ E2E complet |
| Frontend `/verify/m-*` : detail rendu + aperçu → download | ✅ complet |

### Ce qui n'est **pas encore** livré (parties 3-6 de la cascade)
- Audio live capture (micro navigateur, 60s max) — priorité 3, arrivera après scénarios musique/culture réels
- Fix du 500 legacy `/api/frek/certify` (route audio ancienne page `/certify`, indépendante du nouveau flow)
- Passkey / WebAuthn (Palier 2 identité) — bloqué sur signal réel
- Multi-tenant B2B (Sprint M') — bloqué sur signal partenaire


---

## PHASE 15 — Branchement des briques (08/07/2026)

### Doctrine appliquée
> Ne pas ajouter de concepts. Ne pas refaire l'architecture. Brancher proprement les briques existantes.

### Ce qui a été branché

**Backend — Auto-link identity via `X-FREK-Session`**
- `POST /moment/sign` : accepte header optionnel `X-FREK-Session`. Si token valide → moment auto-ajouté à `frek_persons.linked_objects[]` de l'identity correspondante.
- `POST /moment/sign-media` : idem, header optionnel.
- `POST /fk/create` : idem, header optionnel.
- Rétrocompatibilité totale : sans token, comportement inchangé (moment/fk anonymes).
- Token invalide : skip silencieux du link, la signature réussit quand même.

**Frontend — Envoi automatique du token**
- `Moment.jsx` : `X-FREK-Session` injecté sur `/sign` et `/sign-media` si présent dans localStorage.
- `FK.jsx` : `X-FREK-Session` injecté sur `/fk/create` si présent.
- `MyMoments.jsx` : refonte pour afficher l'univers **unifié** — si identity protégée détectée, fetch `/api/v1/identity/{id}/objects` qui renvoie moments + FK ensemble ; sinon fallback anonyme `moment/mine?session_id=X`.
- Nouveau CTA `/mine` : "Protéger cet univers →" (link vers `/identity`) dès 1 moment signé, pour convertir l'utilisateur anonyme en univers persistant.

### Bugs corrigés en passant
- Cache Vite stale sur MyMoments.jsx après purge deps (l'import axios n'existait plus en réel mais le cache le montrait)
- Duplicate JSX return orphelin après refonte du composant (tronqué à 210 lignes propres)

### Flow utilisateur final "un geste → une preuve durable" (Priorité 3)
1. Utilisateur arrive sur `/`
2. Signe (avec ou sans photo/audio) → moment `m-*` créé + block FREK-Chain
3. Voit `/mine` → prompt "Protéger cet univers" si ≥1 moment
4. Va sur `/identity` → clique "Associer une Passkey" → Touch ID / Face ID → protégée
5. `session_token` stocké → tous les prochains `/moment/sign` et `/fk/create` sont **automatiquement liés** à son FREK-Identity
6. Sur autre appareil : `/identity` → "Retrouver votre univers" → Passkey → retrouve moments + FK
7. Chaque objet FK peut être vérifié offline via son fichier `.fk` (Ed25519 embarqué)

### Ce qui reste dans le backlog (aucun code avant signal)
- Namespaces DID (`did:frek:user/artist/label/institution:*`) — structure prête, non exposée
- Community graph (relations inter-FREK-IDs)
- Organizational identity (membres, permissions)
- CLI FK autonome
- FREKANSLA intelligence layer (fingerprint)
- Import ID3/EXIF/XMP
- Page publique `/spec/fk` (charte visible) — spec déjà rédigée dans `/app/memory/FK_CULTURE_SPEC_v1.0.md`


---

## PHASE 14 — Freeze v1.0 Production (08/07/2026)

### Décision fondateur
> "Il faut tout figer sans sur-architecturer et sur-construire et rendre tout production live donc que ça fonctionne réellement."

### Actions livrées

**1. Deployment audit (deployment_agent)** — status WARN, aucun blocker critique :
- ✅ Compilation OK, env files OK, CORS OK, URLs via env only, supervisor OK, no dotenv override
- Warnings uniquement sur deps ML/PostgreSQL inutilisées → purgées

**2. Purge deps inutilisées** — 11 packages retirés de requirements.txt (0 import réel confirmé) :
- ML : `librosa`, `numba`, `llvmlite`, `scikit-learn`, `scipy`, `soundfile`, `tiktoken`, `tokenizers`, `huggingface_hub`
- DB legacy : `psycopg2-binary`, `pgvector`, `SQLAlchemy`
- Impact : image plus légère, boot plus rapide, plus de risque de resource limit sur Kubernetes

**3. Dead code cleanup (identity_engine)** — Recommandations testing_agent iteration_21 appliquées :
- Retrait de la classe `LinkObjectRequest` orpheline
- Retrait de la branche unreachable `if req.identity_type not in IDENTITY_TYPES` (Pydantic Literal valide déjà avant handler)

**4. Smoke health final** — 6/6 endpoints critiques HTTP 200 :
- `/api/v1/health/deep` ✅
- `/api/v1/moment/stats` ✅
- `/api/v1/fk/stats` ✅
- `/api/v1/fk/pubkey` ✅
- `/api/v1/spec/` ✅
- `POST /api/v1/identity/authenticate/begin` ✅

### État figé v1.0 Production

**Modules backend live** (11) : moment, fk, identity_engine, notary (FREK-Chain + Bitcoin OTS), passport (Ed25519), spec, health, heritage, sync, staff, event, badges, jetons, email_service, frek_v1 (Luciole)

**Modules frontend live** (routes) : `/` (Moment), `/mine`, `/fk`, `/identity`, `/verify/:id`, `/spec`, `/manifeste`, `/philosophy`, `/dashboard` (ops), `/proof/:hash`, `/explorer`, `/atlas`, `/accueil`, etc.

**Intégrations live** :
- ✅ FREK-Chain notarisation (locale, souveraine)
- ✅ Bitcoin OpenTimestamps (background daemon)
- ✅ Object Storage Emergent (photos/audios/FK signés)
- ✅ WebAuthn Passkey (native navigateur, aucune biométrie stockée)
- ✅ Stripe Checkout (jetons B2B, restricted live key)
- ✅ AWS SES (email templates ready, verification SES sandbox pending user)
- ⚠️ Baserow (token expiré côté user)

**Ce qui reste dans le backlog gouverné par signal réel** — aucun code écrit avant qu'un signal ne le déclenche :
- Community Graph (relations FREK-ID)
- Trust Bridge externe (OAuth/DID)
- Organizational identity (professional multi-membres)
- Institutional API keys
- CLI FK autonome
- FREKANSLA fingerprint pipeline
- Import auto ID3/EXIF/XMP
- Bitcoin OTS spécifique .fk (block FREK-Chain suffit)

### Doctrine finale gelée

> "FREKCORE crée l'infrastructure de preuve culturelle.
> FK est le format qui permet aux créations numériques de transporter leur identité, leur histoire et leur preuve à travers le temps.
> FREKCORE ne crée pas des comptes. FREKCORE protège des identités culturelles."

**Signal → Décision → Construction.** Rien ne s'ajoute avant qu'un besoin réel ne le déclenche.


---

## PHASE 13 — Identity Engine (Passkey / WebAuthn) (08/07/2026)

### Décision fondateur

Diagramme validé :
```
FREK-ID (identité souveraine)
   ├── Passkey (WebAuthn — preuve de contrôle)
   ├── FK Objects (.fk)
   └── Community Graph (futur)
```

Principe : *"FREKCORE ne crée pas des comptes. FREKCORE protège des identités culturelles."*

### Livré

**Backend** — module `/app/backend/identity_engine/` :
- `models.py` — `FREKIdentity` (id `id-{12hex}-{4hex}`, type individual/professional/institution, status anonymous/protected/revoked, credentials[], linked_objects[], linked_sessions[], permissions[], metadata)
- `service.py` — WebAuthn ceremonies (registration + authentication) via `webauthn` v3.0.0, session tokens HMAC-signés stateless (90 jours)
- `routes.py` — 8 endpoints :
  - `POST /identity/init` — bootstrap FREKIdentity anonyme (attache session_id existant)
  - `POST /identity/{frek_id}/register/begin` — options Passkey (challenge, rp, user, pubKeyCredParams)
  - `POST /identity/{frek_id}/register/complete` — verify + attach + issue session
  - `POST /identity/authenticate/begin` — challenge username-less (discovery)
  - `POST /identity/authenticate/complete` — verify assertion + issue session
  - `GET /identity/me` — via header `X-FREK-Session`
  - `GET /identity/{frek_id}` — vue publique safe (jamais de credentials en clair)
  - `GET /identity/{frek_id}/objects` — moments + FK liés (protégé)
  - `POST /identity/link-object` — attache un FK/moment à l'identité

- Nouveau env var **`FREK_RP_ORIGIN`** — WebAuthn requiert un rpId cohérent avec l'origin. Sans ça, ceremony échoue (rpId=localhost mismatch).
- MongoDB collections : `frek_persons`, `frek_persons_challenges` (TTL 5 min)

**Frontend** — route `/identity` (blanc/bleu v1.0 minimaliste institutionnel) :
- 3 états AnimatePresence : **anonymous** ("Votre univers existe" + bouton Associer Passkey + lien "Retrouver univers") → **ceremony** (loader biométrique) → **protected** ("Votre identité FREK est maintenant protégée" + FREK-ID + stats + CTA)
- Helpers `b64urlToBuf`, `bufToB64url`, `serializeCredential` pour la ceremony WebAuthn côté navigateur (native `navigator.credentials.create/get`)
- localStorage : `frek_identity_token` (session HMAC), `frek_identity_id`
- Sign out / add multiple Passkeys / recover (auth username-less avec discovery)

### Ce qui n'est PAS livré (structure prête, endpoints stubs pour plus tard)

- ❌ Multi-membres organizational identity (structure `identity_type=professional` prête, pas d'endpoint /organization)
- ❌ Institutional API keys (structure `identity_type=institution` prête, pas d'endpoint)
- ❌ Trust Bridge externe (OAuth/DID/SSO) — architecture prévue, pas construite
- ❌ Community Graph (relations entre FREK-IDs) — non implémenté

### Compatibilité doctrine

- ✅ Aucun compte email/password
- ✅ Aucune dépendance Google
- ✅ Aucun réseau social ni marketplace
- ✅ Aucun stockage biométrique (uniquement credential public COSE)
- ✅ FREK-ID reste l'identité — Passkey = mécanisme de contrôle
- ✅ Séparation identité / objet culturel
- ✅ Architecture multi-acteurs prête pour extensions futures

### Signaux réels attendus pour la suite

| Signal | Déclenchera |
|---|---|
| 1er label crée son identité professionnelle | Endpoints `/organization` + membres/permissions |
| 1er musée / institution demande une clé API | Endpoints `/institution/api-keys` + gouvernance |
| 1er cas de collaboration inter-FREK-IDs | Community Graph (relations, événements, transmissions) |
| 1re demande d'auth externe (SSO entreprise) | Trust Bridge OAuth/DID |


---

## PHASE 12 — FK Implementation MVP v0.1 (08/07/2026)

### Signal validé et implémentation démarrée

Décision fondateur : "On implante." Trio verrouillé :
- **FREKANSLA** = création intelligente
- **FK Culture** = objet culturel transportable
- **FREKCORE** = confiance et continuité

Cadrage précis intégré :
- Endpoint `/fk/create` (pas `/pack`) — vocabulaire orienté objet culturel
- **Exporter votre objet culturel FK** (pas "télécharger une archive")
- Architecture prévoit les **7 couches dès v0.1**, `intelligence/` réservée pour FREKANSLA
- **Test de survie** intégré : un `.fk` doit rester vérifiable sur toute machine, sans DB

### Backend — module `/app/backend/fk/` (livré)

- `models.py` — Pydantic strict pour les 7 couches (manifest, identity, creators, timeline, media, intelligence, rights, proof)
- `packager.py` — création complète : FREK-ID `fk-{12hex}-{4hex}`, notarisation FREK-Chain, signature Ed25519 (clé passport réutilisée), assemblage ZIP conforme spec
- `validator.py` — vérification **offline** : ZIP valid, couches présentes, hashes recalculés, root_hash, signature Ed25519 avec clé publique embarquée, intégrité binaire de chaque média
- `routes.py` — 6 endpoints publics :
  - `POST /api/v1/fk/create` (multipart : métadonnées + médias, jusqu'à 100 MB / 20 items)
  - `POST /api/v1/fk/verify` (upload `.fk` → rapport détaillé)
  - `GET /api/v1/fk/detail/{frek_id}` (metadata publique safe)
  - `GET /api/v1/fk/{frek_id}/download` (si conservé côté serveur)
  - `GET /api/v1/fk/stats` (compteur public)
  - `GET /api/v1/fk/pubkey` (clé publique FREKCORE pour vérif tiers)

### Frontend — route `/fk` (livrée)

- Tabs "Créer un objet FK" / "Vérifier un .fk", theme blanc/bleu v1.0
- Formulaire création : titre, type (9 catégories : song, album, event, captation, photo, artwork, heritage, document, other), créateur, description, multi-upload médias, toggle "Conserver une copie chiffrée côté FREKCORE"
- Après création : affichage attestation complète (FREK-ID, root_hash, block, size, media count) + bouton **"Exporter votre objet culturel FK"** (download direct)
- Vérification : drop zone → rapport valide/invalide + détail des 15+ contrôles

### Tests (100% verts)

- `test_create_fk_minimal` ✅
- `test_create_fk_with_media` ✅
- **`test_survival_offline_verification`** ✅ (test fondamental : identité intacte après oubli complet)
- `test_tampering_detected_manifest` ✅ (modification manifest → invalidité détectée)
- `test_tampering_detected_media` ✅ (modification média → invalidité détectée)
- `test_canonical_json_deterministic` ✅ (hashes stables)
- `test_frek_id_prefix` ✅ (distinction fk- / m- / stage-based)

### Bug fixé pendant l'implem

- **Ordre de scellement** : la première version calculait `layer_hashes` AVANT que `manifest.attestation_ref.block_hash` soit renseigné → le manifest écrit dans le ZIP différait du manifest hashé → validation échouait. Réordonnance : notariser d'abord, renseigner `attestation_ref` sur le manifest, PUIS calculer les hashes.

### Ce qui n'est PAS livré (aligné cadrage fondateur)

- ❌ Codec audio
- ❌ Lecteur média
- ❌ Blockchain complète (FREK-Chain souverain existant suffit)
- ❌ Stockage massif (Object Storage existant + hash externes suffisent)
- ⏳ Génération fingerprint audio (chromaprint / BPM / spectral) — attend FREKANSLA
- ⏳ Import auto métadonnées natives (ID3, EXIF, XMP) — reporté
- ⏳ Ancrage Bitcoin OTS spécifique `.fk` (block FREK-Chain suffit en v0.1)
- ⏳ CLI Python autonome — l'API HTTP suffit

### Impact stratégique

Le jalon philosophique est atteint :
> "Pour la première fois, une création numérique peut devenir un objet culturel portable, identifiable et attestable."

Chaque acteur (artiste, label, musée, archive) peut désormais :
1. Créer un `.fk` via `/fk` ou l'API
2. L'échanger comme n'importe quel fichier
3. Le vérifier sans dépendre de FREKCORE (Ed25519 embarqué + hashes recalculables)

Prochains signaux réels qui débloqueront la suite :
- Un artiste demande `song.fk` en usage réel → CLI + intégration DAW
- Un musée demande archivage `heritage.fk` → procédure long terme
- Un partenaire signataire → intelligence layer via FREKANSLA


---

## PHASE 11 — FK Specification v1.0 (Cultural Object Container) (08/07/2026)

### Signal stratégique du fondateur — cadrage définitif

Discussion en session : FK **n'est pas un format audio**. FK = **Cultural Object Container** — un conteneur narratif et probatoire léger, qui ajoute la couche de mémoire et d'identité autour de médias existants sans les remplacer.

### Phrase de positionnement officielle (RDV investisseurs / partenaires)

> "FREKCORE crée l'infrastructure de preuve culturelle. FK est le format qui permet aux créations numériques de transporter leur identité, leur histoire et leur preuve à travers le temps."

### Principe fondateur

> Les formats existants transportent les médias. FK transporte leur sens.
> FK doit fonctionner comme Markdown : petit fichier, grande capacité de narration.

### Livrables (documents — pas de code)

- **`/app/memory/FK_CULTURE_SPEC_v1.0.md`** — Spec technique complète (15 sections + 2 annexes)
  - Extension `.fk` — MIME `application/vnd.frek.culture+zip`
  - Conteneur ZIP-based (précédents EPUB, USDZ, OOXML)
  - 7 couches : `manifest.fk.json` + `metadata/` (identity, creators, timeline) + `media/` + `intelligence/` (fingerprints, analysis, signatures) + `rights/` + `proof/`
  - Deux modes : FK léger (~1-50 Ko, médias référencés) et FK autonome (embarque tout)
  - Bidirectionnel : import (WAV, MP4, PDF, IMAGE, DATA → FK) et export (FK → WAV, MP3, STEMS, VIDEO, ARCHIVE)
  - Vérification offline (recalcul hashes + signature Ed25519 avec clé `.well-known`)
- **`/app/memory/FK_CULTURE_PUBLIC_CHARTER.md`** — Charte publique (~2 pages) pour publication `/spec/fk` et distribution en RDV

### Répartition FREKANSLA / FREKCORE clarifiée

- **FREKANSLA** = laboratoire créatif → produit du FK (couche `intelligence/`)
- **FREKCORE** = infrastructure de preuve → signe (couche `proof/` + FREK-Chain + BTC optionnel)

### 4 cas d'usage prioritaires (produits FK cibles)

- **Musique** : `song.fk` = œuvre + auteurs + versions + preuve
- **Label** : `album.fk` = masters + crédits + droits + évolutions
- **Festival** : `event.fk` = performances + artistes + médias + témoignages
- **Patrimoine** : `heritage.fk` = origine + histoire + transmission

### Roadmap technique (aucun code écrit avant signal réel)

Ordre d'implémentation quand un signal déclenchera :
1. Modèle FK JSON (JSON Schema draft 2020-12)
2. Générateur FK (Python/JS)
3. Validateur FK
4. Import média existant (WAV/MP4/PDF/IMAGE)
5. Génération fingerprint (chromaprint / spectral / BPM)
6. Connexion API FREKCORE (signature + block)
7. Export `.fk`

### Ce qui ne sera **pas** construit

- ❌ Codec audio
- ❌ Lecteur média
- ❌ Blockchain complète (FREK-Chain souverain existant suffit)
- ❌ Stockage massif (Object Storage existant + références externes suffisent)

### Politique de diffusion (aligné IP Protection Strategy)

- **Public** : vision, définition, cas d'usage → charte téléchargeable + page `/spec/fk`
- **NDA partenaire** : structure conteneur, schémas JSON, roadmap technique
- **Vault interne** : clés Ed25519, seeds, procédures de rotation

### Signaux réels qui déclencheront l'implémentation

| Signal | Déclenchera |
|---|---|
| 1er artiste demande export `song.fk` | Générateur FK v0.1 + CLI Python |
| 1re institution demande vérification | Endpoint `/api/v1/fk/verify` + page publique |
| 1er DAW accepte l'intégration | SDK Python/JavaScript |
| 1er musée demande archivage | Procédure long terme + audit |
| 1er label demande `album.fk` | Schéma multi-pistes + interface batch |

### Impact stratégique

FK élargit le marché adressable de FREKCORE de "notaire audio" à **notaire culturel universel**. Le vecteur d'adoption devient un **format qui circule**, pas une infrastructure à convaincre à chaque fois. Publics touchés : artistes, labels, musées, archives, institutions, ayants droit, notaires, distributeurs, chercheurs.


---

## PHASE 16 — Univers unifié + logo cliquable + Passkey iframe fix (08/07/2026)

### Doctrine appliquée
> Un utilisateur ne doit plus percevoir plusieurs applications séparées.
> FREK-ID reste l'identité universelle. Les profils d'usage sont un choix d'expérience, pas des comptes.

### Livré

**Phase 0 — Audit obligatoire** (aucun code écrit) :
- Cartographié `identity_engine`, `moment`, `fk`, `MyMoments.jsx`.
- Confirmé : auto-link `X-FREK-Session` déjà en place sur `/moment/sign`, `/sign-media`, `/fk/create`.
- Confirmé : `identity_type` supporte déjà `individual/professional/institution` (Pydantic Literal).
- ✅ Zero nouveau endpoint backend, zero nouvelle collection Mongo, zero nouveau système d'auth.

**Phase 1 — `/universe` (porte d'entrée unique)** (`pages/Universe.jsx`, alias `/create`) :
- Hero "Bienvenue dans votre univers FREKCORE".
- 4 étapes visuelles (Créer/retrouver FREK-ID → Passkey → Objets → Patrimoine) avec statut done/ready/locked calculé côté client via `/identity/me`.
- 5 profils d'usage (Artiste/Institution/Professionnel/Organisation/Personnel) → `localStorage.frek_universe_profile` + mapping `identity_type` sur `/identity/init` existant.
- Panneau état identité (FREK-ID + Passkey + compteurs moments/FK).

**Phase 2 — `/mine` en "Mon Univers"** (`pages/MyMoments.jsx`) :
- Headline "Mon univers." (au lieu de "Ton univers.").
- Nouveau panneau `mine-identity-panel` (FREK-ID + Passkeys + niveau souverain).
- Legal notice footer.

**Phase 3 — Profil d'usage** : sélecteur non-invasif via `universe-profile-picker`, 5 choix mappés sur les 3 `identity_type` backend existants.

**Phase 4 — Positionnement FK** : titre écran de succès "Objet culturel vérifiable." + tagline expliquant que FK n'est pas une archive technique.

**Phase 6 — Messaging légal recadré** : suppression des "certifie la vérité" ; ajout partout de "FREKCORE atteste l'existence, l'intégrité et l'origine déclarée d'un objet numérique." (footers /universe, /mine, /manifeste, /fk, /verifier). Manifeste précise : "Nous ne remplaçons ni un juge ni un notaire d'État."

**Logo brand cliquable** (`components/BrandLogo.jsx`) :
- Composant réutilisable, logo `/frek-logo.png` seul (sans wordmark par défaut, sur demande fondateur).
- Bouton `<Link>` vers `/universe` (canonical hub) sur toutes les pages v1.0 : Universe, Moment, MyMoments, Identity, FK, Manifeste, Spec, Explorer, Philosophy, MomentVerify, Verifier.
- Micro-animation : scale + rotate au hover, active-shrink.

**Fix `/verifier` (page blanche "Accessible ici")** (`pages/Verifier.jsx`) :
- Route interne `/verifier?lang={python|js}` qui rendait un `text/x-python` brut → blanc dans certains navigateurs / iframes.
- Aperçu code monospace, boutons "Télécharger" + "Copier" + tabs Python/JavaScript + README.
- Consomme les endpoints existants `/api/v1/passport/verifier/{python,js,readme}` sans les modifier.
- `Spec.jsx` et `PassportPanel.jsx` pointent désormais vers `/verifier`.

**Fix Passkey "Passkey annulée" instantané** (`identity_engine/service.py` + `pages/Identity.jsx`) :
- Detection iframe cross-origin + mismatch domaine côté frontend → bandeau `identity-iframe-warning` + bouton "Ouvrir dans un nouvel onglet".
- Vérification pré-ceremony dans `register()` et `authenticate()` : bloque le prompt avant qu'il n'échoue.
- Backend : **suppression du fallback silencieux `localhost`**. `get_rp_id()` / `get_origin()` lèvent `WebAuthnConfigError` si `FREK_RP_ORIGIN` manquant.
- Nouveau helper `rp_config_status()` + log startup explicite (rp_id + origin visibles au boot).
- Preuve boot : `Identity Engine RP: rp_id=culture-chain.preview.emergentagent.com origin=https://culture-chain.preview.emergentagent.com`.

### Ce qui n'a PAS été touché (doctrine "signal réel")
- Community Graph, Trust Bridge OAuth/DID, Organizational multi-membres, Institutional API keys, CLI FK, FREKANSLA fingerprint : structure `identity_type=professional/institution` déjà en place, aucune UI construite avant signal réel.

### Preuves fonctionnelles
- `/universe` charge, hero + 4 étapes + profil picker OK.
- `/verifier` affiche code Python et JS avec download/copy — plus de page blanche.
- `/identity` : état anonymous visible, FREK-ID `id-XXXXXXXX-XXXX`, bouton Passkey présent + bandeau iframe warning affiché uniquement quand nécessaire.
- `/` : logo seul (sans wordmark) + nav Univers/Manifeste/Spec/Explorer.
- Backend startup log confirme RP config exact.

