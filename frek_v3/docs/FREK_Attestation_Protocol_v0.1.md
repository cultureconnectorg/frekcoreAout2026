# FREK Attestation Protocol — v0.1
## Technical Specification — Capture, Identity & Hardware Attestation

**Version:** 0.1.0-draft  
**Date:** 2026-08-10  
**Status:** DRAFT — Internal Review  
**Classification:** Architecture & Implementation Specification  

---

## 1. Vue d'ensemble

Le FREK Attestation Protocol (FAP) définit le format standardisé, la chaîne cryptographique et les procédures de vérification permettant à un dispositif FREK de produire une preuve vérifiable de l'état d'un signal audio au moment de la capture.

Le protocole est conçu pour être :
- **Autonome** : une preuve L2 est vérifiable sans accès au cloud FREK.
- **Extensible** : trois niveaux d'attestation (L0, L1, L2) permettent une adoption progressive.
- **Résistant aux replays** : challenge-response avec compteur monotone et nonce.
- **Lié au matériel** : la preuve L2 est ancrée dans une racine de confiance matérielle (PUF).

---

## 2. Modèle architectural

### 2.1 Séparation des responsabilités

```
┌─────────────────┐     ┌─────────────────────────┐     ┌─────────────────┐
│   FREK V3       │────▶│  FREK Attestation       │────▶│  FREK Core /    │
│  (Hardware)     │     │  Protocol v0.1          │     │  Network        │
│                 │     │  (Langage standardisé)  │     │  (Services)     │
└─────────────────┘     └─────────────────────────┘     └─────────────────┘
```

- **FREK V3** : produit la preuve matérielle (capture → traitement → signature).
- **FAP v0.1** : définit le format, la sémantique et la procédure de vérification.
- **FREK Core** : enrichit, archive et contextualise la preuve (optionnel pour la vérification L2).

### 2.2 Principe fondamental

> **La preuve L2 est vérifiable de manière autonome.** Le cloud FREK enrichit et archive ; il n'est pas requis pour déterminer l'authenticité de la signature matérielle.

---

## 3. Niveaux d'attestation

### 3.1 L0 — Software Attestation

| Élément | Description |
|---------|-------------|
| `fingerprint` | Vecteur de features audio (format libre) |
| `metadata` | Informations contextuelles (format JSON/TLV) |
| `software_signature` | Signature logicielle (clé logicielle, non matérielle) |

**Garantie** : le logiciel affirme avoir produit ce fingerprint. Aucune preuve matérielle.  
**Usage** : prototypage, environnements contrôlés, rétrocompatibilité.

### 3.2 L1 — Device Attestation

| Élément | Description |
|---------|-------------|
| `fingerprint` | Vecteur de features audio |
| `metadata` | Informations contextuelles |
| `device_identity` | Identifiant unique du dispositif |
| `cryptographic_signature` | Signature ECDSA P-256 avec clé dérivée du dispositif |

**Garantie** : un dispositif identifié a signé cette preuve. La clé peut résider dans un secure element externe ou une zone sécurisée logicielle.  
**Usage** : production avec secure element externe (ATECC608B ou équivalent).

### 3.3 L2 — Hardware Attested (FREK V3 Certificate of Capture)

| Élément | Description |
|---------|-------------|
| `fingerprint` | Vecteur de features audio |
| `metadata` | Informations contextuelles |
| `device_identity` | Identifiant unique dérivé du PUF |
| `puf_derived_key` | Clé publique correspondante (incluse ou référencée) |
| `firmware_measurement` | Hash du firmware en exécution (secure boot attestation) |
| `counter` | Compteur monotone anti-replay |
| `nonce` | Nonce challenge-response |
| `signature` | Signature ECDSA P-256 sur l'ensemble |

**Garantie** : un silicium FREK V3, avec une identité physique non clonable, a capturé, traité et signé cette preuve. Le firmware n'a pas été altéré depuis le boot.  
**Usage** : production FREK V3, preuve légale, certification institutionnelle.

---

## 4. Modèle de données binaire

### 4.1 Conventions

