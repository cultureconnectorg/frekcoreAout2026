# FREK V3 — Engineering Exploded View v0.2
## Corrections post-audit n°2 — 4 points critiques intégrés

**Date :** 2026-08-10  
**Statut :** Engineering-locked partiel — 4 corrections appliquées  
**Règle :** Tout élément non marqué 🟢 LOCKED est considéré comme 🟡 PROPOSED ou 🔴 TBD

---

## Corrections de la v0.1 → v0.2

| # | Problème | Correction |
|---|----------|------------|
| 1 | FK dérivée du DRK | FK est une **clé publique d'autorité** (FREK Authority), pas une clé dérivée du PUF |
| 2 | TRNG = NIST SP 800-90B | Séparation : **Entropy Source** → SP 800-90B health tests → **DRBG** → random output |
| 3 | Compteur : 100K preuves max | Problème identifié — wear leveling / checkpointing / fréquence d'usage à définir |
| 4 | Device ID "ne traverse pas" | Reformulation : donnée publique, dérivation sans secret, pas de passage de secret |

---

## 1. Architecture SoC corrigée

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FREK V3 SoC — ENGINEERING v0.2                  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🟢 LOCKED — TRUST DOMAIN                                        │   │
│  │                                                                 │   │
│  │  PUF (SRAM-based)                                               │   │
│  │    ↓                                                            │   │
│  │  Fuzzy Extractor (BCH, FER < 10⁻⁹)                              │   │
│  │    ↓                                                            │   │
│  │  IKM (256 bits, volatile)                                       │   │
│  │    ↓                                                            │   │
│  │  HKDF-SHA256(salt=FABRIC_DATA, info="frek-v3-root")             │   │
│  │    ↓                                                            │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │  DRK — Device Root Key                                  │    │   │
│  │  │  256 bits, registres hardware uniquement                │    │   │
│  │  │  NEVER EXPORTED — NEVER STORED IN SRAM/FLASH            │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  │    ↓                                                            │   │
│  │  ┌─────────────┐  ┌─────────────┐                               │   │
│  │  │ AK          │  │ CK (opt)    │                               │   │
│  │  │ Attestation │  │ Comm Key    │                               │   │
│  │  │ Key         │  │             │                               │   │
│  │  └─────────────┘  └─────────────┘                               │   │
│  │                                                                 │   │
│  │  TRNG Subsystem :                                               │   │
│  │    Physical Entropy Source (ring oscillator / thermal noise)    │   │
│  │    ↓                                                            │   │
│  │    SP 800-90B Health Tests (startup + continuous)               │   │
│  │    ↓                                                            │   │
│  │    DRBG (CTR-DRBG ou HMAC-DRBG, reseeded)                      │   │
│  │    ↓                                                            │   │
│  │    Random Output → ECDSA nonce k                                │   │
│  │                                                                 │   │
│  │  ECC P-256 Accelerator                                          │   │
│  │  SHA-256 Accelerator                                            │   │
│  │  Secure Boot ROM (immutable)                                    │   │
│  │                                                                 │   │
│  │  🔒 PRIVATE KEYS NEVER CROSS THIS BOUNDARY                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              │ Secure Bus (optional encryption)         │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🟢 LOCKED — GENERAL COMPUTE                                     │   │
│  │                                                                 │   │
│  │  RISC-V Control Core (32-bit, minimal)                          │   │
│  │  DMA, Interrupt Controller, Timers, Watchdog                    │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🟡 PROPOSED — DSP PIPELINE (algorithm programmable)             │   │
│  │                                                                 │   │
│  │  FFT Accelerator (hardware)                                     │   │
│  │  Feature Extractor (programmable)                               │   │
│  │  MFCC / Embeddings / Learned Fingerprint (TBD)                  │   │
│  │                                                                 │   │
│  │  SRAM — Feature Buffer (size TBD)                               │   │
│  │  ROM — DSP Firmware (programmable)                              │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🟢 LOCKED — AUDIO INPUT (Architecture A choisie)                │   │
│  │                                                                 │   │
│  │  Microphone → Codec/ADC externe → I²S/PDM → FREK DSP            │   │
│  │                                                                 │   │
│  │  FREK V3 est un SoC NUMÉRIQUE PUR.                              │   │
│  │  Pas d'ADC intégré. Pas de mixed-signal.                        │   │
│  │                                                                 │   │
│  │  Interface : I²S (4 fils : BCLK, LRCLK, DATA, MCLK)             │   │
│  │            ou PDM (2 fils : CLK, DATA)                          │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🟡 PROPOSED — NVM                                               │   │
│  │                                                                 │   │
│  │  MRAM préférée (10¹⁵ cycles, low power)                         │   │
│  │  eFlash fallback (10⁵ cycles, redondance triple)                │   │
│  │  OTP — FABRIC_DATA, Helper Data hash, fuses                     │   │
│  │                                                                 │   │
│  │  🔴 PROBLÈME IDENTIFIÉ :                                        │   │
│  │  eFlash 10⁵ cycles = 100 000 preuves max.                       │   │
│  │  Pour un device en production 5 ans, c'est insuffisant.         │   │
│  │  Solution requise : wear leveling ou MRAM obligatoire.          │   │
│  │                                                                 │   │
│  │  STOCKÉ :                                                       │   │
│  │    • Monotonic Counter (rollback-resistant)                     │   │
│  │    • Helper Data (PUF reconstruction)                           │   │
│  │    • Config / Flags                                             │   │
│  │    • Firmware image (externe au Trust Domain)                   │   │
│  │                                                                 │   │
│  │  NON STOCKÉ :                                                   │   │
│  │    • DRK (jamais)                                               │   │
│  │    • AK / CK (jamais)                                          │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 🟢 LOCKED — I/O INTERFACES                                      │   │
│  │                                                                 │   │
│  │  I²C (slave, 400 kHz Fast-mode)                                 │   │
│  │  SPI (slave, mode 0, 8 MHz max)                                 │   │
│  │  UART (115200 baud, 8N1, fallback)                              │   │
│  │  GPIO (4 pins, configurable)                                    │   │
│  │                                                                 │   │
│  │  🔴 TBD : Pinout exact, assignation par pin, séquence power-up  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Secure Boot corrigé — Séparation FK / Authority Key

