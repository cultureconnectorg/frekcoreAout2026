# FREK V3 — Hardware Attestation Protocol (spec + reference verifier)

> **Statut au 08/07/2026** : intégration Phase 1 (Emergent.sh) — **16/16 tests PASSED en 0.09s**.

## Rôle

Ce dossier héberge la **spécification cryptographique verrouillée** du protocole FREK V3
(attestation hardware L0/L1/L2) et l'**implémentation de référence en Python** qui sert
de "ground truth" mathématique pour toutes les implémentations futures (Rust, FPGA, ASIC).

## Règle d'or

Ce dossier est **isolé de `/app/backend/`** et **n'est PAS importé** par FREKCORE.
Les fichiers Python sont **immuables** — toute modification casse la référence cryptographique.

- **NE PAS** modifier `docs/*.md`
- **NE PAS** modifier `reference_verifier/*.py`
- **NE PAS** intégrer `reference_verifier/` dans le backend `frekcore` (Phase 3 = Rust)
- **NE PAS** renommer les champs / constantes (format binaire figé)

## Structure

```
frek_v3/
├── docs/                     # Spécifications figées (12 docs)
│   ├── FREK_Attestation_Protocol_v0.1.md      (32 kB)
│   ├── FREK_Cryptographic_Architecture_Review_v0.1.md (41 kB)
│   ├── FREK_Object_Model_Specification_v0.1.md (12 kB)
│   ├── FREK_DSP_Fingerprint_Specification_v0.1.md (13 kB)
│   ├── FREK_Architecture_Integree_v0.2.md (20 kB)
│   ├── FREK_V3_Engineering_Exploded_View_v0.2.md (26 kB)
│   ├── FREK_V3_Reconciliation_Architecture_v0.2.md (20 kB)
│   ├── FREK_V3_Roadmap_Next_Lock_v0.2.md (13 kB)
│   ├── FREK_V3_Architecture_Review_Final.md (6 kB)
│   ├── BILAN_DISCUSSION_FREK_V3.md (11 kB)
│   ├── CE_QUI_MANQUE.md (8 kB)
│   └── INSTRUCTIONS_EMERGENT.md (6 kB)
└── reference_verifier/       # Vérificateur de référence Python (immuable)
    ├── frek_constants.py     # Constants (MAGIC=0x46, VERSION=0x01, ECDSA P-256)
    ├── frek_types.py         # FrekProof / DeviceState / VerificationResult
    ├── frek_crypto.py        # Primitives (HKDF, ECDSA, SHA-256 canonique)
    ├── frek_parser.py        # Parser/serializer binaire (proof L2 = 315 bytes)
    ├── frek_registry.py      # Registre devices (état vérificateur)
    ├── frek_verifier.py      # Logique verify() complète
    ├── frek_device_sim.py    # Device FREK V3 simulé (PUF, IKM, DRK, AK)
    ├── test_frek_verifier.py # 16 Golden Test Vectors
    └── README.md
```

## 5 points verrouillés du protocole

| # | Point | Implémentation |
|---|-------|----------------|
| 1 | **DEVICE_ID** | `Truncate(SHA-256(AK_pub), 16)` |
| 2 | **Signature** | ECDSA P-256, `r || s`, 64 bytes raw (pas DER) |
| 3 | **MESSAGE** | `SHA-256(DOMAIN || VERSION || LEVEL || ... || AK_PUB)` encodage canonique |
| 4 | **Replay** | Séparation cryptographique (signature) vs policy (counter, nonce, état device) |
| 5 | **PUF isolation** | Le vérificateur ne voit jamais DRK/IKM/PUF — uniquement `AK_pub` + preuve + registry |

## Chaîne de confiance

```
PUF (silicium hardware)
    ↓
Fuzzy Extractor → IKM
    ↓
HKDF → DRK (hardware only)
    ↓
HKDF → AK (Attestation Key)
    ↓
FREK Proof (signée par AK)
    ↓
Reference Verifier (vérifie avec AK_pub)
```

## Tests

```bash
cd /app/frek_v3/reference_verifier
python -m pytest test_frek_verifier.py -v
```

**Résultat attendu : 16 passed, 0 failed**

| Test | Résultat attendu |
|------|------------------|
| Proof valide | ✅ ACCEPT |
| Signature modifiée | ❌ INVALID_SIGNATURE |
| AUDIO_HASH modifié | ❌ INVALID_SIGNATURE |
| NONCE incorrect | ❌ NONCE_MISMATCH |
| Counter inférieur | ❌ REPLAY |
| Counter identique | ❌ REPLAY |
| DEVICE_ID inconnu | ❌ UNKNOWN_DEVICE |
| AK_pub remplacée | ❌ IDENTITY_MISMATCH |
| Firmware hash non autorisé | ❌ FIRMWARE_REJECTED |
| Mauvais MAGIC | ❌ MALFORMED |
| Mauvaise VERSION | ❌ UNSUPPORTED_VERSION |
| Champ tronqué | ❌ MALFORMED |
| Bit-flip sur chaque champ | ❌ (INVALID_SIGNATURE / IDENTITY_MISMATCH / etc.) |
| Counter window | ✅/❌ selon fenêtre |
| Device révoqué | ❌ REVOKED |
| Autonomous mode | ✅ ACCEPT |

## Ordre de travail (roadmap)

```
FAP v0.1 → Crypto Review v0.1 → Reference Verifier (ceci) → Golden Vectors → FPGA → ASIC
```

Le FPGA (Phase 4) devra produire des preuves que ce vérificateur accepte **bit pour bit**.

## Dépendances (isolées de frekcore)

- Python ≥ 3.10 ✅ (Python 3.11.15 disponible)
- `cryptography` ≥ 44.0 ✅ (49.0.0 installé)
- `pytest` ✅ (9.0.2 installé)

## Ce qui reste hors de FREKCORE aujourd'hui

- Aucune intégration backend, aucun endpoint, aucun import Python vers ce dossier
- Phase 2 (prochaine) : Rust verifier ré-implémentant `frek_verifier.py` bit-exact
- Phase 3 : intégration Rust dans `frekcore` (endpoint `/api/v1/frek_v3/verify`)
- Phase 4 : prototype FPGA (Zynq / Cyclone) reproduisant `frek_device_sim.py`
- Phase 5 : ASIC (silicium hardware)

## Reporting

- **Structure créée** : ✅ `/app/frek_v3/{docs,reference_verifier}/` à côté de `/app/backend/`
- **Fichiers copiés** : ✅ 12 docs + 9 fichiers Python + README, **aucune modification**
- **Dépendances** : ✅ `cryptography 49.0.0` + `pytest 9.0.2` (déjà présents)
- **Tests** : ✅ **16/16 PASSED en 0.09s**
- **Impact frekcore** : ✅ **ZÉRO** — aucun fichier backend modifié
