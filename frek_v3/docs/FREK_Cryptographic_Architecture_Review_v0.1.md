# FREK Cryptographic Architecture Review — v0.1
## Hardware Root of Trust, Key Derivation & Attestation Security

**Version:** 0.1.0-draft  
**Date:** 2026-08-10  
**Status:** DRAFT — Security Review  
**Classification:** Cryptographic Architecture & Threat Analysis  
**Distribution:** Semiconductor Engineering, Security Engineering, Cryptography Review Board  

---

## Résumé exécutif

Ce document définit l'architecture cryptographique de FREK V3 et corrige une construction présente dans le FREK Attestation Protocol v0.1 : **la Device Root Key ne doit en aucun cas dépendre du compteur monotone ni du hash du firmware.** Ces deux éléments sont des *données attestées* dans la preuve, pas des paramètres de dérivation clé. Mélanger les deux rôles crée une fragilité de gestion de clés, bloque les mises à jour de firmware et compromet la récupération sur incident.

Le principe fondamental est :

> **La Device Root Key est immuable et dérivée uniquement du PUF. Toute clé applicative est dérivée de cette racine via HKDF avec domain separation stricte. Le compteur et le firmware hash sont signés, jamais utilisés comme entrée de KDF.**

---

## 1. Physically Unclonable Function (PUF)

### 1.1 Choix de la technologie PUF

Deux familles de PUF sont évaluées pour FREK V3 :

| Critère | SRAM PUF | Ring Oscillator (RO) PUF |
|---------|----------|--------------------------|
| **Maturité** | Très mature (Intrinsic ID, QuantumTrace) | Mature (académique et industriel) |
| **Intégration** | Réutilise la SRAM existante du SoC | Nécessite des anneaux dédiés en silicium |
| **Entropie** | ~4-6 bits par cellule (dépend du procédé) | ~1-3 bits par paire d'anneaux |
| **Reproductibilité** | Nécessite correction d'erreur agressive | Meilleure stabilité thermique |
| **Latence d'enrollment** | Au premier boot (lecture SRAM) | Au premier boot (comptage d'oscillations) |
| **Surface silicium** | Nulle (SRAM existante) | Faible (~100-1000 anneaux) |
| **Dépendance au procédé** | Forte (22nm ULP optimisé) | Modérée |

**Recommandation FREK V3 : SRAM PUF**  
Pour un SoC ultra-low-power en 22-40nm, la SRAM PUF est préférable car elle ne consomme pas de surface additionnelle et son enrollment est naturel au premier power-on. La stabilité thermique est gérée par le fuzzy extractor (§1.4).

### 1.2 Enrollment

L'enrollment est l'opération unique effectuée lors du **premier boot** du dispositif en sortie de fabrication (ou après un effacement complet de la NVM).

```
PUF_ENROLLMENT:
    1. Power-on reset complet
    2. Attente de stabilisation thermique (≥ 100 ms à T_ambiante)
    3. Lecture de la totalité de la zone SRAM PUF (N bits)
    4. Extraction de l'entropie via Fuzzy Extractor
    5. Stockage des Helper Data en NVM (OTP/eFlash/MRAM)
    6. Destruction immédiate de toute trace de la réponse brute en SRAM volatile
    7. Verrouillage de la zone PUF (read-protect hardware)
```

**Contrainte critique** : l'enrollment ne peut être refait qu'après un **factory reset complet** avec effacement de la NVM. Toute tentative de ré-enrollment sans effacement est rejetée par le secure boot ROM.

### 1.3 Helper Data

Les Helper Data sont les données publiques produites par le fuzzy extractor permettant de reconstituer la réponse PUF exacte lors des boots suivants.

| Propriété | Spécification |
|-----------|---------------|
| **Taille** | ~1,5× à 2× la taille de la réponse brute (dépend du code correcteur) |
| **Stockage** | NVM dédiée, accessible en lecture seule après enrollment |
| **Intégrité** | Hash SHA-256 stocké en OTP séparé ; vérifié à chaque reconstruction |
| **Confidentialité** | Les Helper Data ne sont **pas** secrets (leakage acceptable) |
| **Immunité** | Doivent résister à la manipulation (si altérés, reconstruction échoue → device bloqué) |

**Code correcteur recommandé** : Code de Reed-Muller (1, m) ou BCH avec t=3-5 corrections d'erreurs pour 256 bits de secret. Le taux d'erreur brut (BER) de la SRAM PUF en 22nm est typiquement 5-15% ; le code correcteur doit ramener le taux d'échec de reconstruction (FER) sous 10⁻⁹.

### 1.4 Fuzzy Extractor

Le fuzzy extractor garantit que la réponse PUF est reproductible malgré le bruit thermique et la dérive du silicium.

```
FuzzyExtractor:
    Generate(response):
        key, helper_data = Code.Encode(response)
        return key, helper_data

    Reproduce(noisy_response, helper_data):
        corrected = Code.Decode(noisy_response, helper_data)
        return corrected  // = key si le bruit est dans la capacité de correction
```

