# FREK Object Model (FOM) — Specification v0.1
## Langage commun de confiance pour tous les objets FREK

**Version :** 0.1.0-draft  
**Date :** 2026-08-10  
**Statut :** DRAFT — À valider avant implémentation .fk  
**Principe :** Tout ce qui produit, transporte, identifie ou certifie un objet FREK parle le même langage de confiance.

---

## 1. Définition

> **Un objet FREK est une entité numérique ou physique dont l'identité, la provenance, les droits et les preuves sont vérifiables cryptographiquement via l'infrastructure FREK.**

Le FREK Object Model (FOM) définit la structure commune à tous les objets FREK, indépendamment de leur type (audio, vidéo, document, asset physique).

---

## 2. Structure de l'objet FREK

```
FREK OBJECT
│
├── manifest
│   ├── object_id          (URN UUID v4)
│   ├── object_type        (audio | video | image | document | asset | physical)
│   ├── version            (semver : 1.0.0)
│   └── created_at         (ISO 8601)
│
├── identity
│   ├── creator            (DID:frek:<creator_id>)
│   ├── organization       (DID:frek:<org_id> | null)
│   ├── device             (DID:frek:<device_id> | null)
│   └── contributors       (DID:frek[])
│
├── content
│   ├── primary            (référence au contenu principal)
│   ├── variants           (références aux variants : master, preview, etc.)
│   └── metadata           (métadonnées spécifiques au type)
│
├── provenance
│   ├── creation           (timestamp, lieu, device)
│   ├── modifications      (historique des modifications)
│   ├── events             (événements liés : release, broadcast, etc.)
│   └── lineage            (objets parents, samples, remixes)
│
├── rights
│   ├── ownership          (DID:frek:<owner_id>)
│   ├── licenses           (liste des licences)
│   ├── splits             (répartition des droits)
│   └── contributors       (rôles et pourcentages)
│
├── credentials
│   └── FREK VC            (Verifiable Credential signée)
│       ├── type           (FREKCaptureCredential | FREKAuthorshipCredential | ...)
│       ├── issuer         (DID:frek:<issuer_id>)
│       ├── proof          (Ed25519Signature2020)
│       └── claims         (attestations spécifiques)
│
└── proofs
    ├── content_hash       (SHA-256 du contenu)
    ├── signatures         (signatures des parties prenantes)
    └── chain_references   (références FREK-Chain + OTS + Bitcoin)
```

---

## 3. Types d'objets FREK

```
FREK OBJECT
    │
    ├── FK AUDIO
    │   ├── Musique (track, album, mix)
    │   ├── Podcast
    │   ├── Broadcast
    │   └── Field recording
    │
    ├── FK VIDEO
    │   ├── Film
    │   ├── Clip
    │   ├── Live stream
    │   └── Documentaire
    │
    ├── FK IMAGE
    │   ├── Photographie
    │   ├── Art numérique
    │   ├── Illustration
    │   └── NFT
    │
    ├── FK DOCUMENT
    │   ├── Contrat
    │   ├── Certificat
    │   ├── Rapport
    │   └── Publication
    │
    ├── FK ASSET
    │   ├── Fichier 3D
    │   ├── Code source
    │   ├── Dataset
    │   └── Modèle ML
    │
    └── FK PHYSICAL
        ├── Objet d'art
        ├── Produit
        ├── Capteur IoT
        └── Document physique (scan)
```

---

## 4. Le format .fk

### Définition

> **.fk est le conteneur portable d'un objet FREK.**  
> C'est un fichier structuré qui encapsule l'ensemble du FREK Object Model.

### Structure du fichier .fk

```
SON.FK
│
├── manifest.json              (métadonnées de l'objet)
├── identity.json              (DIDs et identités)
├── content/                   (contenu et variants)
│   ├── master.wav
│   ├── preview.mp3
│   └── artwork.jpg
├── provenance.json            (historique et événements)
├── rights.json                (droits et licences)
├── credentials/
│   └── frek-vc.jsonld         (Verifiable Credential)
├── proofs/
│   ├── content-hash.sha256
│   ├── signatures.json
│   └── chain-references.json
└── index.json                 (index de validation rapide)
```