- **Endianness** : Big-Endian (network byte order) pour tous les champs multi-octets.
- **Alignement** : Les champs sont alignés sur des frontières naturelles (pas de padding imposé).
- **Encodage des strings** : UTF-8, préfixées par leur longueur sur 1 octet (max 255 octets) ou 2 octets (max 65535).
- **Timestamps** : ISO 8601 étendu avec millisecondes, encodé UTF-8.

### 4.2 Structure du FREK Proof (L2)

```
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    MAGIC      |    VERSION    |     LEVEL     |   RESERVED    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        DEVICE_ID (16 octets)                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                     COUNTER (8 octets, uint64)                +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        NONCE (16 octets)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      DEVICE_TIME (24 octets, ISO 8601)        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      AUDIO_HASH (32 octets, SHA-256)          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    FINGERPRINT_HASH (32 octets, SHA-256)      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    CONTEXT_HASH (32 octets, SHA-256)          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   FIRMWARE_HASH (32 octets, SHA-256)          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      PUB_KEY (33 octets, P-256 compressed)    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      SIGNATURE (64 octets, ECDSA P-256)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Taille totale fixe** : 1 + 1 + 1 + 1 + 16 + 8 + 16 + 24 + 32 + 32 + 32 + 32 + 33 + 64 = **283 octets** (L2).

### 4.3 Détail des champs

| Champ | Offset | Taille | Type | Description |
|-------|--------|--------|------|-------------|
| `MAGIC` | 0 | 1 | uint8 | Valeur fixe `0x46` ('F' pour FREK) |
| `VERSION` | 1 | 1 | uint8 | Version du protocole (0x01 pour v0.1) |
| `LEVEL` | 2 | 1 | uint8 | Niveau d'attestation (0x00=L0, 0x01=L1, 0x02=L2) |
| `RESERVED` | 3 | 1 | uint8 | Réservé (0x00) |
| `DEVICE_ID` | 4 | 16 | bytes | Identifiant unique du dispositif (UUIDv4-like, 128 bits) |
| `COUNTER` | 20 | 8 | uint64 | Compteur monotone, incrémenté à chaque preuve |
| `NONCE` | 28 | 16 | bytes | Nonce fourni par le vérificateur (challenge) |
| `DEVICE_TIME` | 44 | 24 | string | Horodatage local du dispositif (ex: `2026-08-10T02:31:14.827Z`) |
| `AUDIO_HASH` | 68 | 32 | bytes | SHA-256 du buffer audio brut (ou de son hash intermédiaire) |
| `FINGERPRINT_HASH` | 100 | 32 | bytes | SHA-256 du vecteur de features extrait |
| `CONTEXT_HASH` | 132 | 32 | bytes | SHA-256 des métadonnées contextuelles |
| `FIRMWARE_HASH` | 164 | 32 | bytes | SHA-256 du firmware mesuré au boot (secure boot) |
| `PUB_KEY` | 196 | 33 | bytes | Clé publique P-256 compressée (point sur la courbe) |
| `SIGNATURE` | 229 | 64 | bytes | Signature ECDSA P-256 (r, s) sur le MESSAGE |

### 4.4 Structure du MESSAGE signé

Le MESSAGE est le hash SHA-256 de la concatération binaire des champs suivants, **dans l'ordre strict** :

```
MESSAGE = SHA-256(
    VERSION ||
    LEVEL ||
    DEVICE_ID ||
    COUNTER ||
    NONCE ||
    DEVICE_TIME ||
    AUDIO_HASH ||
    FINGERPRINT_HASH ||
    CONTEXT_HASH ||
    FIRMWARE_HASH ||
    PUB_KEY
)
```

**Remarque** : le champ `SIGNATURE` n'est évidemment pas inclus dans le MESSAGE.  
**Remarque** : le `MAGIC` et le `RESERVED` ne sont pas signés (ils servent uniquement au parsing).

---

## 5. Cryptographie

### 5.1 Courbe elliptique

- **Courbe** : NIST P-256 (secp256r1)
- **Taille de clé** : 256 bits
- **Format de clé publique** : compressé (33 octets : 0x02 ou 0x03 + x)
- **Format de signature** : raw (r || s), 64 octets, sans ASN.1/DER

### 5.2 Fonction de hachage

- **Algorithme** : SHA-256 (FIPS 180-4)
- **Usage** : hachage des données (MESSAGE) et des entrées audio/contexte

### 5.3 Génération de la clé

```
PUF_RESPONSE = PUF_Silicon_Challenge()
DEVICE_ROOT_KEY = HKDF-SHA256(
    ikm = PUF_RESPONSE,
    salt = FABRIC_ID || WAFER_ID || DIE_COORD,
    info = "frek-v3-device-root-key-v0.1",
    L = 32
)
```

- **PUF_RESPONSE** : réponse brute du PUF (SRAM PUF ou Ring Oscillator PUF).
- **FABRIC_ID, WAFER_ID, DIE_COORD** : métadonnées de fabrication injectées en OTP.
- **HKDF** : RFC 5869, extraction + expansion.
- La clé privée `DEVICE_ROOT_KEY` ne quitte jamais le Trust Domain.

### 5.4 Dérivation de la clé de signature

```
DEVICE_SIGNING_KEY = HKDF-SHA256(
    ikm = DEVICE_ROOT_KEY,
    salt = COUNTER || FIRMWARE_HASH,
    info = "frek-v3-signing-key-v0.1",
    L = 32
)
```

**Rationale** : la clé de signature est dérivée du compteur et du firmware. Si le firmware change, la clé de signature change (forward secrecy limitée). Le compteur garantit qu'une clé compromise à un instant N ne permet pas de forger des preuves antérieures.

### 5.5 Signature

```
SIGNATURE = ECDSA-Sign(
    private_key = DEVICE_SIGNING_KEY,
    message_hash = MESSAGE,
    k = TRNG(256 bits)  // nonce cryptographique, jamais réutilisé
)
```

**Exigence** : le nonce `k` d'ECDSA doit être généré par un TRNG hardware et vérifié comme unique (RFC 6979 déterministe accepté en fallback avec graine TRNG).

---

## 6. Gestion du temps

### 6.1 Principe

Le protocole distingue trois concepts temporels :

| Concept | Source | Fiabilité | Usage |
|---------|--------|-----------|-------|
| `DEVICE_TIME` | RTC interne FREK V3 | Faible (dérive possible) | Contexte local, corrélation approximative |
| `VERIFIER_TIME` | Horloge du vérificateur | Forte | Horodatage de réception/vérification |
| `EXTERNAL_TIMESTAMP` | TSA / Blockchain | Très forte | Ancrage juridique, preuve de non-antériorité |

### 6.2 Règles

1. **FREK V3 ne prétend pas fournir une horloge atomique.** Le `DEVICE_TIME` est informatif.
2. Le vérificateur **doit** enregistrer son propre `VERIFIER_TIME` lors de la réception.
3. Un écart significatif entre `DEVICE_TIME` et `VERIFIER_TIME` peut déclencher une alerte, mais ne constitue pas un rejet automatique (le dispositif peut être offline depuis longtemps).
4. Pour les preuves L2 produites en mode offline, l'ancrage `EXTERNAL_TIMESTAMP` est appliqué lors de la synchronisation.

### 6.3 Synchronisation (optionnelle)

```
VERIFIER ──▶ FREK V3 : { "cmd": "SYNC_TIME", "time": "2026-08-10T02:31:14.827Z" }
FREK V3 ──▶  VERIFIER : { "status": "OK", "drift_ms": 47 }
```

La synchronisation est une opération de convenance, pas de sécurité. La sécurité temporelle repose sur le `COUNTER` et le `NONCE`.

---

## 7. Compteur monotone et anti-replay

### 7.1 Compteur (COUNTER)

- **Type** : uint64, Big-Endian.
- **Stockage** : NVM réinscriptible résistante aux rollbacks (MRAM, eFlash avec wear leveling, ou compteur hardware dédié).
- **Initialisation** : 0x0000000000000000 en usine.
- **Incrémentation** : +1 à chaque production de preuve L2, **avant** la signature.
- **Débordement** : à 0xFFFFFFFFFFFFFFFF, le dispositif entre en état `COUNTER_EXHAUSTED` et refuse de nouvelles preuves L2.

### 7.2 Politique de vérification du compteur

Le vérificateur maintient un état par `DEVICE_ID` :

```
LAST_VALID_COUNTER[DEVICE_ID] = N