**❌ ERREUR v0.1 :**
```
DRK → FK → "vérifie firmware au boot"
```

**✅ CORRECTION v0.2 :**
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  FREK AUTHORITY PUBLIC KEY (FK_pub)                             │
│  ─────────────────────────────────                              │
│  Gravée en OTP lors du provisioning en usine                    │
│  Identique pour TOUS les devices d'une génération               │
│  NE dépend PAS du PUF                                           │
│  NE dérive PAS du DRK                                           │
│                                                                 │
│  Usage : vérifier la signature du firmware                      │
│                                                                 │
│  Rotation : par génération de devices (nouvelle FK_pub en OTP)  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SECURE BOOT SEQUENCE                                           │
│                                                                 │
│  1. Reset vector → ROM (immutable)                              │
│  2. ROM mesure le firmware en Flash → FIRMWARE_HASH             │
│  3. ROM vérifie sig(firmware) avec FK_pub                       │
│  4. Si valide → jump to firmware                                │
│  5. Si invalide → secure boot failure → device bloqué           │
│                                                                 │
│  FIRMWARE_HASH stocké dans registre read-only                   │
│  (accessible par le firmware, non modifiable par celui-ci)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Pourquoi c'est fondamental :**

| Approche | Problème |
|----------|----------|
| FK dérivée du DRK | Chaque device a une FK différente. Impossible de signer un firmware unique valide pour tous. |
| FK_pub d'autorité (correction) | Même FK_pub pour tous. Un firmware signé par FREK Authority fonctionne sur tous les devices. |

