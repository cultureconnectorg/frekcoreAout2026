# FREK V3 — Roadmap & Next Lock v0.2
## Baseline v0.1 validée — Prochain verrou défini

**Date :** 2026-08-10  
**Statut :** Baseline v0.1 ARCHIVÉE — Next Lock ciblé  
**Règle :** Aucune spec ASIC avant validation du Next Lock

---

## Déclaration de baseline

> **Le pack FREK v0.1 est une BASELINE.**  
> Il prouve que l'architecture est cohérente, que le protocole est valide, et que la chaîne de confiance est solide.  
> Il n'est PAS une spécification prête pour ASIC.  
> Il ne le sera que après validation du Next Lock.

---

## Ce qui est verrouillé (Baseline v0.1)

| Élément | Document | Statut |
|---------|----------|--------|
| Protocole d'attestation | FAP v0.1 | 🟢 ARCHIVÉ |
| Architecture cryptographique | Crypto Review v0.1 | 🟢 ARCHIVÉ |
| Implémentation Python de référence | reference_verifier/ | 🟢 ARCHIVÉ (16 tests passés) |
| Engineering Exploded View | Engineering v0.2 | 🟢 ARCHIVÉ (4 corrections intégrées) |
| DSP Specification (draft) | DSP Spec v0.1 | 🟡 DRAFT (attente décision objectif) |

**Ces documents ne sont plus modifiés.**  
Toute évolution passe par une nouvelle version (v0.2, v1.0, etc.) avec revue formelle.

---

## Le Next Lock — Définition

> **Le Next Lock est le point où la spécification devient suffisamment déterministe pour qu'un FPGA puisse la reproduire bit-à-bit et qu'un second implémenteur (Rust) puisse la valider indépendamment.**

Il se compose de **trois livrables interdépendants** :

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXT LOCK v0.2                           │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ GOLDEN VECTORS  │  │ RUST VERIFIER   │  │ DSP EXPÉRI- │ │
│  │  (déterministes)│  │ (indépendant)   │  │ MENTAL      │ │
│  │                 │  │                 │  │ (validation)│ │
│  │ • Clés fixes    │  │ • Même spec     │  │ • Corpus    │ │
│  │ • Entrées fixes │  │ • Code différ.  │  │ • Métriques │ │
│  │ • Sorties fixes │  │ • Mêmes résult. │  │ • FPR/FNR   │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │        │
│           └────────────────────┼───────────────────┘        │
│                                ▼                            │
│                    ┌─────────────────────┐                  │
│                    │  CONVERGENCE        │                  │
│                    │  Python = Rust      │                  │
│                    │  Théorie = Mesure   │                  │
│                    └─────────────────────┘                  │
│                                │                            │
│                                ▼                            │
│                    ┌─────────────────────┐                  │
│                    │  FPGA PROTOTYPE     │                  │
│                    │  (peut commencer)   │                  │
│                    └─────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Livrable 1 — Golden Vectors déterministes

### Définition

Un jeu de données totalement reproductibles : même entrée → même sortie, à chaque exécution, sur n'importe quelle machine.

### Contenu

```
GOLDEN_VECTOR_SET/
├── device/
│   ├── private_key.hex          (P-256, TEST ONLY, jamais en production)
│   ├── public_key.hex           (33 octets compressés)
│   ├── device_id.hex            (Truncate(SHA-256(pub_key), 16))
│   ├── puf_seed.hex             (256 bits, TEST ONLY)
│   └── firmware_hash.hex        (SHA-256 d'un firmware de test)
│
├── inputs/
│   ├── nonce.hex                (16 octets fixes)
│   ├── audio_buffer.hex         (ex: 2048 samples @ 48kHz)
│   ├── fingerprint_vector.hex   (résultat du DSP sur audio_buffer)
│   ├── context_metadata.hex     (JSON de test)
│   └── device_time.txt          (ISO 8601 fixe)
│
├── expected/
│   ├── audio_hash.hex           (SHA-256(audio_buffer))
│   ├── fingerprint_hash.hex     (SHA-256(fingerprint_vector))
│   ├── context_hash.hex         (SHA-256(context_metadata))
│   ├── message_hash.hex         (SHA-256(canonical_message))
│   ├── signature.hex            (ECDSA-Sign(private_key, message_hash))
│   └── proof.hex                (283 octets complets)
│
└── README.md                    (comment reproduire)
```