Si COUNTER_reçu <= N :
    → REJECT (REPLAY_DETECTED)
Si COUNTER_reçu > N + MAX_WINDOW :
    → REJECT (COUNTER_GAP_TOO_LARGE)  // possible reset/attaque
Sinon :
    → ACCEPT
    LAST_VALID_COUNTER[DEVICE_ID] = COUNTER_reçu
```

**MAX_WINDOW** : configurable, valeur par défaut 1000.

### 7.3 Nonce (NONCE)

- **Taille** : 128 bits (16 octets).
- **Génération** : par le vérificateur (challenge-response) ou par le dispositif en mode autonome (TRNG).
- **Usage en mode challenge-response** :
  ```
  VERIFIER génère NONCE aléatoire
  FREK V3 inclut NONCE dans la preuve
  VERIFIER vérifie que NONCE == NONCE_attendu
  ```
- **Usage en mode autonome** :
  ```
  FREK V3 génère NONCE interne (TRNG)
  Le vérificateur vérifie l'unicité dans une fenêtre temporelle
  ```

---

## 8. Protocole de communication

### 8.1 Transport

FREK V3 communique avec le host via :
- **I²C** : mode esclave, adresse configurable (défaut 0x50), vitesse 400 kHz (Fast-mode).
- **SPI** : mode esclave, CPOL=0, CPHA=0, vitesse max 8 MHz.
- **UART** : 115200 baud, 8N1 (fallback).

### 8.2 Protocole de commandes (I²C/SPI)

Toutes les commandes suivent un format TLV (Type-Length-Value) :

```
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     CMD       |     STATUS    |          LENGTH               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                           PAYLOAD                             +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Champ | Taille | Description |
|-------|--------|-------------|
| `CMD` | 1 | Code de commande |
| `STATUS` | 1 | Code de retour (0x00 = OK) |
| `LENGTH` | 2 | Taille du payload en octets (Big-Endian) |
| `PAYLOAD` | variable | Données spécifiques à la commande |