**Paramètres suggérés** :
- **Entrée PUF** : 4096 bits de SRAM (512 octets)
- **Secret extrait** : 256 bits (32 octets)
- **Code correcteur** : BCH(511, 256, 31) ou équivalent
- **Helper Data** : 511 bits (~64 octets)
- **FER cible** : < 10⁻⁹ sur la plage température -40°C à +125°C

### 1.5 Entropie minimale

L'entropie du PUF doit être évaluée selon NIST SP 800-90B.

| Métrique | Valeur minimale | Méthode de test |
|----------|-----------------|-----------------|
| **Min-entropy par bit** | ≥ 0,7 bit/bit | Tests NIST (Most Common Value, Collision, etc.) |
| **Entropie totale (256 bits)** | ≥ 192 bits équivalentes | Post-traitement par hash (SHA-256) |
| **Unicité inter-device** | Hamming distance moyenne ≥ 45% | Mesure sur échantillon de 100+ dies |
| **Stabilité intra-device** | BER ≤ 15% avant correction | Mesure sur 1000 cycles power-on |

**Mitigation si entropie insuffisante** :  
Si les tests de production révèlent une entropie < 0,5 bit/bit, le die est marqué `PUF_WEAK` et rejeté. Le taux de rejet acceptable est fixé à < 5%.

---

## 2. Root of Trust

### 2.1 Principe de séparation des clés

La Device Root Key (DRK) ne signe **jamais** directement une preuve applicative. Elle sert uniquement à dériver des clés filles via HKDF. Cette séparation limite l'impact d'une compromission d'une clé fille et permet la rotation sélective.

```
PUF_RESPONSE (256 bits, volatile)
    ↓
Fuzzy Extractor
    ↓
IKM (Input Keying Material) — 256 bits
    ↓
HKDF-SHA256(salt=FABRIC_DATA, info="frek-v3-root")
    ↓
┌─────────────────────────────────────┐
│     DEVICE ROOT KEY (DRK)           │
│     256 bits — jamais exportée      │
│     Stockée uniquement en registres │
│     hardware du Trust Domain        │
└─────────────────────────────────────┘
    ↓
    ├── HKDF(salt=0x00, info="frek-v3-attestation")
    │       ↓
    │   ATTESTATION_KEY (AK) — signe les preuves FREK
    │
    ├── HKDF(salt=0x00, info="frek-v3-firmware")
    │       ↓
    │   FIRMWARE_KEY (FK) — vérifie les signatures de firmware
    │
    └── HKDF(salt=0x00, info="frek-v3-communication")
            ↓
        COMMUNICATION_KEY (CK) — chiffrement du bus interne (optionnel)
```

### 2.2 Device Root Key (DRK)

| Propriété | Spécification |
|-----------|---------------|
| **Source** | PUF_RESPONSE via Fuzzy Extractor |
| **Dérivation** | HKDF-SHA256(IKM=PUF, salt=FABRIC_DATA, info="frek-v3-root") |
| **Stockage** | Registres hardware du Trust Domain uniquement ; jamais en SRAM/Flash |
| **Durée de vie** | Immuable pendant toute la vie du dispositif |
| **Export** | Strictement interdit ; aucune instruction ne peut la lire |
| **Usage** | Dérivation de clés filles uniquement |

**FABRIC_DATA** : concaténation de `FABRIC_ID || WAFER_ID || DIE_X || DIE_Y || LOT_ID`. Ces données sont gravées en OTP lors du test de wafer et servent de salt pour lier la DRK à l'identité physique du die.

### 2.3 Attestation Key (AK)

| Propriété | Spécification |
|-----------|---------------|
| **Dérivation** | HKDF(DRK, salt=0x00, info="frek-v3-attestation") |
| **Usage** | Signature ECDSA des preuves FREK (L2) |
| **Export** | Interdit ; utilisée par le crypto accelerator hardware |
| **Rotation** | Non prévue (la DRK est immuable) |
| **Clé publique** | Dérivée par multiplication scalaire sur la courbe P-256 ; exportable via `GET_IDENTITY` |

**Correction par rapport au FAP v0.1** :  
Dans le FAP v0.1, la clé de signature était dérivée du compteur et du firmware hash. Cette construction est **abandonnée**. L'AK est dérivée une seule fois au boot et reste stable. Le compteur et le firmware hash sont des *champs signés*, pas des paramètres de KDF.

### 2.4 Firmware Key (FK)

| Propriété | Spécification |
|-----------|---------------|
| **Dérivation** | HKDF(DRK, salt=0x00, info="frek-v3-firmware") |
| **Usage** | Vérification de la signature du firmware au secure boot |
| **Export** | Interdit ; utilisée par le secure boot ROM |
| **Rotation** | Non prévue |

Le FK vérifie que le firmware chargé est signé par FREK Authority. La clé publique correspondante (FK_pub) est gravée en OTP et utilisée par le ROM de boot.