**La FK n'est pas une clé de device. C'est une clé d'écosystème.**

---

## 3. TRNG Subsystem — Correction terminologique

**❌ ERREUR v0.1 :**
> "TRNG (NIST SP 800-90B)"

**✅ CORRECTION v0.2 :**

```
┌─────────────────────────────────────────────────────────────────┐
│  TRNG SUBSYSTEM                                                 │
│                                                                 │
│  ┌─────────────────┐                                            │
│  │ Physical Entropy│  Source physique :                        │
│  │ Source          │  • Ring oscillators                       │
│  │                 │  • Thermal noise (amplificateur)          │
│  │                 │  • Metastability                          │
│  └────────┬────────┘                                            │
│           ↓                                                     │
│  ┌─────────────────┐                                            │
│  │ SP 800-90B      │  Évaluation et tests :                    │
│  │ Health Tests    │  • Startup tests (au boot)                │
│  │                 │  • Continuous tests (en runtime)          │
│  │                 │  • Min-entropy estimation                 │
│  └────────┬────────┘                                            │
│           ↓                                                     │
│  ┌─────────────────┐                                            │
│  │ DRBG            │  Générateur déterministe :                │
│  │ (CTR-DRBG ou    │  • Seed = entropy source + nonce          │
│  │  HMAC-DRBG)     │  • Reseed périodique                      │
│  │                 │  • Forward secrecy                        │
│  └────────┬────────┘                                            │
│           ↓                                                     │
│  ┌─────────────────┐                                            │
│  │ Random Output   │  Utilisé pour :                           │
│  │                 │  • ECDSA nonce k                          │
│  │                 │  • Blinding ECC                           │
│  │                 │  • Masquage                               │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**NIST SP 800-90B** évalue la qualité de la source d'entropie.  
**NIST SP 800-90A** définit les DRBG (Deterministic Random Bit Generators).  
**Le TRNG complet** = Source physique + Health Tests (90B) + DRBG (90A).

---

## 4. Device ID — Reformulation

**❌ FORMULATION v0.1 ambiguë :**
> "Il ne traverse jamais le Trust Domain"

**✅ CORRECTION v0.2 :**

```
DEVICE_ID
│
├── Nature : DONNÉE PUBLIQUE
├── Calcul : Truncate(SHA-256(AK_pub), 16)
├── Stockage : nulle part dans le Trust Domain (calculé à la volée)
├── Transport : inclus dans chaque FREK Proof (publique)
└── Secret requis : AUCUN
    └── La dérivation utilise AK_pub (clé publique), pas AK_priv (clé privée)
    └── Aucune donnée secrète ne quitte le Trust Domain pour produire le Device ID