### 8.3 Commandes principales

#### `0x01` — GET_IDENTITY

**Requête** (host → FREK V3) :
```
CMD = 0x01, STATUS = 0x00, LENGTH = 0x0000
```

**Réponse** (FREK V3 → host) :
```
CMD = 0x01, STATUS = 0x00
PAYLOAD = {
    DEVICE_ID (16),
    PUB_KEY (33),
    FIRMWARE_HASH (32),
    PROTOCOL_VERSION (1)
}
```

#### `0x02` — GET_PROOF (mode challenge-response)

**Requête** :
```
CMD = 0x02, STATUS = 0x00
PAYLOAD = {
    NONCE (16),
    TIMEOUT_MS (2)  // temps max d'attente
}
```

**Réponse** :
```
CMD = 0x02, STATUS = 0x00
PAYLOAD = {
    FREK_PROOF (283 octets pour L2)
}
```

**Flux** :
```
HOST ──▶ FREK V3 : GET_PROOF(NONCE)
FREK V3 : capture audio (durée configurable, défaut 2048 samples @ 48kHz)
FREK V3 : DSP → Fingerprint
FREK V3 : COUNTER++
FREK V3 : sign(MESSAGE)
FREK V3 ──▶ HOST : FREK_PROOF
```

#### `0x03` — GET_PROOF_AUTONOMOUS (mode offline)

Identique à `0x02`, mais sans NONCE externe. Le NONCE est généré par le TRNG interne.

#### `0x04` — SYNC_TIME

**Requête** :
```
CMD = 0x04, STATUS = 0x00
PAYLOAD = {
    TIMESTAMP (24, ISO 8601)
}
```

**Réponse** :
```
CMD = 0x04, STATUS = 0x00
PAYLOAD = {
    DRIFT_MS (4, int32, Big-Endian)
}
```