### Format technique

| Propriété | Spécification |
|-----------|---------------|
| **Format** | ZIP-like container (ou tar.gz) |
| **Manifest** | JSON-LD avec context FREK |
| **VC** | JSON-LD conforme W3C VC Data Model 2.0 |
| **Signatures** | Ed25519 (Eddsa-JCS-2022) |
| **Hash** | SHA-256 |
| **Compression** | Optionnelle (deflate) |
| **Encryption** | Optionnelle (AES-256-GCM ou ChaCha20-Poly1305) |

### Exemple minimal (FK Audio)

```json
// manifest.json
{
  "@context": ["https://frek.id/fom/v1"],
  "object_id": "urn:uuid:f3e2d1c0-b9a8-f7e6-d5c4-b3a291807060",
  "object_type": "fk:Audio",
  "version": "1.0.0",
  "created_at": "2026-08-10T18:00:00Z",
  "title": "Midnight Sessions",
  "description": "Live DJ set at Studio A"
}

// identity.json
{
  "creator": "did:frek:artist-laurentia-001",
  "organization": "did:frek:label-kora-001",
  "device": "did:frek:device-luciole-001",
  "contributors": [
    "did:frek:producer-john-001",
    "did:frek:engineer-jane-001"
  ]
}

// credentials/frek-vc.jsonld
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://frek.id/vc/v1"
  ],
  "id": "urn:uuid:...",
  "type": ["VerifiableCredential", "FREKCaptureCredential"],
  "issuer": "did:frek:device-luciole-001",
  "issuanceDate": "2026-08-10T18:00:00Z",
  "credentialSubject": {
    "id": "did:frek:device-luciole-001",
    "captureType": "audio",
    "audioFingerprint": {
      "algorithm": "frek-dsp-v1",
      "hash": "sha256:3a7f8b2c..."
    },
    "captureTimestamp": "2026-08-10T18:00:00.000Z",
    "firmwareVersion": "frek-v3-fw-v1.0.3",
    "hardwareCounter": 18472
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "proofValue": "z58D..."
  }
}
```

---

## 5. Le FREK Object Model ne réinvente rien

| Besoin | Solution existante | Usage dans FOM |
|--------|-------------------|----------------|
| **Identité** | DID:frek | Référencé dans `identity` |
| **Cryptographie** | Ed25519 | Signatures dans `credentials` et `proofs` |
| **Preuve** | FREK-Chain + OTS + Bitcoin | Référencé dans `proofs.chain_references` |
| **Credential** | W3C VC + SD-JWT VC | Format dans `credentials` |
| **Interopérabilité** | OID4VCI + EUDI + mDL | Transport et vérification |
| **Hash** | SHA-256 | Intégrité dans `proofs.content_hash` |

**Règle :** Le FOM ne définit pas de nouvelle cryptographie. Il référence et utilise les standards FREK existants.

---

## 6. Workflows

### Workflow 1 : Création via FREKANSLA

```
DAW (Ableton, Logic, etc.)
    │
    ▼
FREKANSLA (plugin DAW)
    │
    ├── Capture projet
    ├── Identification artiste (DID:frek)
    ├── Collecte métadonnées
    ├── Définition splits/droits
    │
    ▼
Génération FK Object
    │
    ├── manifest.json
    ├── identity.json
    ├── content/ (bounce master + preview)
    ├── provenance.json
    ├── rights.json
    │
    ▼
FREK VC (signée par l'artiste)
    │
    ▼
.fk (conteneur final)
    │
    ▼
FREKCORE
    │
    ├── Indexation
    ├── FREK-Chain anchoring
    ├── OTS + Bitcoin
    └── Publication
```

### Workflow 2 : Capture via Luciole/FREK V3

