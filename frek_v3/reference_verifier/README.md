# FREK Reference Verifier v0.1

Implementation de référence Python du **FREK Attestation Protocol v0.1** et de la **FREK Cryptographic Architecture Review v0.1**.

## Architecture

```
frek_reference_verifier/
├── frek_constants.py      # Constantes du protocole
├── frek_types.py          # Structures de données (dataclasses)
├── frek_crypto.py         # Primitives cryptographiques
├── frek_parser.py         # Parser / serializer binaire
├── frek_registry.py       # Registre de devices (état du vérificateur)
├── frek_verifier.py       # Logique de vérification complète
├── frek_device_sim.py     # Device FREK V3 simulé (génération de preuves)
├── test_frek_verifier.py  # Golden Test Vectors + tests unitaires
└── README.md              # Ce fichier
```

## 5 points verrouillés

| # | Point | Implémentation |
|---|-------|----------------|
| 1 | **DEVICE_ID** | `Truncate(SHA-256(AK_pub), 16)` — dérivée de la clé publique |
| 2 | **Signature** | `r || s`, 64 bytes raw, pas DER |
| 3 | **MESSAGE** | `SHA-256(DOMAIN || VERSION || LEVEL || ... || AK_PUB)` avec encodage canonique strict |
| 4 | **Replay** | Séparation cryptographique (signature valide) vs policy (counter, nonce, état device) |
| 5 | **PUF isolation** | Le vérificateur ne voit jamais DRK/IKM/PUF — uniquement `AK_pub` + `FREK Proof` + registry state |

## Chaîne de confiance

```
PUF (silicium)
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

## Utilisation

### Vérifier une preuve

```python
from frek_registry import DeviceRegistry
from frek_verifier import FrekVerifier
from frek_device_sim import SimulatedFrekDevice

# 1. Créer un device simulé
device = SimulatedFrekDevice()
identity = device.get_identity()

# 2. Enregistrer le device dans le registry
registry = DeviceRegistry()
registry.register(
    device_id=identity["device_id"],
    ak_pub=identity["ak_pub"],
    trusted_firmware_hashes={identity["firmware_hash"]},
)

# 3. Générer une preuve
import secrets
nonce = secrets.token_bytes(16)
proof = device.generate_proof(
    audio_buffer=b"audio_data",
    fingerprint_vector=b"fingerprint",
    context_metadata=b"{\"loc\":\"studio\"}",
    nonce=nonce,
)

# 4. Vérifier
verifier = FrekVerifier(registry)
result = verifier.verify(proof, expected_nonce=nonce)
print(result.accepted)  # True
print(result.code)      # "ACCEPT"
```

### Exporter les Golden Test Vectors

```bash
cd frek_reference_verifier
python test_frek_verifier.py
```

### Lancer les tests

```bash
cd frek_reference_verifier
pytest test_frek_verifier.py -v
```

## Golden Test Vectors

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

## Ordre de travail

```
FAP v0.1 → Crypto Review v0.1 → Reference Verifier (ceci) → Golden Vectors → FPGA → ASIC
```

Le FPGA devra produire des preuves que ce vérificateur accepte **bit pour bit**.

## Dépendances

- Python ≥ 3.10
- `cryptography` ≥ 44.0
- `pytest` (pour les tests)

## License

Internal — FREK Architecture Team
