# FREK V3 — Réconciliation Architecture
## Hardware Baseline réaligné sur l'écosystème FREK existant

**Version :** 0.2.0-reconciled  
**Date :** 2026-08-10  
**Statut :** ARCHITECTURE VALIDÉE — Baseline hardware conservée, couche crypto/proof réalignée  
**Principe :** La puce ne crée pas un nouveau système de confiance. Elle devient un producteur matériel de preuves FREK natives.

---

## 1. La vision corrigée

### Avant (erreur)

```
FREK V3 (hardware)  ──preuve binaire propriétaire──►  Vérificateur Rust (nouveau)
     │                                                      │
     └── PUF → ECDSA P-256 → Device ID → FAP v0.1 ──────────┘
```

**Problème :** Système parallèle, incompatible avec l'écosystème FREK existant.

### Après (réconciliation)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ÉCOSYSTÈME FREK UNIVERSEL                            │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  FREK-ID    │  │ FREK-Chain  │  │     VC      │  │  Vérificateurs│   │
│  │ did:frek:*  │  │ OTS + BTC   │  │ Ed25519     │  │ Python/JS   │   │
│  │             │  │             │  │ SD-JWT      │  │ Offline     │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │           │
│         └────────────────┼────────────────┼────────────────┘           │
│                          │                │                            │
│                          ▼                ▼                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    FREKCORE (infrastructure universelle)          │   │
│  │                                                                 │   │
│  │  • notary    • passport    • did    • eudi    • standards      │   │
│  │  • seal      • spec        • FREK-Chain    • OTS anchoring     │   │
│  │                                                                 │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │  KORA (extérieure, consomme via API comme les autres)   │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          ▲                                             │
│                          │                                             │
│  ┌───────────────────────┴─────────────────────────────────────────┐   │
│  │                    FREK V3 / LUCIOLE (racine matérielle)        │   │
│  │                                                                 │   │
│  │  PUF → Trust Domain → Ed25519 → did:frek:<id>                  │   │
│  │    ↓                                                            │   │
│  │  DSP / FFT / MFCC / Fingerprint                                 │   │
│  │    ↓                                                            │   │
│  │  FREK Capture VC (signée matériellement)                        │   │
│  │    ↓                                                            │   │
│  │  FREKCORE ←── même protocole, même crypto, même identité ──────┘   │
│  │                                                                 │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │  PREMIER CAS D'USAGE : musique / audio                  │   │   │
│  │  │  FUTURS CAS D'USAGE : capteurs IoT, vidéo, biométrie,   │   │   │
│  │  │                       objets physiques, documents...    │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ce qui est conservé du travail V3

| Élément | Statut | Justification |
|---------|--------|---------------|
| **PUF / racine matérielle** | 🟢 CONSERVÉ | Le cœur de la confiance hardware. Identité liée au silicium. |
| **Trust Domain** | 🟢 CONSERVÉ | Séparation physique entre secrets et logique applicative. |
| **Secure Boot** | 🟢 CONSERVÉ | FK_pub d'autorité pour valider le firmware. |
| **Compteur monotone** | 🟢 CONSERVÉ | Anti-replay dans la VC (champ `counter`). |
| **DSP / FFT / MFCC** | 🟢 CONSERVÉ | Pipeline audio pour produire le fingerprint. |
| **Architecture hardware** | 🟢 CONSERVÉ | SoC, RISC-V, accélérateurs, I/O. |
| **FPGA → ASIC** | 🟢 CONSERVÉ | Feuille de route inchangée. |
| **Golden Vectors** | 🟡 ADAPTÉ | Format VC au lieu de preuve binaire. |

---

## 3. Ce qui est réaligné

| Élément | Avant (erreur) | Après (réconciliation) |
|---------|----------------|------------------------|
| **Courbe** | ECDSA P-256 | **Ed25519** (compatible FREK existant) |
| **Format de preuve** | Binaire propriétaire 283 octets | **VC JSON-LD** (W3C standard) |
| **Identité** | Device ID dérivé de AK_pub | **DID:frek:<device_id>** (existant) |
| **Signature** | ECDSA raw (r‖s) | **Ed25519Signature2020** |
| **Ancrage** | Autonome (pas de cloud) | **FREK-Chain + OTS + Bitcoin** (existant) |
| **Vérification** | Rust verifier (nouveau) | **Vérificateurs Python/JS existants** |
| **Selective disclosure** | Non | **SD-JWT VC** (existant) |
| **Interopérabilité** | Protocole FREK propriétaire | **OID4VCI + EUDI + mDL + CARICOM** (existant) |

---

## 4. La VC matérielle produite par la puce