#### `0x05` — GET_STATUS

**Réponse** :
```
PAYLOAD = {
    STATUS_FLAGS (1) :
        bit 0 : SECURE_BOOT_OK
        bit 1 : PUF_OK
        bit 2 : TRNG_OK
        bit 3 : COUNTER_OK
        bit 4 : FIRMWARE_VALID
        bit 5 : TAMPER_DETECTED
        bit 6 : COUNTER_EXHAUSTED
        bit 7 : RESERVED
    UPTIME_MS (8, uint64)
    PROOF_COUNT (8, uint64)
}
```

### 8.4 Codes d'erreur

| Code | Nom | Description |
|------|-----|-------------|
| `0x00` | `OK` | Succès |
| `0x01` | `INVALID_CMD` | Commande inconnue |
| `0x02` | `INVALID_LENGTH` | Payload trop court/long |
| `0x03` | `INVALID_NONCE` | Nonce malformé ou réutilisé |
| `0x04` | `COUNTER_EXHAUSTED` | Compteur au maximum |
| `0x05` | `TAMPER_DETECTED` | Détection d'intrusion matérielle |
| `0x06` | `PUF_FAILURE` | Échec de lecture du PUF |
| `0x07` | `TRNG_FAILURE` | Échec du générateur aléatoire |
| `0x08` | `SIGNATURE_FAILURE` | Échec de la signature (erreur interne) |
| `0x09` | `TIMEOUT` | Délai de capture dépassé |
| `0x0A` | `FIRMWARE_INVALID` | Secure boot échoué |
| `0x0B` | `BUSY` | Dispositif occupé (preuve en cours) |
| `0x0C` | `LEVEL_NOT_SUPPORTED` | Niveau d'attestation non disponible |

---

## 9. Mode offline

### 9.1 Scénario

Dispositif FREK V3 utilisé dans un environnement sans connectivité (studio, festival, terrain).

### 9.2 Comportement

1. Le dispositif fonctionne en mode autonome (`GET_PROOF_AUTONOMOUS`).
2. Le `NONCE` est généré par le TRNG interne.
3. Le `DEVICE_TIME` est maintenu par le RTC interne.
4. Les preuves sont stockées dans une mémoire tampon locale (SRAM/Flash externe).
5. Lors de la synchronisation avec le vérificateur :
   - Le vérificateur vérifie la signature de chaque preuve.
   - Le vérificateur vérifie la monotonie des compteurs.
   - Le vérificateur vérifie l'unicité des nonces internes.
   - Le vérificateur ajoute `VERIFIER_TIME` et éventuellement `EXTERNAL_TIMESTAMP`.

### 9.3 Risques et mitigations

| Risque | Mitigation |
|--------|------------|
| Dérive du RTC | `VERIFIER_TIME` corrige à posteriori ; écart toléré configurable |
| Replay de preuves offline | Compteur monotone + nonce interne unique |
| Saturation de la mémoire tampon | Politique FIFO ou rejet ; alerte via `STATUS_FLAGS` |
| Altération de la mémoire tampon externe | Les preuves sont signées ; toute altération invalide la signature |

---

## 10. Vérification côté FREK Core

### 10.1 Algorithme de vérification