### 2.5 Communication Key (CK)

| Propriété | Spécification |
|-----------|---------------|
| **Dérivation** | HKDF(DRK, salt=0x00, info="frek-v3-communication") |
| **Usage** | Chiffrement optionnel du bus I²C/SPI (AES-128-GCM ou ChaCha20-Poly1305) |
| **Export** | Interdit |

Le CK est réservé pour les implémentations nécessitant une confidentialité du bus entre FREK V3 et le host (scénarios de menace élevée).

---

## 3. Key Derivation Function (KDF)

### 3.1 HKDF-SHA-256

FREK V3 utilise HKDF (RFC 5869) en deux phases : Extract puis Expand.

```
HKDF-Extract(salt, IKM):
    PRK = HMAC-SHA256(salt, IKM)
    return PRK

HKDF-Expand(PRK, info, L):
    N = ceil(L / 32)
    T = ""
    T_prev = ""
    for i = 1 to N:
        T_prev = HMAC-SHA256(PRK, T_prev || info || 0x01)
        T = T || T_prev
    return T[0:L]
```

### 3.2 Salt

| Clé | Salt | Justification |
|-----|------|---------------|
| DRK | `FABRIC_DATA` (64-128 bits) | Lie la clé racine à l'identité physique du wafer |
| AK, FK, CK | `0x00` (32 octets de zéros) | RFC 5869 recommande un salt nul quand aucune source de salt n'est disponible ; la diversification est assurée par `info` |

**Règle** : le salt de la DRK est fixe et immuable. Le salt des clés filles est nul car la diversification est entièrement portée par le paramètre `info`.

### 3.3 Info (domain separation)

Le paramètre `info` est la garantie de séparation des domaines cryptographiques. Il doit être :
- **Unique** par usage (attestation, firmware, communication)
- **Immuable** une fois défini
- **Préfixé** par un identifiant de protocole pour éviter les collisions cross-projet

```
info_attestation = "frek-v3-attestation "
info_firmware    = "frek-v3-firmware "
info_comm        = "frek-v3-communication "
```

Le suffixe ` ` (octet nul) évite les attaques par prefix collision (ex: "frek-v3-attestation" vs "frek-v3-attestation-legacy").

### 3.4 Dérivation déterministe sans exposition de la racine

La DRK n'est jamais exposée à la logique applicative. La dérivation des clés filles est effectuée par le **crypto accelerator hardware** dans le Trust Domain :

```
Boot Sequence:
    1. Power-on
    2. PUF Reproduce → IKM
    3. HKDF-Extract(FABRIC_DATA, IKM) → DRK  [dans le Trust Domain]
    4. HKDF-Expand(DRK, "frek-v3-attestation", 32) → AK  [dans le Trust Domain]
    5. HKDF-Expand(DRK, "frek-v3-firmware", 32) → FK  [dans le Trust Domain]
    6. Secure Boot (FK vérifie le firmware)
    7. Application start
```

**Aucune clé ne traverse le bus système.** Les opérations HKDF sont réalisées par un état machine hardware dédié.

---

## 4. Signature

### 4.1 ECDSA P-256

Paramètres conformes FIPS 186-4 :

| Paramètre | Valeur |
|-----------|--------|
| Courbe | NIST P-256 (secp256r1) |
| Taille de clé | 256 bits |
| Taille de signature | 512 bits (r || s, 64 octets) |
| Format | Raw (pas de DER/ASN.1) |
| Hash | SHA-256 |

### 4.2 Génération du nonce k

Le nonce `k` d'ECDSA est le point le plus critique de sécurité. Une réutilisation ou une prédictibilité de `k` expose immédiatement la clé privée (Sony PS3, 2010).

**Mode privilégié : TRNG hardware**

```
k = TRNG(256 bits)
Vérification : 1 ≤ k < n (ordre de la courbe)
Si k invalide : régénérer
```

Le TRNG hardware doit être conforme NIST SP 800-90B avec un taux d'entropie ≥ 0,99 bit/bit post-traitement.

**Mode fallback : RFC 6979 (déterministe)**

```
k = HMAC_DRBG(SHA-256, seed=private_key || message_hash)
```

RFC 6979 est utilisé en cas de défaillance du TRNG (détection par health tests). Il élimine le risque de biais du TRNG mais est déterministe (même message → même signature). C'est acceptable car le `NONCE` externe et le `COUNTER` garantissent l'unicité du message.

**Politique** :
- Par défaut : TRNG
- Si TRNG health test fail : bascule automatique sur RFC 6979
- Si les deux échouent : `SIGNATURE_FAILURE` (device bloqué)

### 4.3 Protection contre les fuites

