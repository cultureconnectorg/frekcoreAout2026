> ⚠️ **CONFIDENTIAL — FREKCORE Internal**
> Distribution restricted. NDA required for external sharing.
> Ce document appartient au niveau Vault (Level 3) de la doctrine IP FREKCORE.

---


# FREKCORE Sprint E — Proof of Existence Audit
## Audit de souverainete technique

**Date audit** : 2026-07-08T10:41:35Z
**FREKCORE version** : 1.0.0-rc
**Bundle path** : `/app/proof_bundle_20260708T103916Z`
**Executeur** : Automatise (`/app/scripts/proof_of_existence.sh`)

---

## 1. Doctrine testee

> **"Une preuve FREK reste verifiable meme si FREKCORE disparait."**

Cet audit demontre que les 4 dimensions cryptographiques d'un FREK-ID sont
verifiables **offline**, uniquement avec des artefacts publics et des
verifiers standalone — **sans aucun appel a FREKCORE**.

## 2. Sujet de l'audit

- **FREK-ID emis pour ce test** : `ed010822-077e-4f36-9ecb-d4aea3015f8e`
- **Event** : `SOVEREIGNTY_AUDIT`
- **Cle publique Ed25519 (trust root)** : `CrgwxpFRyASkNqSNeQhdzdaAVtawxU3PHoVND8uc73Y=`
- **Bloc FREK-Chain associe** : `eb6e6f3ebf37994ca7ef4509199a495c3eb96a9d7ecca3c95f4a98f9b7971c83`
- **Racine Merkle passport** : `9d0df5bffc0d0be9a2e29ebe043ed8563fe3127807b3e431453e58ab5c2b7629`

## 3. Sequence executee

1. **Emission** — POST /api/v1/identity/emit → FREK-ID cree en base + block #1265 notarise sur FREK-Chain + soumis a 3 calendars OTS.
2. **Export** — recuperation via API de 13 artefacts publics (passport, DID, VC, block, .ots, verifier, JWKS, etc.).
3. **Shutdown simule** — plus AUCUN appel a l'API FREKCORE apres cette etape.
4. **Verification offline** avec verifier standalone + lib opentimestamps standard.

## 4. Resultats de verification (offline uniquement)

### 4.1 Identite Ed25519 — VALID ✅

Executed :
```bash
python3 verify_passport.py --passport passport.json --public-key-b64 "CrgwxpFRyASkNqSNeQhdzdaAVtawxU3PHoVND8uc73Y="
```
Result : `{"valid": true, "mode": "full", "errors": [], "claims_count": 12}`

### 4.2 Integrite Merkle SHA-256 — VALID ✅
Racine `9d0df5bffc0d0be9a2e29ebe043ed8563fe3127807b3e431453e58ab5c2b7629` reconstruite par folding des 12 leaves du passport, verifiee dans verify_passport.py.

### 4.3 DID Document W3C DID Core 1.0 — VALID ✅
Structure conforme : @context, id=did:frek:{frek_id}, verificationMethod=Multikey, publicKeyMultibase='z...' (base58btc + multicodec ed25519-pub 0xed01).

### 4.4 Verifiable Credential eddsa-jcs-2022 — VALID ✅
JCS canonicalization RFC 8785 + SHA-256 hash + Ed25519 verification sur (opts_hash || doc_hash). Signature independamment revalidee.

### 4.5 Block FREK-Chain integrity — VALID ✅
Champs prev_hash + block_hash + payload_hash present, height=1265, chainage SHA-256(height|prev_hash|payload_hash|...).

### 4.6 OpenTimestamps proof — VALID ✅ (pending BTC 1-6h)
Preuve .ots de 844 bytes deserializee avec la lib opentimestamps standard.
**5 attestations sur calendars publics INDEPENDANTS de FREKCORE** :

- `https://bob.btc.calendar.opentimestamps.org` x2
- `https://alice.btc.calendar.opentimestamps.org` x2
- `https://finney.calendar.eternitywall.com` x1