### Format

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://frek.id/vc/v1"
  ],
  "id": "urn:uuid:f3e2d1c0-b9a8-f7e6-d5c4-b3a291807060",
  "type": ["VerifiableCredential", "FREKCaptureCredential"],
  "issuer": "did:frek:device-f3e2d1c0b9a8f7e6",
  "issuanceDate": "2026-08-10T18:00:00Z",
  "credentialSubject": {
    "id": "did:frek:device-f3e2d1c0b9a8f7e6",
    "captureType": "audio",
    "audioFingerprint": {
      "algorithm": "frek-dsp-v1",
      "hash": "sha256:3a7f8b2c...",
      "parameters": {
        "sampleRate": 48000,
        "bitDepth": 24,
        "windowSize": 2048,
        "hopSize": 1024,
        "mfccBands": 40,
        "mfccCoefficients": 13
      }
    },
    "captureTimestamp": "2026-08-10T18:00:00.000Z",
    "deviceTime": "2026-08-10T18:00:00.827Z",
    "firmwareVersion": "frek-v3-fw-v1.0.3",
    "firmwareHash": "sha256:9e4d2c1b...",
    "hardwareCounter": 18472,
    "nonce": "a83f9e2b1c4d5e6f7a8b9c0d1e2f3a4b5"
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-08-10T18:00:00.827Z",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "did:frek:device-f3e2d1c0b9a8f7e6#key-1",
    "proofValue": "z58D..."
  }
}
```

### Champs produits matériellement (Trust Domain)

| Champ | Source | Produit par |
|-------|--------|-------------|
| `issuer` | DID:frek dérivé du PUF | Trust Domain |
| `audioFingerprint.hash` | SHA-256(fingerprint DSP) | Trust Domain |
| `captureTimestamp` | RTC interne | Trust Domain |
| `deviceTime` | RTC interne | Trust Domain |
| `firmwareVersion` | Registre read-only (ROM) | Trust Domain |
| `firmwareHash` | SHA-256(firmware mesuré au boot) | Trust Domain |
| `hardwareCounter` | Compteur monotone NVM | Trust Domain |
| `nonce` | TRNG (challenge-response) | Trust Domain |
| `proof.proofValue` | Ed25519Sign(private_key, canonicalized VC) | Trust Domain |

### Champs ajoutés par FREKCORE (post-capture)

| Champ | Ajouté par | Quand |
|-------|-----------|-------|
| `id` (URN UUID) | FREKCORE | Réception de la VC |
| `issuanceDate` | FREKCORE | Réception de la VC |
| `proof.created` | FREKCORE | Normalisation du timestamp |
| `frekChainAnchor` | FREKCORE | Inclusion dans FREK-Chain |
| `otsAnchor` | FREKCORE | Génération OTS |
| `bitcoinAnchor` | FREKCORE | Confirmation Bitcoin |

---

## 5. Le flux complet corrigé

```
PHYSIQUE                              HARDWARE                            FREKCORE
   │                                     │                                   │
   │ Son (air)                         │                                   │
   ▼                                     ▼                                   │
Microphone ──► Codec/ADC ──► I²S/PDM ──► FREK V3 DSP                      │
   │                                     │                                   │
   │                                     ├── FFT 2048                        │
   │                                     ├── Mel-filterbank 40               │
   │                                     ├── MFCC 13                         │
   │                                     ├── RMS/ZCR/Centroid/Flux/Rolloff   │
   │                                     ▼                                   │
   │                                 Fingerprint (36 octets)                 │
   │                                     │                                   │
   │                                     ├── SHA-256(fingerprint)            │
   │                                     ├── Read RTC                        │
   │                                     ├── Read counter                    │
   │                                     ├── Read firmware hash              │
   │                                     ├── Generate nonce (TRNG)           │
   │                                     ▼                                   │
   │                                 VC JSON-LD (canonique)                  │
   │                                     │                                   │
   │                                     ├── Ed25519Sign(private_key, VC)    │
   │                                     ▼                                   │
   │                                 FREK Capture VC signée                  │
   │                                     │                                   │
   │                                     └──────────────────────────────────►│
   │                                                                         │
   │                                                                         ├── Validation VC
   │                                                                         │   (signature Ed25519)
   │                                                                         │   (DID:frek résolution)
   │                                                                         │   (counter anti-replay)
   │                                                                         │
   │                                                                         ├── Inclusion FREK-Chain
   │                                                                         │   (bloc interne)
   │                                                                         │
   │                                                                         ├── OTS Generation
   │                                                                         │   (one-time signature)
   │                                                                         │
   │                                                                         ├── Bitcoin Anchor
   │                                                                         │   (confirmation)
   │                                                                         │
   │                                                                         └── VC enrichie
   │                                                                             (ancrages ajoutés)
   │                                                                             ▼
   │                                                                         Vérificateur offline
   │                                                                             (Python/JS)
   │                                                                             ▼
   │                                                                         Validation complète
   │                                                                             (signature + chaine + BTC)