| Contre-mesure | Implémentation |
|---------------|----------------|
| **Masquage** | Multiplication scalaire masquée (randomized projective coordinates) |
| **Blinding** | Clé privée blindée : `d' = d + r·n` avec `r` aléatoire ; signature calculée avec `d'` puis corrigée |
| **Randomisation du pattern** | Insertion de cycles dummy aléatoires dans le crypto accelerator |
| **Consommation constante** | ALU à consommation indépendante des données (WDDL ou équivalent) |
| **Isolation physique** | Trust Domain séparé par ring guard ; alimentation découplée |

### 4.4 Vérification de signature

La vérification est effectuée par le vérificateur (host, cloud, ou tiers) avec la clé publique AK_pub. L'algorithme est le standard ECDSA-Verify de FIPS 186-4.

---

## 5. Compteur monotone

### 5.1 Architecture du compteur

Le compteur est un mécanisme anti-replay critique. Il doit être :
- **Monotone strictement croissant** : jamais de décrémentation
- **Persistant** : survit au power-loss
- **Rollback-resistant** : impossible de revenir à une valeur antérieure

```
┌─────────────────────────────────────────┐
│         COUNTER ENGINE                  │
│                                         │
│  ┌─────────────┐    ┌─────────────┐     │
│  │   Shadow    │───▶│    NVM      │     │
│  │  Register   │    │  (MRAM/     │     │
│  │  (volatile) │◀───│   eFlash)   │     │
│  └─────────────┘    └─────────────┘     │
│         │                               │
│         ▼                               │
│  ┌─────────────┐                        │
│  │  Redundancy │  3 copies + majority   │
│  │   Check     │  voting                │
│  └─────────────┘                        │
└─────────────────────────────────────────┘
```

### 5.2 Stockage en NVM

**Technologie recommandée : MRAM (Magnetoresistive RAM)**

| Propriété | MRAM | eFlash | OTP |
|-----------|------|--------|-----|
| **Endurance** | 10¹⁵ cycles | 10⁵ cycles | 1 cycle |
| **Vitesse d'écriture** | ~10 ns | ~10 µs | N/A |
| **Consommation** | Très faible | Élevée (pompe de charge) | Nulle |
| **Rollback** | Possible sans protection | Possible sans protection | Impossible (écriture unique) |
| **Disponibilité 22nm** | Émergente (TSMC, Samsung) | Mature | Mature |

**Recommandation** : Si MRAM disponible, utiliser MRAM avec **monotonic counter hardware** (incrémentation atomique). Sinon, utiliser eFlash avec **redondance triple** et **majority voting**.

### 5.3 Résistance au rollback

Mécanisme de protection contre le rollback (retour à une valeur antérieure du compteur) :

```
Counter_Increment:
    1. Lire les 3 copies du compteur en NVM : C1, C2, C3
    2. Vérifier cohérence : majority(C1, C2, C3)
    3. Si incohérence → TAMPER_DETECTED
    4. Nouvelle valeur = majority + 1
    5. Écrire Nouvelle valeur dans C1, C2, C3 (séquentiel, pas atomique)
    6. Vérifier lecture après écriture
    7. Si échec → COUNTER_CORRUPTED
```