Status : `PENDING_BTC` (attestation Bitcoin definitive dans 1-6h, upgradable via `ots upgrade` sur n'importe quel client OTS).

## 5. Empreintes SHA-256 (fingerprint des 13 artefacts)

```
0104944ded81f3b073c64589b8b2fc8b41e824fba49df4fd758fca6bebbba56a  public_key.json
185b8fdaebf1441c0a73159bd8884bcff3d0c291d50a10513227c8006f77c797  notary_proof.ots
1c24439415b8ec1d8085b8a5dde39fa905aef9fcf1406b238a17593d21b9af02  notary_proof.json
608d5024c7267985ab1faa3d9725ba8f5417a371fd217147e95cc0669278ee8c  verify_passport.py
95a8ae57c355c67d8fd29934c722847a89bd88197422fedc3700f2265fc1d927  notary_block.json
9757a8186f7899c2c741ca3c032aaeeb17b05879f62311336c0d019615d8b2ae  passport.json
a0e721ef40dab513699cae54242ae8e1f6340d8c151fccb52db2f6eecaa4f61a  vc.json
a9a4a63b88a6431a185afaf8e3e5f9cbffd141be88e48bc3bce449d084453730  verify_passport_result.json
b2e8129ae827a6e8d09131d78937552f747d8fff23af0707cda25e66022665f3  did.json
be827b4e9b921d2b12d60c79f2536c2b56a86f80fc3a7babd9b2d82ce21a813a  verify_ots_offline.py
c9e929fcae402359db07a09b1f01b93eeece9f60498a32058141068454b993c1  verify_passport.js
e59649512931e0fbbc08ad2fb56fb9be2795dd9a730b1e5b9d80000ad2560509  jwks.json
f81e733d01874975af3beb6892611b425636340452d2c71c82aac7eb03dc5dc3  ots_verification.json
```

## 6. Trust root & autonomie

La cle publique Ed25519 est le seul ancrage cryptographique de tout le systeme. Elle est exposee sur :
- `/api/v1/passport/key` (JSON + PEM + raw b64)
- `/.well-known/jwks.json` (RFC 7517 universelle)
- `/api/v1/did/frekcore` (DID Document W3C)

Elle est backupee **chiffree GPG AES256** (Sprint A) et **doit** etre stockee hors du serveur (password manager humain).

## 7. Verifier standalone — 0 dependance FREKCORE

Fichiers reproducteurs (inclus dans ce bundle) :
- `verify_passport.py` — Python single-file, dep unique `cryptography`.
- `verify_passport.js` — JS ES module zero-deps (Web Crypto API).
- `verify_ots_offline.py` — Python single-file, dep unique `opentimestamps`.

Reproduction complete :
```bash
pip install cryptography opentimestamps
python3 verify_passport.py --passport passport.json --public-key-b64 "CrgwxpFRyASkNqSNeQhdzdaAVtawxU3PHoVND8uc73Y="
python3 verify_ots_offline.py notary_proof.ots notary_block.json
```

## 8. Verdict senior

### ✅ **PROOF OF EXISTENCE : VALIDE**

**FREKCORE tient sa promesse de "notaire culturel tech"** :

1. Un tiers dispose des artefacts + verifier + cle publique peut valider un evenement culturel sans dependre de frekcore.com.
2. La signature Ed25519 est mathematiquement invariante — meme dans 5 ans, meme si FREKCORE.io n'existe plus.
3. La preuve OTS pointe vers 3 organisations publiques independantes (Bob/Alice/Finney) qui ancreront le hash dans Bitcoin — **Bitcoin garantit alors la datation, pas FREKCORE**.
4. La cle publique est exposee sur 3 standards universels (JWK, DID, PEM) — reconciliable par n'importe quel wallet EUDI, ID4Africa, mDL, W3C VC.

### Chaine de confiance certifiee

```
Porteur → FREK-ID (nominatif, a vie)
       → Signature Ed25519 (cle FREKCORE)
       → SHA-256 chain FREK-Chain (integrite locale)
       → OpenTimestamps (calendars publics)
       → Bitcoin blockchain (datation universelle)
       → Verifier offline (souverainete)
```

Chaque maillon est verifiable independamment.
**Aucun maillon ne depend d'une infra proprietaire au-dela du protocole ouvert utilise.**

## 9. Reproductibilite

Ce dossier `/app/proof_bundle_20260708T103916Z` est autoportant. Pour verifier a nouveau dans 5 ans :
1. Copier le dossier sur n'importe quelle machine avec Python 3.
2. `pip install cryptography opentimestamps`.
3. Executer les 2 verifiers ci-dessus.
4. Comparer avec `SHA256SUMS.txt` pour detecter toute alteration.

Le present rapport peut lui-meme etre :
- Signe Ed25519 (via `/api/v1/notary/notarize` — ironique mais coherent).
- Publie en Git public (temoin de production).
- Ancre dans Bitcoin (via ots-cli en direct).

---

**SHA-256 auto-audit** : `586a9c83bede1a2ae19510032e62941cbe3a06a1435e359dac14e6537cf40616`