### Règles

- **Les clés de test sont publiques.** Elles sont marquées "TEST ONLY — NEVER USE IN PRODUCTION".
- **Aucune randomisation.** Pas de `secrets.token_bytes()`. Tout est fixe.
- **Reproductibilité.** `python generate_golden.py` doit produire exactement `expected/proof.hex`.

---

## Livrable 2 — Rust Verifier

### Définition

Une implémentation indépendante du vérificateur en Rust, interprétant la même spécification (FAP v0.1) sans regarder le code Python.

### Architecture

```
frek_verifier_rust/
├── Cargo.toml
├── src/
│   ├── lib.rs              # API publique
│   ├── constants.rs        # MAGIC, VERSION, tailles
│   ├── types.rs            # FrekProof, DeviceState, VerificationResult
│   ├── crypto.rs           # SHA-256, HKDF, ECDSA P-256 raw
│   ├── parser.rs           # Parser binaire 283 octets
│   ├── registry.rs         # État par device
│   └── verifier.rs         # Pipeline complet
│
├── tests/
│   ├── golden_vectors.rs   # Test avec les Golden Vectors
│   └── integration.rs      # Tests de non-régression
│
└── README.md
```

### Critère de succès

```bash
cargo test
# → Tous les tests passent
# → Les Golden Vectors produisent EXACTEMENT les mêmes résultats que Python
# → Bit-à-bit identique pour : message_hash, signature, proof
```

**Si Python et Rust divergent :** La spec a une ambiguïté. Il faut la corriger et mettre à jour FAP v0.1 → v0.2.

---

## Livrable 3 — Validation expérimentale du DSP

### Définition

Prouver que les paramètres DSP proposés (DSP Spec v0.1) produisent des fingerprints de qualité suffisante pour l'objectif choisi (Provenance).

### Méthodologie

**Étape 1 — Corpus de test**

```
CORPUS/
├── original/               (100 morceaux, 48kHz/24bit WAV)
├── mp3_128/                (mêmes morceaux, MP3 128 kbps)
├── mp3_320/                (mêmes morceaux, MP3 320 kbps)
├── aac_128/                (mêmes morceaux, AAC 128 kbps)
├── gain_plus6db/           (mêmes morceaux, +6 dB)
├── gain_minus6db/          (mêmes morceaux, -6 dB)
├── noise_20db/             (mêmes morceaux, bruit blanc SNR 20 dB)
└── reverb_light/           (mêmes morceaux, reverb légère)
```

**Étape 2 — Génération des fingerprints**

```python
for file in corpus:
    fingerprint = dsp_pipeline(file)  # Paramètres DSP Spec v0.1
    store(fingerprint)
```

**Étape 3 — Matrice de comparaison**

| | Original | MP3 128 | MP3 320 | AAC 128 | +6 dB | -6 dB | Bruit | Reverb |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Original** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **MP3 128** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **MP3 320** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **AAC 128** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **+6 dB** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **-6 dB** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Bruit** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Reverb** | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

**Légende :** ✅ = Match (distance < seuil) | ⚠️ = Partial | ❌ = No match

**Étape 4 — Métriques**

```
False Positive Rate (FPR) = 0%  (morceaux différents matchés)
False Negative Rate (FNR) = < 1% (mêmes morceaux non matchés après transformation)
```

### Critère de succès

- FPR = 0% (aucune collision entre morceaux différents)
- FNR < 1% pour MP3, AAC, gain, bruit
- FNR < 5% pour reverb légère (tolérance réduite acceptable)

---

## Séquence d'exécution