```

**La bonne formulation :**

> Le Device ID est une donnée publique dérivée de la clé d'attestation publique (AK_pub). Sa production ne nécessite aucune donnée secrète et aucune opération cryptographique dans le Trust Domain. Le Device ID est inclus dans la preuve FREK comme identifiant public du dispositif, mais il n'est jamais utilisé comme secret ni comme preuve d'authenticité.

---

## 5. Compteur monotone — Problème identifié

**Le vrai problème hardware :**

| NVM | Endurance | Preuves max | Durée de vie (1 preuve/jour) |
|-----|-----------|-------------|------------------------------|
| eFlash | 10⁵ cycles | 100 000 | ~274 ans |
| eFlash | 10⁵ cycles | 100 000 | ~27 ans (10 preuves/jour) |
| eFlash | 10⁵ cycles | 100 000 | ~2,7 ans (100 preuves/jour) |
| MRAM | 10¹⁵ cycles | Illimité pratique | Illimitée |

**Pour un microphone professionnel en studio (10-100 preuves/jour) :**
- eFlash = 2,7 à 27 ans. C'est acceptable mais limite.
- MRAM = illimité. C'est la cible.

**Solutions à évaluer :**

| Solution | Description | Impact |
|----------|-------------|--------|
| **MRAM obligatoire** | Pas de fallback eFlash | Coût +, disponibilité - |
| **Wear leveling** | Compteur incrémenté par blocs de 1024 | Complexité +, endurance ×1024 |
| **Checkpointing** | Compteur sauvegardé périodiquement | Résilience power-loss + |
| **Compteur secondaire** | Compteur volatile + sync NVM périodique | Endurance ×N, risque de perte |

**Décision requise :** Définir la fréquence de certification attendue par use case avant de choisir la technologie NVM.

---

## 6. Architecture Audio A — Verrouillée comme recommandation

```
┌─────────────────────────────────────────────────────────────────┐
│  ARCHITECTURE A — RECOMMANDÉE pour FREK V3                      │
│                                                                 │
│  Microphone → Codec/ADC externe → I²S/PDM → FREK V3 DSP         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  AVANTAGES                                              │   │
│  │  • SoC numérique pur (pas de mixed-signal)              │   │
│  │  • Intégration facile (réutilise le codec existant)     │   │
│  │  • BOM client réduit                                    │   │
│  │  • Validation plus rapide                               │   │
│  │  • FPGA prototype plus simple                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  CONTRAINTES                                            │   │
│  │  • Qualité audio dépend du codec externe                │   │
│  │  • Moins de contrôle sur la chaîne complète             │   │
│  │  • Nécessite un codec I²S/PDM dans l'appareil hôte      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Interface formelle :                                           │
│    • I²S : BCLK, LRCLK, SDATA, MCLK (optionnel)               │
│    • PDM : CLK, DATA                                            │
│    • Fréquence : 48 kHz typique (configurable)                 │
│    • Profondeur : 16-24 bits (configurable)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Architecture B (ADC intégré) :** Reporté à V4 ou produit haut de gamme spécifique.

---

## 7. Checklist avant FPGA — Mise à jour v0.2

| Élément | Statut v0.2 | Bloque le FPGA ? | Commentaire |
|---------|-------------|------------------|-------------|
| FAP v0.1 | 🟢 LOCKED | Non | |
| Crypto Review v0.1 | 🟢 LOCKED | Non | |
| Engineering Exploded View | 🟢 LOCKED | Non | 4 corrections intégrées |
| Secure Boot (FK_pub authority) | 🟢 LOCKED | Non | Correction intégrée |
| TRNG Subsystem | 🟢 LOCKED | Non | Terminologie corrigée |
| Device ID formulation | 🟢 LOCKED | Non | Clarifié |
| Architecture Audio A | 🟡 RECOMMANDÉE | Non | Interface à formaliser |
| **Golden Vectors (fixes)** | ⏳ À faire | **OUI** | |
| **Rust verifier** | ⏳ À faire | **OUI** | |
| **DSP Spec v0.1** | ⏳ À faire | **OUI** | Prochain document |
| Compteur / NVM | 🟡 PROBLÈME IDENTIFIÉ | Non | MRAM vs wear leveling |
| Pinout exact | 🔴 TBD | Non | |
| Package définitif | 🔴 TBD | Non | |
| Process node | 🟡 PROPOSED | Non | |
| Power budget | 🟡 OBJECTIF | Non | |

---

## 8. Synthèse de l'état FREK V3

```
                 FREK V3
                    │
       ┌────────────┴────────────┐
       │                         │
   VERROUILLÉ                 À DÉFINIR
       │                         │
   Crypto                    DSP Spec v0.1
   Trust Domain              Golden Vectors
   PUF                       Rust Verifier
   Key hierarchy             NVM final (compteur)
   Attestation               Interfaces exactes
   Secure Boot               Power / Performance
   Device ID
   TRNG Subsystem
   Architecture Audio A
       │
       └────────────┬────────────┘
                    ↓
              FPGA PROTOTYPE
```

---

*Document verrouillé — Engineering v0.2*  
*4 corrections critiques intégrées suite à audit n°2*