**Protection supplémentaire** :  
Le compteur est lié à la preuve via le `MESSAGE` signé. Un attaquant ne peut pas revenir à un compteur antérieur sans invalider la signature (la clé AK n'a pas changé, mais le MESSAGE contient le nouveau compteur).

### 5.4 Power-loss safety

Si une coupure de courant survient pendant l'incrémentation du compteur :
- Les copies en NVM peuvent être désynchronisées
- Au prochain boot, le majority voting restaure la valeur correcte
- Si 2 copies sur 3 sont corrompues → `COUNTER_CORRUPTED` → device bloqué

### 5.5 Usure NVM

Avec un compteur uint64 (valeur max ~1,8×10¹⁹) et une endurance eFlash de 10⁵ cycles :
- **Durée de vie** : 10⁵ preuves maximum avec eFlash
- **Solution** : MRAM (10¹⁵ cycles) ou **compteur hardware** avec wear leveling (incrémentation par bloc de 1024, compteur secondaire volatile)

**Politique** : à 90% de l'endurance, le device émet un warning `COUNTER_NEAR_EXHAUSTION`. À 100%, `COUNTER_EXHAUSTED` → blocage des preuves L2.

### 5.6 Comportement après corruption

| Scénario | Réponse du device |
|----------|-------------------|
| Compteur incohérent (majority fail) | `TAMPER_DETECTED` → blocage des preuves L2, reset du Trust Domain nécessaire |
| Compteur > MAX (débordement uint64) | `COUNTER_EXHAUSTED` → fin de vie du device |
| Compteur incrémenté mais signature échoue | `SIGNATURE_FAILURE` → retry limité à 3 fois, puis `TAMPER_DETECTED` |
| Power-loss pendant incrémentation | Recovery au boot suivant via majority voting |

---

## 6. Firmware Attestation

### 6.1 FIRMWARE_HASH

Le `FIRMWARE_HASH` dans la preuve FREK est le **hash SHA-256 du firmware en exécution**, mesuré par le secure boot ROM au moment du boot.

```
Secure Boot Sequence:
    1. Reset vector → ROM
    2. ROM mesure le firmware en Flash : FIRMWARE_HASH = SHA-256(firmware_image)
    3. ROM vérifie la signature du firmware avec FK_pub
    4. Si valide → jump to firmware
    5. Si invalide → secure boot failure → device bloqué
```

**Le FIRMWARE_HASH est une donnée, pas une clé.** Il est inclus dans le MESSAGE signé par l'AK pour attester que la preuve a été produite par un firmware spécifique et validé.

### 6.2 Secure Boot

| Étape | Description |
|-------|-------------|
| **1. ROM** | Code immuable gravé en masque ; vérifie le bootloader |
| **2. Bootloader** | Vérifie le firmware applicatif ; gère les mises à jour |
| **3. Firmware** | Application FREK (DSP, fingerprint engine, protocol handler) |

**Chaîne de confiance** : ROM (trusté par construction) → Bootloader (signé par FREK Authority) → Firmware (signé par FREK Authority).

### 6.3 Mesure du firmware

La mesure est effectuée par le ROM, pas par le firmware lui-même (auto-mesure non fiable).

```
Measure_Firmware():
    addr = FIRMWARE_BASE_ADDRESS
    size = FIRMWARE_SIZE (lu depuis l'en-tête signé)
    hash = SHA-256(Flash[addr : addr+size])
    return hash
```

Le hash est stocké dans un **registre hardware read-only** accessible par le firmware mais non modifiable par celui-ci.

### 6.4 Mise à jour de firmware (OTA)

```
Firmware_Update:
    1. Nouveau firmware reçu par le host (chiffré + signé)
    2. Bootloader vérifie la signature avec FK_pub
    3. Bootloader vérifie le version number (anti-rollback)
    4. Bootloader écrit le nouveau firmware en zone de staging
    5. Bootloader mesure le staging
    6. Bootloader copie staging → active (atomic swap)
    7. Reboot
    8. ROM mesure le nouveau firmware → nouveau FIRMWARE_HASH
```

**Anti-rollback** : le bootloader refuse d'installer un firmware avec un version number inférieur au courant. Le version number est stocké en NVM rollback-protected.

### 6.5 Rollback autorisé vs interdit

| Type de rollback | Politique |
|------------------|-----------|
| **Rollback interdit (par défaut)** | Le version number doit être strictement supérieur. Empêche les attaques par downgrade. |
| **Rollback autorisé (recovery)** | Nécessite une preuve de révocation signée par FREK Authority. Utilisé en cas de firmware corrompu ou vulnérable. |

---

## 7. Threat Model Cryptographique

### 7.1 Capacités de l'attaquant

L'attaquant est modélisé selon le modèle **DPA (Differential Power Analysis) avancé** :

- Accès physique au dispositif (décapsulation possible)
- Équipement de laboratoire (sonde EM, laser, FIB)
- Contrôle du host et du bus de communication
- Connaissance complète du protocole et du firmware (Kerckhoffs)
- Capacité à enregistrer des millions de preuves valides

### 7.2 Attaques et mitigations

| Attaque | Vecteur | Mitigation FREK V3 | Confiance |
|---------|---------|-------------------|-----------|
| **Extraction physique** | Sonde FIB sur le bus interne, lecture de la SRAM | Bus interne chiffré ; DRK dans registres hardware ; PUF volatile | Haute |
| **Probing** | Micro-sonde sur les lignes de données | Top metal shielding ; mesh de détection ; PUF réagit à la perturbation | Haute |
| **Fault injection** | Glitch d'horloge/alimentation pour sauter des vérifications | Détecteurs de glitch ; redondance temporelle ; double vérification | Haute |
| **Side-channel (power)** | DPA/CPA sur la multiplication scalaire ECDSA | Masquage ; blinding ; consommation constante ; randomisation | Haute |
| **Side-channel (EM)** | Analyse du rayonnement électromagnétique | Blindage métallique ; réduction du loop area ; fréquence d'horloge limitée | Moyenne |
| **Clonage** | Copie du firmware et usurpation d'identité | PUF : l'identité est liée au silicium physique ; impossible à cloner | Très haute |
| **Remplacement de firmware** | Flashage d'un firmware malveillant | Secure boot avec FK ; FIRMWARE_HASH signé ; anti-rollback | Haute |
| **Compromission du host** | Le host modifie les données avant envoi | La signature couvre l'ensemble du MESSAGE ; le host ne peut pas forger | Haute |
| **Replay** | Réutilisation d'une preuve valide | Compteur monotone + nonce challenge-response | Très haute |
| **Man-in-the-middle** | Interception/modification sur le bus | Signature cryptographique ; le MITM ne possède pas l'AK | Très haute |
| **Extraction de clé par signatures** | Corrélation entre signatures pour retrouver k | TRNG + RFC 6979 fallback ; vérification de l'unicité de k | Haute |

### 7.3 Scénarios d'attaque détaillés

#### Scénario A : Attaquant possède le firmware et observe des millions de preuves

**Analyse** : L'attaquant connaît AK_pub (publique), le protocole (public), et observe des signatures valides.  
**Résultat** : Sans la clé privée AK, il ne peut pas forger de nouvelles signatures. ECDSA est sûr sous l'hypothèse du logarithme discret.  
**Limite** : Si le TRNG est biaisé et que `k` est prévisible, l'attaquant peut retrouver AK par corrélation. D'où l'exigence de health tests TRNG.

#### Scénario B : Attaquant remplace le firmware par un firmware FREK modifié

**Analyse** : L'attaquant compile un firmware FREK avec une backdoor.  
**Résultat** : Le secure boot refuse de charger le firmware (signature invalide avec FK_pub). Même si l'attaquant désactive le secure boot, le FIRMWARE_HASH dans la preuve sera différent et le vérificateur peut émettre une alerte.  
**Limite** : Si l'attaquant trouve une vulnérabilité dans le bootloader permettant de bypasser FK_pub, il peut charger un firmware arbitraire. D'où la nécessité d'un bootloader minimal et audité.

#### Scénario C : Attaquant extrait le PUF d'un device mort

**Analyse** : L'attaquant décapsule un device, lit la SRAM PUF avec une sonde.  
**Résultat** : La réponse PUF dépend de la géométrie exacte des transistors, de la température, et de la tension. Une lecture destructive (décapsulation) altère la réponse. De plus, sans les Helper Data, la reconstruction est impossible.  
**Limite** : Si l'attaquant accède aux Helper Data en NVM et à la réponse PUF brute, il peut reconstruire la DRK. D'où le stockage des Helper Data dans une zone NVM séparée et protégée.

### 7.4 Trusted Computing Base (TCB) cryptographique

Le TCB se limite à :

1. **PUF + Fuzzy Extractor** : génération de l'entropie racine
2. **HKDF hardware** : dérivation des clés
3. **Secure Boot ROM** : vérification du firmware
4. **ECDSA Accelerator** : signature dans le Trust Domain
5. **TRNG** : génération de k
6. **Compteur hardware** : anti-replay

**Hors TCB** : firmware applicatif, host, bus de communication, cloud FREK, vérificateur.

---

## 8. Key Lifecycle

### 8.1 Fabrication

| Étape | Responsable | Action |
|-------|-------------|--------|
| **Wafer test** | Fondeur / FREK | Test électrique ; gravure FABRIC_DATA en OTP |
| **Packaging** | OSAT | Assemblage ; bonding ; test final |
| **Provisioning** | FREK Authority | Enrollment PUF (premier boot) ; génération des Helper Data ; verrouillage |

**Ségrégation des rôles** : le fondeur ne doit jamais avoir accès aux clés cryptographiques. Seul le PUF et les métadonnées de fabrication (publiques) sont présents au moment du wafer test.

### 8.2 Enrollment

```
Enrollment_Procedure:
    1. Device power-on en mode "factory"
    2. PUF enrollment → Helper Data générés
    3. HKDF → DRK dérivée (non exportée)
    4. AK_pub extraite et enregistrée dans la Device Identity Registry
    5. Helper Data hashé et stocké en OTP
    6. Mode "factory" verrouillé irréversiblement (fuse blown)
    7. Device prêt pour distribution
```

### 8.3 Activation

L'activation est la transition entre l'état "usine" et l'état "opérationnel". Elle peut inclure :
- La personnalisation du `DEVICE_ID` (si non fixé en usine)
- L'association à un compte FREK Network (Couche 3)
- La configuration des politiques de compteur et de timeout

### 8.4 Rotation

| Clé | Rotation possible ? | Mécanisme |
|-----|---------------------|-----------|
| **DRK** | **Non** | Immuable ; liée au PUF physique |
| **AK** | **Non** | Dérivée de la DRK ; stable |
| **FK** | **Non** | Dérivée de la DRK ; la clé publique de vérification est en OTP |
| **CK** | **Oui** | Nouvelle dérivation HKDF avec un salt de session (si chiffrement bus activé) |

**Absence de rotation pour AK/FK** : c'est une contrainte du PUF. Si une clé est compromise, le device doit être révoqué (§8.5). C'est acceptable car le coût unitaire du silicium est faible et le nombre de devices est élevé.

### 8.5 Révocation

```
Revocation:
    1. FREK Authority signe un certificat de révocation : { DEVICE_ID, REASON, TIMESTAMP }
    2. Le certificat est publié dans la FREK Revocation List (CRL distribuée)
    3. Les vérificateurs rejettent toute preuve d'un device révoqué
    4. Le device lui-même n'est pas désactivé physiquement (impossible à distance)
    5. Le device peut être recyclé via factory reset (effacement NVM + ré-enrollment)
```

### 8.6 Destruction

```
Secure_Erase:
    1. Effacement de la NVM (Helper Data, compteur, configuration)
    2. Effacement de la SRAM PUF (power-cycle rapide répété)
    3. Blown des fuses de sécurité (irréversible)
    4. Le device ne peut plus produire de preuve valide
```

---

## 9. Formalisation de la chaîne de preuve

### 9.1 Diagramme de dérivation complet

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FABRICATION                                  │
│  FABRIC_ID || WAFER_ID || DIE_X || DIE_Y || LOT_ID  →  OTP         │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ENROLLMENT (1x)                              │
│                                                                      │
│   Power-on → SRAM PUF Read → Fuzzy Extractor → IKM (256 bits)       │
│                              ↓                                       │
│                        Helper Data → NVM (OTP)                      │
│                              ↓                                       │
│   DRK = HKDF-Extract(salt=FABRIC_DATA, ikm=IKM)                     │
│   DRK = HKDF-Expand(PRK=DRK, info="frek-v3-root", L=32)             │
│                              ↓                                       │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │  DEVICE ROOT KEY (DRK) — registres hardware uniquement  │       │
│   └─────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BOOT (à chaque power-on)                     │
│                                                                      │
│   Power-on → SRAM PUF Read → Fuzzy Extractor(Helper Data) → IKM     │
│                              ↓                                       │
│   DRK = HKDF-Extract(salt=FABRIC_DATA, ikm=IKM)  [reconstituée]     │
│                              ↓                                       │
│   ┌────────────────────────────┐  ┌────────────────────────────┐    │
│   │ AK = HKDF(DRK, "attest")   │  │ FK = HKDF(DRK, "firmware")│    │
│   └────────────────────────────┘  └────────────────────────────┘    │
│                              ↓                                       │
│   Secure Boot : FK vérifie sig(firmware)                            │
│   FIRMWARE_HASH = SHA-256(firmware) → registre read-only            │
│                              ↓                                       │
│   COUNTER = read_from_NVM() → shadow register                       │
│                              ↓                                       │
│   Device Ready                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PROOF GENERATION                             │
│                                                                      │
│   HOST : GET_PROOF(NONCE)                                           │
│                              ↓                                       │
│   FREK V3 :                                                          │
│      capture audio → DSP → fingerprint                              │
│      AUDIO_HASH      = SHA-256(audio_buffer)                        │
│      FINGERPRINT_HASH = SHA-256(fingerprint_vector)                 │
│      CONTEXT_HASH    = SHA-256(metadata)                            │
│      COUNTER++                                                       │
│      DEVICE_TIME     = RTC_read()                                   │
│                              ↓                                       │
│      MESSAGE = SHA-256(                                             │
│         VERSION || LEVEL || DEVICE_ID || COUNTER || NONCE ||        │
│         DEVICE_TIME || AUDIO_HASH || FINGERPRINT_HASH ||            │
│         CONTEXT_HASH || FIRMWARE_HASH || AK_pub                     │
│      )                                                               │
│                              ↓                                       │
│      SIGNATURE = ECDSA-Sign(AK, MESSAGE)                            │
│         k = TRNG(256 bits) [ou RFC 6979 si TRNG fail]               │
│                              ↓                                       │
│      FREK_PROOF = { tous les champs || SIGNATURE }                  │
│                              ↓                                       │
│   HOST reçoit FREK_PROOF                                             │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         VÉRIFICATION (hors device)                   │
│                                                                      │
│   Vérifier :                                                         │
│      1. MAGIC, VERSION, LEVEL valides                               │
│      2. DEVICE_ID connu et non révoqué                              │
│      3. COUNTER > last_known_counter                                │
│      4. NONCE == nonce_attendu (mode challenge-response)            │
│      5. Reconstruire MESSAGE                                        │
│      6. ECDSA-Verify(AK_pub, MESSAGE, SIGNATURE) == TRUE            │
│      7. Optionnel : vérifier FIRMWARE_HASH contre whitelist         │
│                              ↓                                       │
│      Résultat : VALID / REJECT avec code d'erreur                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Invariants cryptographiques

| Invariant | Description | Vérification |
|-----------|-------------|--------------|
| **I1** | La DRK ne dépend que du PUF et des données de fabrication | Audit du hardware KDF |
| **I2** | Le compteur ne décroît jamais | Majority voting + vérification séquentielle |
| **I3** | Le nonce k d'ECDSA est unique par signature | TRNG health tests + compteur d'unicité |
| **I4** | Le firmware ne peut être chargé sans vérification FK_pub | Secure boot ROM immuable |
| **I5** | La preuve L2 est vérifiable sans accès au cloud | Algorithme ECDSA standard + clé publique |
| **I6** | L'identité du device est liée au silicium physique | PUF + FABRIC_DATA ; clonage impossible |

### 9.3 Ce que l'attaquant ne peut PAS faire

Même avec :
- ✅ Le firmware complet (open source)
- ✅ Le protocole détaillé (ce document)
- ✅ Des millions de preuves observées
- ✅ Le contrôle total du host
- ✅ L'accès physique au bus I²C/SPI

L'attaquant **ne peut pas** :
- ❌ Forger une preuve valide pour un device qu'il ne contrôle pas (sans AK)
- ❌ Cloner l'identité d'un device (sans le PUF physique exact)
- ❌ Revenir à un compteur antérieur (sans invalider la signature)
- ❌ Charger un firmware arbitraire (sans la clé privée de FREK Authority)
- ❌ Extraire la DRK du silicium (sans équipement de laboratoire invasif et destruction du device)

---

## 10. Corrections au FREK Attestation Protocol v0.1

### 10.1 Section 5.4 — Dérivation de la clé de signature (À CORRIGER)

**Texte actuel (v0.1)** :
```
DEVICE_SIGNING_KEY = HKDF-SHA256(
    ikm = DEVICE_ROOT_KEY,
    salt = COUNTER || FIRMWARE_HASH,
    info = "frek-v3-signing-key-v0.1",
    L = 32
)
```

**Problème** : La clé de signature change à chaque incrémentation de compteur ou à chaque mise à jour de firmware. Cela :
- Invalide toutes les clés publiques précédemment enregistrées
- Empêche la vérification rétrospective des preuves
- Crée une gestion de clés extrêmement fragile
- Ne permet pas de rotation contrôlée

**Correction** :
```
# La clé d'attestation est stable
ATTESTATION_KEY = HKDF-SHA256(
    ikm = DEVICE_ROOT_KEY,
    salt = 0x00,
    info = "frek-v3-attestation",
    L = 32
)

# Le compteur et le firmware hash sont des DONNÉES signées
# Ils n'entrent pas dans la dérivation de la clé
```

### 10.2 Section 4.4 — Structure du MESSAGE (À PRÉCISER)

**Précision** : Le MESSAGE signé inclut `FIRMWARE_HASH` et `COUNTER` comme données attestées, pas comme paramètres de signature. La clé AK est stable ; c'est le MESSAGE qui varie.

### 10.3 Section 5.3 — Génération de la clé (À COMPLÉTER)

**Ajout** : Documenter le Fuzzy Extractor, les Helper Data, et le rôle de FABRIC_DATA comme salt.

---

## 11. Références normatives

| Référence | Titre | Usage |
|-----------|-------|-------|
| FIPS 186-4 | Digital Signature Standard (DSS) | ECDSA P-256 |
| FIPS 180-4 | Secure Hash Standard (SHS) | SHA-256 |
| FIPS 198-1 | The Keyed-Hash Message Authentication Code (HMAC) | HMAC-SHA256 |
| NIST SP 800-90B | Recommendation for the Entropy Sources Used for Random Bit Generation | TRNG, PUF entropy |
| NIST SP 800-133 | Recommendation for Cryptographic Key Generation | Key lifecycle |
| RFC 5869 | HMAC-based Extract-and-Expand Key Derivation Function (HKDF) | KDF |
| RFC 6979 | Deterministic Usage of the Digital Signature Algorithm (DSA) | ECDSA nonce déterministe |
| ISO/IEC 20897 | Physically unclonable functions — Part 1 & 2 | PUF standardization |
| Common Criteria | CC v3.1, Part 2 & 3 | Évaluation de la sécurité |

---

## 12. Glossaire

| Terme | Définition |
|-------|------------|
| **PUF** | Physically Unclonable Function |
| **Fuzzy Extractor** | Mécanisme de correction d'erreur pour PUF |
| **Helper Data** | Données publiques permettant la reconstruction PUF |
| **DRK** | Device Root Key — clé racine immuable |
| **AK** | Attestation Key — clé de signature des preuves |
| **FK** | Firmware Key — clé de vérification du firmware |
| **CK** | Communication Key — clé de chiffrement du bus |
| **HKDF** | HMAC-based Key Derivation Function |
| **IKM** | Input Keying Material — entrée de la KDF |
| **PRK** | Pseudorandom Key — sortie de HKDF-Extract |
| **TRNG** | True Random Number Generator |
| **NVM** | Non-Volatile Memory |
| **MRAM** | Magnetoresistive RAM |
| **OTP** | One-Time Programmable |
| **TCB** | Trusted Computing Base |
| **OSAT** | Outsourced Semiconductor Assembly and Test |

---

## 13. Historique des versions

| Version | Date | Auteur | Changements |
|---------|------|--------|-------------|
| 0.1.0-draft | 2026-08-10 | FREK Security Team | Version initiale. Architecture PUF, séparation des clés, HKDF, threat model, key lifecycle. Correction de la dérivation de clé du FAP v0.1. |

---

*Ce document verrouille la chaîne cryptographique de FREK V3. Aucune implémentation (software, FPGA ou ASIC) ne doit dévier de ces spécifications sans revue formelle du Cryptography Review Board.*