```
PHASE 1 — Golden Vectors (1-2 jours)
│
├── Créer generate_golden.py
├── Générer clés fixes (TEST ONLY)
├── Générer entrées fixes
├── Calculer sorties attendues
└── Vérifier reproductibilité (exécuter 10×, comparer)
    │
    ▼
PHASE 2 — Rust Verifier (3-5 jours)
│
├── Créer le crate frek_verifier_rust
├── Implémenter parser, crypto, verifier
├── NE PAS regarder le code Python
├── Tester avec cargo test
└── Valider contre Golden Vectors
    │
    ▼
PHASE 3 — DSP Expérimental (2-3 jours)
│
├── Constituer le corpus (100 morceaux)
├── Implémenter le pipeline DSP (Python ou Rust)
├── Générer fingerprints pour tout le corpus
├── Calculer matrice de distance
└── Mesurer FPR et FNR
    │
    ▼
PHASE 4 — Convergence (1 jour)
│
├── Comparer Python vs Rust (bit-à-bit)
├── Comparer théorie vs mesure (DSP)
├── Documenter écarts
└── Si convergence → LOCK v0.2
    │
    ▼
PHASE 5 — FPGA Prototype (2-3 mois)
│
├── Choisir board (Zynq-7000 / PolarFire SoC)
├── Implémenter soft-core RISC-V
├── Intégrer FFT IP
├── Implémenter crypto soft ou HSM externe
├── Produire preuves avec Golden Vectors
└── Valider que Rust verifier accepte
```

---

## Ce qui ne vient PAS encore

| Élément | Pourquoi pas encore | Quand |
|---------|---------------------|-------|
| **ASIC Specification** | Pas de données FPGA = pas de chiffrage fiable | Après FPGA |
| **Contact fondeur** | Pas de RTL = pas de quoi montrer | Après FPGA |
| **NRE / Business plan** | Pas de mesures = pas de chiffrage | Après FPGA |
| **Certification (FIPS/CC)** | Le niveau dépend du marché, pas défini | Après choix marché |
| **Package / Pinout définitif** | Peut évoluer sur FPGA | Après FPGA |
| **Team hardware complète** | Pas de spec ASIC = pas de quoi recruter pour | Après FPGA |

**Règle :** Le FPGA est le filtre. Si le FPGA prouve que ça marche, on investit dans l'ASIC. Si le FPGA échoue, on corrige la spec avant d'engager des coûts fondeur.

---

## Checklist de validation du Next Lock

| # | Critère | Validation |
|---|---------|------------|
| 1 | Golden Vectors reproductibles 10/10 | `diff` entre 10 exécutions = vide |
| 2 | Rust verifier passe tous les tests | `cargo test` = 100% pass |
| 3 | Rust = Python bit-à-bit | `cmp proof_rust.hex proof_python.hex` = identique |
| 4 | DSP FPR = 0% | Aucune collision entre morceaux différents |
| 5 | DSP FNR < 1% (transformations courantes) | MP3, AAC, gain, bruit |
| 6 | DSP FNR < 5% (reverb légère) | Tolérance acceptable |
| 7 | Documentation des écarts | Si écart > 0, documenté et justifié |

**Si les 7 critères sont verts → Next Lock validé → FPGA peut commencer.**

---

## Synthèse

```
BASELINE v0.1                    NEXT LOCK v0.2                  FPGA
    │                                 │                            │
    ├── FAP v0.1                      ├── Golden Vectors            │
    ├── Crypto Review v0.1            ├── Rust Verifier             │
    ├── Python verifier (16 tests)    ├── DSP Experimental          │
    ├── Engineering v0.2              └── Convergence               │
    └── DSP Spec v0.1 (draft)              │                       │
                                           ▼                       │
                                    LOCK v0.2 VALIDÉ ──────────────┘
```

---

*Document de feuille de route — v0.2*  
*Baseline v0.1 archivée. Next Lock défini. Aucun ASIC avant validation.*