```python
def verify_proof(proof_bytes, device_registry, last_counters, trusted_pubkeys):
    # 1. Parsing
    magic = proof_bytes[0]
    assert magic == 0x46, "INVALID_MAGIC"

    version = proof_bytes[1]
    assert version == 0x01, "UNSUPPORTED_VERSION"

    level = proof_bytes[2]
    assert level == 0x02, "LEVEL_NOT_SUPPORTED"  # ou 0x01, 0x00 selon config

    # 2. Extraction des champs
    device_id = proof_bytes[4:20]
    counter = int.from_bytes(proof_bytes[20:28], 'big')
    nonce = proof_bytes[28:44]
    device_time = proof_bytes[44:68].decode('utf-8').strip(' ')
    audio_hash = proof_bytes[68:100]
    fingerprint_hash = proof_bytes[100:132]
    context_hash = proof_bytes[132:164]
    firmware_hash = proof_bytes[164:196]
    pub_key = proof_bytes[196:229]
    signature = proof_bytes[229:293]

    # 3. Vérification du compteur
    last_counter = last_counters.get(device_id, 0)
    assert counter > last_counter, "REPLAY_DETECTED"
    assert counter <= last_counter + MAX_WINDOW, "COUNTER_GAP_TOO_LARGE"

    # 4. Vérification de la clé publique (optionnel, si registry utilisée)
    if device_registry:
        assert pub_key == device_registry[device_id], "UNKNOWN_DEVICE"

    # 5. Reconstruction du MESSAGE
    message = sha256(
        bytes([version, level]) +
        device_id +
        counter.to_bytes(8, 'big') +
        nonce +
        device_time.encode('utf-8').ljust(24, b' ') +
        audio_hash +
        fingerprint_hash +
        context_hash +
        firmware_hash +
        pub_key
    )

    # 6. Vérification ECDSA
    assert ecdsa_verify(pub_key, message, signature), "INVALID_SIGNATURE"

    # 7. Mise à jour de l'état
    last_counters[device_id] = counter

    # 8. Enrichissement
    verifier_time = datetime.utcnow().isoformat()

    return {
        "status": "VALID",
        "device_id": device_id.hex(),
        "counter": counter,
        "device_time": device_time,
        "verifier_time": verifier_time,
        "firmware_hash": firmware_hash.hex(),
        "audio_hash": audio_hash.hex(),
        "fingerprint_hash": fingerprint_hash.hex()
    }
```

### 10.2 Vérification sans cloud

Une preuve L2 peut être vérifiée avec uniquement :
- La clé publique du dispositif (obtenue via `GET_IDENTITY` ou registry locale).
- L'algorithme ECDSA P-256 + SHA-256 (disponible dans OpenSSL, libsodium, etc.).
- L'état du compteur pour ce dispositif.

Aucun appel à FREK Core n'est nécessaire.

---

## 11. Versioning et évolutivité

### 11.1 Version du protocole

- Le champ `VERSION` (1 octet) permet la compatibilité ascendante.
- `0x01` = v0.1 (présente spécification).
- Les versions futures peuvent étendre le format (champs optionnels en fin de structure, TLV interne).

### 11.2 Règles de compatibilité

| Scénario | Comportement |
|----------|--------------|
| Vérificateur reçoit preuve VERSION+1 | Rejeter ou accepter selon politique (configurable) |
| Vérificateur reçoit preuve VERSION-1 | Accepter si supporté, sinon rejeter avec `UNSUPPORTED_VERSION` |
| FREK V3 reçoit commande inconnue | Retourner `INVALID_CMD` |

### 11.3 Extensibilité

Les champs `RESERVED` (actuellement 1 octet) et les extensions TLV dans le payload permettent d'ajouter :
- Nouveaux algorithmes de signature (Ed25519, BLS12-381).
- Nouveaux niveaux d'attestation (L3 avec TEE, L4 avec enclave SGX/SEV).
- Métadonnées enrichies (GPS, température, humidité — capteurs additionnels).

---

## 12. Threat Model

### 12.1 Capacités de l'attaquant

L'attaquant est modélisé comme ayant accès à :
- **Le bus de communication** (I²C/SPI/UART) entre FREK V3 et le host.
- **Le firmware du host** (potentiellement compromis).
- **Le réseau** entre le host et FREK Core.
- **Des équipements de laboratoire** (oscilloscope, analyseur logique, sonde EM).

L'attaquant **n'a pas** accès à :
- L'intérieur du Trust Domain de FREK V3 (silicium, PUF, TRNG).
- La clé privée dérivée du PUF.

### 12.2 Attaques dans le périmètre