```

---

## 6. La relation KORA / FREKCORE

```
┌─────────────────────────────────────────────────────────────────┐
│                         FREKCORE                                │
│              (infrastructure universelle, neutre)               │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  FREK-ID    │  │ FREK-Chain  │  │  Verifiable Credentials │ │
│  │  did:frek   │  │  OTS + BTC  │  │  Ed25519 / SD-JWT       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  API publique (REST / DIDComm / OID4VCI)               │   │
│  └─────────────────────────────────────────────────────────┘   │
│       ▲              ▲              ▲              ▲           │
│       │              │              │              │            │
│       │              │              │              │            │
│  ┌────┴────┐   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐       │
│  │  KORA   │   │  EUDI   │   │ ID4Africa│   │ CARICOM │       │
│  │ (CVLN)  │   │ (wallet)│   │ (wallet) │   │ (wallet)│       │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘       │
│                                                                 │
│  KORA = consommatrice d'API FREKCORE, comme les autres         │
│  KORA ≠ propriétaire de FREKCORE                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Règle :** KORA consomme les services FREKCORE via API. Elle n'est pas dans FREKCORE. FREKCORE est neutre et universel.

---

## 7. Les cas d'usage

### Premier cas d'usage (V3) : Musique / Audio

```
DJ Mix ──► Microphone ──► FREK V3 ──► VC "FREKCaptureCredential" ──► FREK-Chain
```

**Attestation :** "Ce mix a été capturé par cet appareil à cet instant, avec cette version firmware, et cette empreinte audio."

### Futurs cas d'usage (V4+) : Universel

| Capteur | VC produite | Usage |
|---------|-------------|-------|
| **Microphone** | FREKCaptureCredential (audio) | Musique, broadcast, preuve légale |
| **Caméra** | FREKCaptureCredential (vidéo) | Preuve visuelle, deepfake detection |
| **Capteur IoT** | FREKCaptureCredential (données) | IoT authentifié, supply chain |
| **Biométrie** | FREKCaptureCredential (biométrie) | Identité physique vérifiée |
| **Document scanner** | FREKCaptureCredential (document) | Authenticité documentaire |

**La puce est une racine matérielle universelle. Le premier capteur est l'audio.**

---

## 8. Ce qui est archivé vs ce qui est en cours

### Archivé (Baseline v0.1 hardware)

| Document | Statut |
|----------|--------|
| FAP v0.1 (binaire 283 octets) | ❌ OBSOLÈTE — remplacé par VC JSON-LD |
| Crypto Review v0.1 (ECDSA P-256) | 🟡 ADAPTÉ — Ed25519 à la place |
| Engineering Exploded View v0.2 | 🟢 CONSERVÉ — architecture hardware valide |
| DSP Spec v0.1 | 🟢 CONSERVÉ — pipeline audio valide |
| Python verifier (ECDSA) | 🟡 ADAPTÉ — parser VC Ed25519 |

### En cours (Réconciliation v0.2)

| Document | Statut |
|----------|--------|
| FREK VC Hardware Spec v0.1 | ⏳ À rédiger — format exact de la VC matérielle |
| Ed25519 dans Trust Domain | ⏳ À spécifier — dérivation PUF → Ed25519 |
| Golden Vectors (VC Ed25519) | ⏳ À générer — clés fixes, VC fixes |
| Rust verifier (VC Ed25519) | ⏳ À implémenter — parser VC, vérifier Ed25519 |
| Intégration FREK-Chain | ⏳ À spécifier — VC → bloc → OTS → BTC |

---

## 9. Message final

> **FREK V3 n'est pas un nouveau système de confiance.**  
> **C'est la racine matérielle de l'écosystème FREK existant.**  
> 
> La puce capture quelque chose dans le monde physique :  
> **son → empreinte → identité matérielle → credential → preuve → FREKCORE**  
> 
> La musique est le premier cas d'usage.  
> L'architecture est universelle.  
> 
> **FREKCORE = infrastructure universelle.**  
> **FREK-ID = identité universelle.**  
> **FREK-Chain = preuve universelle.**  
> **FREK V3 = racine matérielle universelle.**  
> **FREK Verified = manifestation visible de la confiance.**  
> 
> **KORA = consommatrice d'API, comme les autres.**

---

*Document de réconciliation — v0.2.0-reconciled*  
*Baseline hardware V3 conservée. Couche crypto/proof réalignée sur écosystème FREK existant.*
