# 10 — Hash Registry

**FREKCORE Assurance Package v1.0** — Document 10
**Version** : 1.0.0-rc
**Date de gel** : 2026-07-08T13:24:00Z
**Objet** : registre immuable des empreintes SHA-256 de tous les artefacts du package.

---

## 1. Utilité

Ce document permet à un tiers de :
1. Vérifier qu'un fichier reçu est authentique et non-altéré.
2. Détecter toute modification post-publication.
3. Notariser le package entier en signant ce document (récursivité cryptographique).

Toute divergence entre un hash calculé et cette liste **prouve une altération** — soit du fichier, soit du registre lui-même.

---

## 2. Empreintes SHA-256 des documents du package

| # | Document | SHA-256 |
|---|---|---|
| 01 | Architecture Overview | `eb1ded3b8d4777cf0ad5a45b10b23ff45624c0fd9188b12979ac2882c3e9fffa` |
| 02 | Security Model | `69ad1d5ea3f875f1e805733015119d1313f58c82a259c9081e01c77a02668ff7` |
| 03 | Proof of Existence Audit | `2694d9ded85f74c89b7c01b92126dd9dbf340f71525fe588e9ba7260ff1ad135` |
| 04 | Performance Audit | `ebd89a8c7a9c169b2e10cfef979759bb1f20c9ef75e177442758b9acdc2737d1` |
| 05 | Resilience Audit | `7c3ec9d6c1815250e3efcc0093e7d4e0f9f633db4ade7d94bdac945a7911695f` |
| 06 | Field Test Report **TEMPLATE** | `1c0b54ae4e4eb3c46086cc9ce47a95fb37b5587cd03d441fd71013d20443bd27` |
| 07 | Business Model | `13b373db6909e84fb74baae1894a20570b576ac3ac362b49c5d210234202f418` |
| 08 | External Review | `30008f5f1292201fdcd0cbe08e55403f1009f9e943b8a58e5c37e4ca50247b7a` |
| 09 | Version History | `eef1af91037a7db1e3810c261c70745fd04e30e3b4b9f431d2fcaea80b0946a8` |

---

## 3. Empreintes des artefacts d'exécution associés (au 2026-07-08)

| Artefact | Source | SHA-256 |
|---|---|---|
| Clé publique Ed25519 (JSON) | `GET /api/v1/passport/key` | `0104944ded81f3b073c64589b8b2fc8b41e824fba49df4fd758fca6bebbba56a` |
| Spec publique v1.0.0 | `GET /api/v1/spec/` | `47e4022a37edb1ed61483f6617db1fa48118658b640bb023e0a63f42d2d091b0` |
| Verifier Python standalone | `GET /api/v1/passport/verifier/python` | `608d5024c7267985ab1faa3d9725ba8f5417a371fd217147e95cc0669278ee8c` |
| Verifier JS standalone | `GET /api/v1/passport/verifier/js` | `c9e929fcae402359db07a09b1f01b93eeece9f60498a32058141068454b993c1` |

---

## 4. Clé publique Ed25519 (trust root)

**Fingerprint du fichier `.passport_key.pem` sur disque** :
`496a69437acd86d5dcc42f79c59fa951786c47ad8fb84e21b9028fd28f6e9088`

**Clé publique brute (base64, 32 bytes)** :
Voir `GET /api/v1/passport/key` (champ `public_key_raw_b64`).

Cette clé est immuable pour toute la durée de v1.0.
Une rotation invaliderait tous les passeports FREK émis avant la rotation.

---

## 5. Chain FREK-Chain — état au freeze

| Métrique | Valeur |
|---|---|
| Chain height | 1311 |
| Chain integrity | `valid: true` |
| Blocks vérifiés | 1311 |
| Anchors OTS total | 1409 |
| Blocks BTC-confirmés | 1291 |
| Calendars OTS actifs | 5 publics indépendants |

---

## 6. Reproductibilité

Pour vérifier l'intégrité du package :

```bash
# 1. Télécharger le dossier assurance_package_v1.0/
# 2. Recalculer les hashes
sha256sum 0*_*.md

# 3. Comparer avec §2 ci-dessus

# 4. Si tous les hashes matchent → package authentique.
# 5. Si un hash diverge → altération. Le registre doit être lu comme suspect.
```

Pour vérifier les artefacts d'exécution :

```bash
API=https://<your-frekcore-url>
curl -s "$API/api/v1/passport/key" | sha256sum
curl -s "$API/api/v1/spec/" | sha256sum
curl -s "$API/api/v1/passport/verifier/python" | sha256sum
```

Comparer avec §3 ci-dessus.

---

## 7. Notarisation de ce registre

Ce document `10_Hash_Registry.md` peut lui-même être notarisé sur FREK-Chain :

```bash
sha256sum 10_Hash_Registry.md
# → HASH_REGISTRY

curl -X POST "$API/api/v1/notary/notarize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"payload_type\":\"assurance_package_v1\",\"payload_data\":{\"registry_sha256\":\"HASH_REGISTRY\"}}"
```

Le block resultant devient une preuve immuable que **l'Assurance Package v1.0 existait dans cet état exact à cette date**.

Cette notarisation est **optionnelle** mais recommandée avant tout envoi externe.

---

## 8. Auto-hash de ce document

**SHA-256 de `10_Hash_Registry.md`** : à calculer après finalisation.

```bash
sha256sum 10_Hash_Registry.md
```

Voir ci-dessous pour la valeur figée.

---

**SHA-256 de ce registre (au moment du gel)** : `5b79e9fb4dd2ab7d87bc1d14cfdfa6065b594026d61d0b365153cd7d77f72689`