| Attaque | Vecteur | Mitigation dans FAP v0.1 |
|---------|---------|--------------------------|
| **Replay** | Enregistrer et rejouer une preuve valide | Compteur monotone + nonce challenge-response |
| **Man-in-the-middle** | Intercepter/modifier la preuve sur le bus | Signature cryptographique sur l'ensemble |
| **Clonage** | Copier le firmware et usurper l'identité | PUF : l'identité est liée au silicium physique |
| **Rollback firmware** | Installer un firmware ancien/vulnérable | `FIRMWARE_HASH` signé ; secure boot |
| **Fault injection** | Perturber l'alimentation/horloge pour sauter des vérifications | Contre-mesures matérielles (détection de glitch, redondance) |
| **Side-channel** | Analyser la consommation/EM pendant la signature | Masquage, randomisation, blinding ECC |
| **Extraction de clé** | Sonder le bus interne ou la mémoire | Clé jamais exportée ; bus interne chiffré ; PUF volatile |
| **Déni de service** | Saturer le dispositif de requêtes | Rate limiting ; `BUSY` status ; compteur protégé |

### 12.3 Attaques hors périmètre

| Attaque | Commentaire |
|---------|-------------|
| Compromission du host | Le host peut mentir sur le contexte, mais pas sur la preuve matérielle. Le `CONTEXT_HASH` est signé par le V3, pas par le host. |
| Compromission de FREK Core | La vérification L2 reste possible offline. Le cloud n'est pas dans la TCB (Trusted Computing Base). |
| Attaque sur la chaîne de fabrication | Mitigée par le PUF + les métadonnées de fabrication en OTP. Un clone nécessite le silicium physique exact. |

### 12.4 Trusted Computing Base (TCB)

Le TCB de FAP v0.1 se limite à :
1. Le silicium FREK V3 (PUF, TRNG, crypto accelerator, secure boot ROM).
2. L'algorithme de vérification ECDSA P-256 + SHA-256 (implémentation auditée).
3. La clé publique du dispositif (obtenue de manière fiable).

Le host, le cloud, et le réseau sont **hors TCB**.

---

## 13. Vecteurs de test

### 13.1 Test 1 : Preuve L2 valide (challenge-response)

**Entrées** :
- `NONCE` = `A83F9E2B1C4D5E6F7A8B9C0D1E2F3A4B` (hex)
- `DEVICE_ID` = `F3E2D1C0B9A8F7E6D5C4B3A291807060` (hex)
- `COUNTER` = 18472 (0x0000000000004828)
- `DEVICE_TIME` = `2026-08-10T02:31:14.827Z`
- `AUDIO_HASH` = SHA-256("test_audio_buffer_48kHz_mono")
- `FINGERPRINT_HASH` = SHA-256("test_fingerprint_vector")
- `CONTEXT_HASH` = SHA-256("{"location":"Studio_A","gain":12.5}")
- `FIRMWARE_HASH` = SHA-256("frek_v3_fw_v1.0.3.bin")
- Clé privée (test) : `0x1234...` (P-256)

**Opération** :
```
MESSAGE = SHA-256(0x01 || 0x02 || DEVICE_ID || COUNTER || NONCE || 
                  DEVICE_TIME || AUDIO_HASH || FINGERPRINT_HASH || 
                  CONTEXT_HASH || FIRMWARE_HASH || PUB_KEY)
SIGNATURE = ECDSA-Sign(PRIV_KEY, MESSAGE)
```

**Vérification attendue** : `VALID`

### 13.2 Test 2 : Replay attack

**Scénario** : Rejouer la preuve du Test 1 avec le même `COUNTER` et `NONCE`.

**Vérification attendue** : `REPLAY_DETECTED` (COUNTER non supérieur au dernier connu).

### 13.3 Test 3 : Nonce mismatch

**Scénario** : Le vérificateur envoie `NONCE = AAAA...`, la preuve contient `NONCE = BBBB...`.

**Vérification attendue** : `INVALID_NONCE` (si le vérificateur vérifie le nonce attendu).

### 13.4 Test 4 : Firmware tampered

**Scénario** : La preuve contient un `FIRMWARE_HASH` différent de celui attendu.

