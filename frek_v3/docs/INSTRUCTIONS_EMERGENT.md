# Instructions pour Emergent.sh — Intégration FREK V3

**Date :** 2026-08-10  
**De :** Direction produit / Architecture  
**Pour :** Équipe technique Emergent.sh  
**Statut :** À exécuter sans modification du protocole

---

## Contexte

FREK V3 est la **phase de conceptualisation du hardware** (puce de certification audio). Ce qui est livré ici n'est **pas** du code de production à intégrer dans le backend. C'est une **brique externe de validation** qui prouve que le protocole d'attestation fonctionne mathématiquement.

**Règle d'or :** Ces fichiers sont une **spécification exécutable**. On ne les modifie pas. On les valide, on les archive, et on s'en sert comme référence pour le futur vérificateur Rust.

---

## 1. Structure de fichiers à créer

Dans le repo `emergent.sh/`, créer exactement cette arborescence :

```
emergent.sh/
├── frekcore/                          ← [EXISTANT] NE PAS TOUCHER
│   ├── src/
│   ├── Cargo.toml
│   └── ...
│
├── frek_v3/                           ← [NOUVEAU] Conceptualisation hardware
│   ├── docs/                          ← Spécifications techniques
│   │   ├── FREK_Attestation_Protocol_v0.1.md
│   │   └── FREK_Cryptographic_Architecture_Review_v0.1.md
│   │
│   └── reference_verifier/            ← Implémentation Python de test
│       ├── __init__.py
│       ├── README.md
│       ├── frek_constants.py
│       ├── frek_types.py
│       ├── frek_crypto.py
│       ├── frek_parser.py
│       ├── frek_registry.py
│       ├── frek_verifier.py
│       ├── frek_device_sim.py
│       └── test_frek_verifier.py
│
└── README.md                          ← [EXISTANT]
```

**Contrainte :** Le dossier `frek_v3/` est **à côté** de `frekcore/`, pas dedans. Ce n'est pas une dépendance du backend. C'est un laboratoire de preuve.

---

## 2. Action immédiate — Validation du protocole

### Étape 1 : Dépendance

```bash
cd emergent.sh/frek_v3/reference_verifier
pip install cryptography
```

### Étape 2 : Exécution des tests

```bash
python test_frek_verifier.py
```

### Résultat attendu

```
Running FREK Reference Verifier Tests...
============================================================
  ✅ test_valid_proof
  ✅ test_signature_modified
  ✅ test_audio_hash_modified
  ✅ test_nonce_mismatch
  ✅ test_replay_same_counter
  ✅ test_replay_older_counter
  ✅ test_unknown_device
  ✅ test_identity_mismatch
  ✅ test_firmware_rejected
  ✅ test_bad_magic
  ✅ test_unsupported_version
  ✅ test_truncated_proof
  ✅ test_bitflip_all_fields (11 fields)
  ✅ test_counter_window
  ✅ test_revoked_device
  ✅ test_autonomous_mode
============================================================
Results: 16 passed, 0 failed
```

**Si un test échoue :** Ne pas corriger le code. Signaler immédiatement. Le protocole est verrouillé.

---

## 3. Ce qu'il faut comprendre

### 3.1 Les documents (`docs/`)

| Document | Contenu | Usage |
|----------|---------|-------|
| `FREK_Attestation_Protocol_v0.1.md` | Format binaire de la preuve (283 octets), protocole I²C/SPI, vérification | Référence pour l'implémentation future en Rust |
| `FREK_Cryptographic_Architecture_Review_v0.1.md` | PUF, HKDF, ECDSA P-256, threat model, lifecycle des clés | Référence pour l'audit sécurité et le recrutement hardware |

### 3.2 Le code Python (`reference_verifier/`)

Ce n'est **pas** du code de production. C'est :
- Un **simulateur** de puce FREK V3 (`frek_device_sim.py`)
- Un **vérificateur de référence** (`frek_verifier.py`)
- Des **tests de non-régression** (`test_frek_verifier.py`)

**Objectif :** Prouver que le protocole est cohérent avant de l'implémenter en hardware (FPGA) et en production (Rust).

---

## 4. Ce qu'il ne faut PAS faire

| Interdit | Raison |
|----------|--------|
| Modifier les fichiers `docs/*.md` | Ce sont des spécifications verrouillées. Toute modification doit passer par une revue formelle. |
| Modifier la logique cryptographique du Python | Le code est l'oracle de référence. Si on le change, on perd la traçabilité. |
| Intégrer le Python dans `frekcore/` | `frekcore` reste en Rust/JS. Le Python est un outil de test isolé. |
| Renommer les champs ou les constantes | Le format binaire est figé (offsets, tailles, endianness). |
| Supprimer les tests | Ils serviront à valider la future implémentation Rust. |

---

## 5. Ce qui est prévu ensuite (hors scope immédiat)

Ces étapes seront déclenchées par la direction produit. **Ne pas les démarrer sans validation.**

| Étape | Description | Responsable |
|-------|-------------|-------------|
| **Rust Verifier** | Réimplémentation du vérificateur en Rust (crate séparé) | Dev Rust à recruter / contracter |
| **Intégration frekcore** | Le crate Rust devient une dépendance de `frekcore` pour valider les preuves | Équipe Emergent |
| **FPGA Prototype** | Prototype matériel reproduisant les Golden Test Vectors | Ingénieur hardware à recruter |
| **ASIC Specification** | Spécification complète pour le tape-out | Design house / fondeur |

---

## 6. Livrable attendu de l'équipe

Après intégration des fichiers et exécution des tests, l'équipe doit confirmer par écrit (dans un channel ou un ticket) :

1. **Structure créée** : Les dossiers `frek_v3/docs/` et `frek_v3/reference_verifier/` existent.
2. **Tests passés** : `16 passed, 0 failed` (copier-coller du terminal).
3. **Compréhension** : Un membre de l'équipe a lu au moins un des deux documents et peut expliquer ce qu'est une "preuve L2".
4. **Aucune modification** : Les fichiers sont identiques à ceux livrés (vérification par `diff` ou `sha256`).

---

## 7. Questions fréquentes

**Q : Pourquoi Python et pas Rust directement ?**  
R : Python est plus rapide à valider pour une spec. Le Rust viendra après, validé contre les mêmes vecteurs de test.

**Q : Le code Python va-t-il tourner en production ?**  
R : Non. Jamais. C'est un outil de test et de spécification.

**Q : Quand est-ce que FREK V3 sera dans frekcore ?**  
R : Quand le Rust verifier sera prêt et audité. Ce n'est pas prioritaire sur les features courantes de frekcore.

**Q : Qui recrute l'ingénieur hardware ?**  
R : Direction produit. L'équipe technique n'a pas à chercher le profil, mais elle doit être capable d'expliquer les documents à un candidat.

---

**Document verrouillé — v0.1**  
*Ne pas modifier sans accord de l'architecture FREK.*