```
PHYSIQUE
    │
    ├── Son (air)
    ├── Lumière (optique)
    ├── Données (capteur)
    │
    ▼
Luciole / FREK V3 (hardware)
    │
    ├── Capture physique
    ├── DSP (fingerprint)
    ├── PUF → Ed25519 signature
    │
    ▼
FREK Capture VC (signée matériellement)
    │
    ▼
FREKANSLA (optionnel : enrichissement)
    │
    ├── Ajout métadonnées artiste
    ├── Ajout droits
    ├── Ajout artwork
    │
    ▼
.fk (conteneur enrichi)
    │
    ▼
FREKCORE
    │
    ├── Indexation
    ├── FREK-Chain anchoring
    ├── OTS + Bitcoin
    └── Publication
```

### Workflow 3 : Vérification

```
.fk (reçu)
    │
    ▼
Vérificateur offline (Python/JS)
    │
    ├── Parse .fk
    ├── Vérifie VC (signature Ed25519)
    ├── Vérifie DID:frek (résolution)
    ├── Vérifie content_hash (SHA-256)
    ├── Vérifie chain_references (FREK-Chain)
    ├── Vérifie OTS (one-time signature)
    └── Vérifie Bitcoin anchor (confirmation)
    │
    ▼
Résultat : VALID / INVALID avec détails
```

---

## 7. Architecture intégrée

```
                     FREKCORE
                         │
          ┌──────────────┼──────────────┐
          │              │              │
      FREK-ID       FREK-CHAIN        FK
      identité         preuve        objet
          │              │              │
          └──────────────┼──────────────┘
                         │
                 FREK OBJECT MODEL
                         │
          ┌──────────────┼──────────────┐
          │              │              │
      FREKANSLA       LUCIOLE        FREKRAW
       création       hardware      certification
          │              │              │
          └──────────────┼──────────────┘
                         │
                   FREK VERIFIED
```

### Rôles

| Composant | Rôle | Produit |
|-----------|------|---------|
| **FREKCORE** | Infrastructure universelle | Confiance, indexation, anchoring |
| **FREK-ID** | Identité universelle | DID:frek pour tous les acteurs |
| **FREK-CHAIN** | Preuve universelle | Blockchain interne + OTS + Bitcoin |
| **FK** | Objet universel | Conteneur portable d'objet FREK |
| **FREKANSLA** | Création | Premier outil créateur de .fk |
| **LUCIOLE** | Hardware | Racine matérielle de confiance |
| **FREKRAW** | Certification | Service de certification post-capture |
| **FREK VERIFIED** | Signal public | Badge/marque de confiance |

---

## 8. Extensibilité

### Nouveau type d'objet

Pour ajouter un nouveau type (ex: FK Physical — objet d'art) :

1. Définir `object_type` : `"fk:Physical"`
2. Définir `content` spécifique (photos, certificats d'authenticité)
3. Définir `metadata` spécifique (matériaux, dimensions, provenance physique)
4. Réutiliser `identity`, `provenance`, `rights`, `credentials`, `proofs`

### Nouveau credential type

Pour ajouter un nouveau type de credential (ex: FREKAuthorshipCredential) :

1. Définir le schema JSON-LD
2. Enregistrer dans FREKCORE
3. Les émetteurs (FREKANSLA, Luciole, etc.) peuvent l'utiliser

---

## 9. Checklist avant implémentation

| # | Élément | Statut |
|---|---------|--------|
| 1 | FREK Object Model validé | ⏳ Ce document |
| 2 | Format .fk spécifié | ⏳ Ce document |
| 3 | Schemas JSON-LD définis | ⏳ À créer |
| 4 | FREKANSLA intégration spécifiée | ⏳ À spécifier |
| 5 | Luciole intégration spécifiée | ⏳ À spécifier |
| 6 | Vérificateur .fk implémenté | ⏳ À implémenter |
| 7 | Tests interopérabilité | ⏳ À tester |

---

## 10. Message

> **Le FREK Object Model est le langage commun.**  
> **.fk est le conteneur portable.**  
> **FREKCORE est l'infrastructure de confiance.**  
> **FREKANSLA est le premier créateur.**  
> **Luciole est la racine matérielle.**  
> **FREK Verified est le signal public.**  
> 
> **Tout objet FREK, quel que soit son type, parle le même langage.**

---

*Document de spécification — FOM v0.1*  
*À valider avant implémentation du format .fk et intégration FREKANSLA.*