**Vérification attendue** : La signature est valide (le V3 signe ce qu'il voit), mais le vérificateur peut émettre une alerte `FIRMWARE_MISMATCH` (politique applicative, non protocole).

### 13.5 Test 5 : Clé publique inconnue

**Scénario** : La `PUB_KEY` ne correspond à aucun dispositif enregistré.

**Vérification attendue** : `UNKNOWN_DEVICE` (si registry activée).

---

## 14. Exemple de preuve complète (hex dump)

```
Offset  0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F

0000   46 01 02 00  F3 E2 D1 C0 B9 A8 F7 E6 D5 C4 B3 A2   F.............
0010   91 80 70 60  00 00 00 00 00 00 48 28  A8 3F 9E 2B   ..p`......H(.?.
0020   1C 4D 5E 6F  7A 8B 9C 0D 1E 2F 3A 4B  32 30 32 36   .M^oz..../:K2026
0030   2D 30 38 2D  31 30 54 30 32 3A 33 31  3A 31 34 2E   -08-10T02:31:14.
0040   38 32 37 5A  00 00 00 00 00 00 00 00  00 00 00 00   827Z............
0050   00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00   ................
0060   00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00   ................
0070   00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00   ................
0080   00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00   ................
0090   00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00   ................
00A0   00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00   ................
00B0   00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00   ................
00C0   00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00   ................
00D0   00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00   ................
00E0   00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00   ................
00F0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0100   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0110   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0120   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0130   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0140   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0150   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0160   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0170   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0180   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0190   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
01A0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
01B0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
01C0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
01D0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
01E0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
01F0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0200   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0210   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0220   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0230   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0240   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0250   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0260   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0270   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0280   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0290   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
02A0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
02B0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
02C0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
02D0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
02E0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
02F0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0300   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0310   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0320   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0330   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0340   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0350   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0360   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0370   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0380   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
0390   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
03A0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
03B0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
03C0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
03D0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
03E0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
03F0   00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00   ................
```

*Note : L'exemple ci-dessus utilise des valeurs fictives pour les hashes et la signature. Les octets `00` représentent les champs non initialisés dans cet exemple abrégé. Une preuve réelle contiendrait des valeurs SHA-256 et une signature ECDSA valides.*

---

## 15. Références normatives

| Référence | Titre | Usage |
|-----------|-------|-------|
| FIPS 180-4 | Secure Hash Standard (SHS) | SHA-256 |
| FIPS 186-4 | Digital Signature Standard (DSS) | ECDSA P-256 |
| FIPS 198-1 | The Keyed-Hash Message Authentication Code (HMAC) | HMAC-SHA256 |
| RFC 5869 | HMAC-based Extract-and-Expand Key Derivation Function (HKDF) | KDF |
| RFC 6979 | Deterministic Usage of the Digital Signature Algorithm (DSA) | ECDSA nonce déterministe |
| NIST SP 800-90B | Recommendation for the Entropy Sources Used for Random Bit Generation | TRNG |
| ISO 8601 | Data elements and interchange formats — Information interchange | Timestamps |
| I²C-bus specification | NXP Semiconductors, Rev. 6 | I²C transport |

---

## 16. Glossaire

| Terme | Définition |
|-------|------------|
| **FAP** | FREK Attestation Protocol (ce document) |
| **FREK Proof** | Structure de données signée attestant d'une capture audio |
| **PUF** | Physically Unclonable Function — fonction physique non clonable |
| **TRNG** | True Random Number Generator — générateur de nombres aléatoires hardware |
| **NVM** | Non-Volatile Memory — mémoire non volatile |
| **RTC** | Real-Time Clock — horloge temps réel |
| **TCB** | Trusted Computing Base — base de calcul de confiance |
| **OTP** | One-Time Programmable — programmable une seule fois |
| **BOM** | Bill of Materials — nomenclature |
| **NRE** | Non-Recurring Engineering — coûts de développement non récurrents |

---

## 17. Historique des versions

| Version | Date | Auteur | Changements |
|---------|------|--------|-------------|
| 0.1.0-draft | 2026-08-10 | FREK Architecture Team | Version initiale. Architecture L0/L1/L2, format binaire, protocole I²C/SPI, threat model. |

---

*Document généré pour l'architecture FREK V3. Ce protocole transforme l'architecture matérielle en langage standardisé implémentable par des équipes hardware, cryptographiques et backend indépendamment.*
