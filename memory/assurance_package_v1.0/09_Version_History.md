# 09 — Version History

**FREKCORE Assurance Package v1.0** — Document 09
**Version** : 1.0.0-rc
**Date** : 2026-07-08

---

## 1. Repère chronologique

- **Repository créé** : 2026-02-05 (`c925674 Initial commit`)
- **Dernière modification** : 2026-07-08 (`b83d1a8`)
- **Commits totaux** : 172
- **Durée de développement** : 5 mois (Feb 2026 → Jul 2026)

---

## 2. Phases de construction

### Phase 1 — Fondations (Feb 2026)
- Initialisation FastAPI + React + MongoDB
- Premiers endpoints identité
- Concept Luciole (11 niveaux → 5 stades GENESIS/EVIDENCE/BINDING/PROOF/LEGACY)
- Auth OAuth2 client_credentials

### Phase 2 — CC2026 core (Feb-Mar 2026)
- Modules `badges/`, `jetons/`, `event/`, `email_service/`
- PWA scanner staff (`/poste`)
- Stripe checkout (couche Kiltikonet)
- AWS SES intégration (fallback log)
- Dashboard CC2026 (`/dashboard`, accès ops footer discret)

### Phase 2.5 — Security hardening
- bcrypt cost 12 sur staff PIN
- Rate limits sliding window (100/h emit, 5 tentatives login, 300/min IP)
- Brute force lockout (15 min)
- Anomaly trail interne (`security_events`)

### Phase 3 — Verifiability (Mar 2026)
- Passport Ed25519 + Merkle SHA-256
- 12 claims cryptographiques
- Verifier standalone Python + JS
- Endpoints `/api/v1/passport/*`

### Phase 4 — Standards W3C (Apr 2026)
- DID Core 1.0 (`/api/v1/did/*`, `did:frek:{id}`)
- Verifiable Credentials Data Model 2.0
- eddsa-jcs-2022 cryptosuite
- Multikey Multibase (0xed01 + base58btc)

### Phase 4.5 — EUDI + interop
- EUDI Wallet OID4VCI Draft 13+
- SD-JWT VC IETF draft-08+
- JWKS RFC 7517
- DID-Configuration DIF v1
- Manifest universel (ID4Africa, mDL, CARICOM)

### Phase 5 — Fingerprint & audit (May 2026)
- Cultural Fingerprint Layer 7 couches
  (cadence / affinity / device / social / anomaly / coupling / linguistic)
- Audit trail public `/api/v1/audit/{frek_id}`
- Consent RGPD granular

### Phase 6 — Notariat Bitcoin (May-Jun 2026)
- FREK-Chain locale SHA-256 chaînée
- OpenTimestamps loop background (30s / 30 min)
- Bitcoin RPC dual-source
- Explorer public `/explorer` + preuve `/proof/{hash}`
- Compteur universel `/api/core/count`
- Investor Pulse `/api/core/ecosystem/pulse`

### Phase 6.5 — Geo souveraine
- H3 (Uber hex grid) + Open Location Code (Google)
- Nominatim OSM (cache local)
- Sentinel Hub + NASA GIBS satellite imagery
- Atlas heatmap `/atlas`
- Notarisation géo-ancrée

### Phase 7 — Heritage + Sync + Ops (Jun-Jul 2026)
- Module `heritage/` — transmission FREK-ID (6 endpoints)
- Module `sync/` — Baserow bi-directional (5 endpoints)
- Module `health/` — probes K8s + admin backup ops
- Backup daemon supervisé + GPG AES256 obligatoire
- chain_watchdog daemon (vérif 6h)

### Phase 8 — Audits RC v1.0 (Jul 2026)
- Sprint E — Proof of Existence ✅
- Sprint F — Performance Audit ✅
- Sprint G — Resilience Audit ✅ + 4 P1 fixes
- Sprint H — Field templates prêts
- Sprint I — Business Model prêt

---

## 3. Version tag

**FREKCORE v1.0.0-rc** — Release Candidate freezé au 2026-07-08.

Aucun tag git formel n'a été poussé (recommandation : `git tag v1.0.0-rc.1 -m "Assurance Package v1.0"` avant export).

---

## 4. Composants et versions

| Composant | Version |
|---|---|
| Python | 3.11.15 |
| FastAPI | 0.110.1 |
| Motor | 3.x |
| MongoDB | 7.0.37 |
| React | 18 |
| Vite | dernière stable |
| Locust | 2.44.4 |
| opentimestamps-client | dernière PyPI |

Voir `backend/requirements.txt` et `frontend/package.json` pour la liste complète.

---

## 5. Ce que ce document ne fait PAS

- Pas de changelog exhaustif commit-par-commit (172 commits, trop verbeux).
- Pas de release notes marketing (à écrire séparément pour communication publique).
- Pas de note de compatibilité descendante (aucune régression connue depuis v0.9).

Pour un historique complet : `git log --all --oneline` dans le repository.

---

## 6. Prochaines versions envisagées

- **v1.0.0 (production)** : après Sprint H1 réussi (labo 5 personnes).
- **v1.1.0** : Sprint M' (isolation lecture par client_id), endpoint metering, off-site backup.
- **v2.0.0** : Sprint B2 (Deployable Edition) — seulement si un partenaire institutionnel le demande.
