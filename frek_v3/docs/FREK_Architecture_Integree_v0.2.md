# FREK — Architecture Intégrée v0.2
## Du FREK Object Model à l'écosystème complet

**Version :** 0.2.0-integrated  
**Date :** 2026-08-10  
**Statut :** ARCHITECTURE VALIDÉE — FOM + .fk + intégrations définies  
**Principe :** Une fois le FREK Object Model + .fk + FREK-ID + VC + FREK-Chain définis, on peut connecter KORA, Laurentia, Luciole, FREKANSLA ou n'importe quel futur produit sans casser le cœur du système.

---

## 1. Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FREK ÉCOSYSTÈME COMPLET                         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      FREKCORE (cœur)                             │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │   │
│  │  │   FREK-ID   │  │ FREK-CHAIN  │  │      FREK OBJECT        │ │   │
│  │  │  did:frek   │  │  OTS + BTC  │  │      MODEL (FOM)        │ │   │
│  │  │             │  │             │  │                         │ │   │
│  │  │ • Registry  │  │ • Blocks    │  │ • manifest              │ │   │
│  │  │ • Resolver  │  │ • OTS       │  │ • identity              │ │   │
│  │  │ • DID Doc   │  │ • Bitcoin   │  │ • content               │ │   │
│  │  │             │  │             │  │ • provenance            │ │   │
│  │  └─────────────┘  └─────────────┘  │ • rights                │ │   │
│  │                                     │ • credentials           │ │   │
│  │  ┌─────────────────────────────────┐│ • proofs                │ │   │
│  │  │         FORMAT .FK              ││                         │ │   │
│  │  │  (conteneur portable FOM)       │└─────────────────────────┘ │   │
│  │  │                                 │                            │   │
│  │  │  ZIP-like container             │                            │   │
│  │  │  JSON-LD manifest               │                            │   │
│  │  │  VC embedded                    │                            │   │
│  │  │  Content + variants             │                            │   │
│  │  └─────────────────────────────────┘                            │   │
│  │                                                                  │   │
│  │  API publique : REST / DIDComm / OID4VCI                        │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              ▲                                          │
│                              │                                          │
│  ┌───────────────────────────┼───────────────────────────────────────┐ │
│  │                           │           PRODUCTEURS / CRÉATEURS      │ │
│  │                           │                                        │ │
│  │  ┌─────────────┐  ┌──────┴──────┐  ┌─────────────┐  ┌──────────┐ │ │
│  │  │ FREKANSLA   │  │   LUCIOLE   │  │  FREKRAW    │  │  KORA    │ │ │
│  │  │ (plugin DAW)│  │  (hardware) │  │ (certification│  │ (CVLN)  │ │ │
│  │  │             │  │             │  │   service)   │  │         │ │ │
│  │  │ • Capture   │  │ • PUF       │  │ • Post-capture│  │ • API  │ │ │
│  │  │ • Identity  │  │ • Ed25519   │  │   verification│  │ • UX   │ │ │
│  │  │ • Metadata  │  │ • DSP       │  │ • Enrichment  │  │ • Apps │ │ │
│  │  │ • Rights    │  │ • VC signée │  │ • .fk generation│  │       │ │ │
│  │  │ • .fk gen   │  │             │  │               │  │       │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘ │ │
│  │                                                                    │ │
│  │  ┌─────────────────────────────────────────────────────────────┐  │ │
│  │  │  LAURENTIA (artiste / créateur)                            │  │ │
│  │  │  • DID:frek:<laurentia_id>                                  │  │ │
│  │  │  • Crée via FREKANSLA ou Luciole                            │  │ │
│  │  │  • Possède ses .fk                                          │  │ │
│  │  └─────────────────────────────────────────────────────────────┘  │ │
│  │                                                                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    CONSOMMATEURS / VÉRIFICATEURS                 │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐ │   │
│  │  │  EUDI       │  │ ID4Africa   │  │   CARICOM   │  │  mDL   │ │   │
│  │  │ (wallet)    │  │ (wallet)    │  │   (wallet)  │  │ (mobile│ │   │
│  │  │             │  │             │  │             │  │  DL)   │ │   │
│  │  │ • OID4VCI   │  │ • OID4VCI   │  │ • OID4VCI   │  │        │ │   │
│  │  │ • SD-JWT VC │  │ • SD-JWT VC │  │ • SD-JWT VC │  │        │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────┘ │   │
│  │                                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │  VÉRIFICATEURS OFFLINE (Python/JS)                       │   │   │
│  │  │  • Parse .fk                                             │   │   │
│  │  │  • Vérifie VC (Ed25519)                                  │   │   │
│  │  │  • Vérifie DID:frek                                      │   │   │
│  │  │  • Vérifie FREK-Chain                                    │   │   │
│  │  │  • Vérifie Bitcoin anchor                                │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  │                                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │  FREK VERIFIED (signal public)                           │   │   │
│  │  │  • Badge/marque de confiance                             │   │   │
│  │  │  • Visible sur les objets certifiés                      │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Les flux de données

### Flux 1 : Création musicale (FREKANSLA)

```
LAURENTIA (artiste)
    │
    ├── Ouvre DAW (Ableton)
    ├── Compose "Midnight Sessions"
    ├── Bounce master WAV
    │
    ▼
FREKANSLA (plugin DAW)
    │
    ├── Identifie Laurentia (DID:frek:laurentia-001)
    ├── Collecte métadonnées
    ├── Définit splits (Laurentia 50%, Label 30%, Producer 20%)
    ├── Ajoute artwork
    │
    ▼
Génération FK Object
    │
    ├── manifest.json (titre, description, type)
    ├── identity.json (DID Laurentia, DID Label, DID Producer)
    ├── content/ (master.wav, preview.mp3, artwork.jpg)
    ├── provenance.json (création, modifications)
    ├── rights.json (ownership, licenses, splits)
    │
    ▼
FREK VC (signée par Laurentia)
    │
    ├── type : FREKAuthorshipCredential
    ├── issuer : did:frek:laurentia-001
    ├── claims : "J'ai créé cette œuvre"
    ├── proof : Ed25519Signature2020
    │
    ▼
.fk (conteneur final)
    │
    ▼
FREKCORE
    │
    ├── Indexe l'objet
    ├── Crée FREK-Chain block
    ├── Génère OTS
    ├── Ancre Bitcoin
    └── Publie
        │
        ▼
    FREK VERIFIED (badge visible)
```

### Flux 2 : Capture live (Luciole/FREK V3)

```
PHYSIQUE
    │
    ├── DJ set en direct
    ├── Son capturé par micro
    │
    ▼
LUCIOLE / FREK V3 (hardware)
    │
    ├── Micro → Codec → I²S → DSP
    ├── FFT 2048 / Mel 40 / MFCC 13
    ├── Fingerprint audio (36 octets)
    ├── PUF → Ed25519 signing key
    ├── Timestamp RTC
    ├── Counter 18472
    │
    ▼
FREK Capture VC (signée matériellement)
    │
    ├── type : FREKCaptureCredential
    ├── issuer : did:frek:device-luciole-001
    ├── claims : captureTimestamp, audioFingerprint, firmwareVersion, counter
    ├── proof : Ed25519Signature2020 (signée par le hardware)
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
    ├── Indexe l'objet
    ├── Crée FREK-Chain block
    ├── Génère OTS
    ├── Ancre Bitcoin
    └── Publie
        │
        ▼
    FREK VERIFIED (badge visible)
```

### Flux 3 : Vérification

```
UTILISATEUR (reçoit un .fk)
    │
    ▼
Vérificateur offline (Python/JS)
    │
    ├── Parse le conteneur .fk
    ├── Vérifie manifest.json (structure)
    ├── Vérifie identity.json (DIDs valides)
    ├── Vérifie content_hash (SHA-256 du contenu)
    ├── Vérifie VC (signature Ed25519)
    │   ├── Résout DID:frek:<issuer>
    │   ├── Récupère clé publique
    │   ├── Vérifie signature
    │   └── Vérifie date d'émission
    ├── Vérifie provenance (historique cohérent)
    ├── Vérifie rights (licences valides)
    ├── Vérifie chain_references
    │   ├── FREK-Chain block exists
    │   ├── OTS valid
    │   └── Bitcoin confirmation
    │
    ▼
Résultat
    │
    ├── VALID → Affiche FREK VERIFIED badge
    │   └── Détails : artiste, date, device, preuves
    │
    └── INVALID → Affiche raison du rejet
        └── Ex : signature invalide, DID inconnu, chaine rompue
```

---

## 3. Les composants en détail

### 3.1 FREKCORE

**Rôle :** Infrastructure universelle de confiance.

**Modules :**
- **notary** : Service de notarisation
- **passport** : Gestion des identités
- **did** : Résolution DID:frek
- **eudi** : Compatibilité EUDI Wallet
- **standards** : Conformité ID4Africa, mDL, CARICOM
- **seal** : Scellement cryptographique
- **spec** : Spécifications publiques versionnées

**API :**
- REST API (CRUD objets, résolution DID, vérification)
- DIDComm (communication sécurisée entre DIDs)
- OID4VCI (émission de credentials)

### 3.2 FREK-ID

**Rôle :** Identité universelle pour tous les acteurs.

**Types d'identités :**
- **Personne** : `did:frek:person-<uuid>`
- **Organisation** : `did:frek:org-<uuid>`
- **Device** : `did:frek:device-<uuid>`
- **Application** : `did:frek:app-<uuid>`

**DID Document :**
```json
{
  "@context": "https://www.w3.org/ns/did/v1",
  "id": "did:frek:laurentia-001",
  "verificationMethod": [{
    "id": "did:frek:laurentia-001#key-1",
    "type": "Ed25519VerificationKey2020",
    "controller": "did:frek:laurentia-001",
    "publicKeyMultibase": "z6Mkq..."
  }],
  "assertionMethod": ["did:frek:laurentia-001#key-1"],
  "authentication": ["did:frek:laurentia-001#key-1"]
}
```

### 3.3 FREK-CHAIN

**Rôle :** Preuve chronologique et immuable.

**Architecture :**
- **FREK-Chain interne** : Blockchain légère, blocs rapides
- **OTS (One-Time Signature)** : Preuve temporelle
- **Bitcoin anchoring** : Ancrage sur la blockchain publique

**Blocs :**
```json
{
  "block_hash": "sha256:...",
  "previous_hash": "sha256:...",
  "timestamp": "2026-08-10T18:00:00Z",
  "transactions": [
    {
      "object_id": "urn:uuid:...",
      "operation": "CREATE",
      "vc_hash": "sha256:...",
      "ots_commitment": "..."
    }
  ],
  "merkle_root": "sha256:...",
  "bitcoin_anchor": "txid:..."
}
```

### 3.4 FREK Object Model

**Rôle :** Langage commun pour tous les objets.

**Déjà spécifié dans :** `FREK_Object_Model_Specification_v0.1.md`

### 3.5 Format .fk

**Rôle :** Conteneur portable d'objet FREK.

**Déjà spécifié dans :** `FREK_Object_Model_Specification_v0.1.md`

### 3.6 FREKANSLA

**Rôle :** Premier outil créateur de .fk.

**Intégration :**
- Plugin DAW (Ableton, Logic, FL Studio, etc.)
- Capture projet en temps réel
- Identification artiste via DID:frek
- Collecte métadonnées
- Définition splits et droits
- Génération .fk
- Publication vers FREKCORE

**Workflow :**
```
DAW → FREKANSLA → FK Object → .fk → FREKCORE
```

### 3.7 Luciole / FREK V3

**Rôle :** Racine matérielle de confiance.

**Intégration :**
- Capture physique (audio, vidéo, données)
- DSP embarqué (fingerprint)
- PUF (identité hardware)
- Ed25519 (signature matérielle)
- Production de FREK Capture VC

**Workflow :**
```
Physique → Luciole → FREK Capture VC → (FREKANSLA) → .fk → FREKCORE
```

### 3.8 FREKRAW

**Rôle :** Service de certification post-capture.

**Usage :**
- Enrichissement de VC existantes
- Ajout de métadonnées
- Certification tierce
- Génération de .fk à partir de captures brutes

### 3.9 KORA

**Rôle :** CVLN (Collective Virtual Living Network) — consommatrice d'API.

**Relation avec FREKCORE :**
- KORA consomme les API FREKCORE
- KORA n'est PAS dans FREKCORE
- KORA peut créer, lire, vérifier des objets FREK
- KORA a sa propre identité DID:frek

### 3.10 Laurentia

**Rôle :** Artiste / créateur.

**Identité :** DID:frek:<laurentia_id>

**Actions :**
- Crée via FREKANSLA
- Capture via Luciole
- Possède ses .fk
- Définit ses droits

### 3.11 FREK VERIFIED

**Rôle :** Signal public de confiance.

**Formes :**
- Badge numérique (sur les .fk)
- Marque visuelle (logo FREK Verified)
- API de vérification ("Est-ce que cet objet est FREK Verified ?")

---

## 4. Compatibilités et interopérabilités

### 4.1 Standards supportés

| Standard | Support | Usage |
|----------|---------|-------|
| **W3C DID** | ✅ | DID:frek |
| **W3C VC Data Model 2.0** | ✅ | FREK VC |
| **Ed25519Signature2020** | ✅ | Signatures |
| **SD-JWT VC** | ✅ | Selective disclosure |
| **OID4VCI** | ✅ | Émission de credentials |
| **EUDI Wallet** | ✅ | Compatibilité européenne |
| **mDL (ISO 18013-5)** | ✅ | Mobile Driving License |
| **ID4Africa** | ✅ | Compatibilité africaine |
| **CARICOM** | ✅ | Compatibilité caraïbe |

### 4.2 Wallets compatibles

- EUDI Wallet (UE)
- ID4Africa Wallet
- CARICOM Wallet
- Tout wallet OID4VCI compatible

---

## 5. Métriques actuelles (FREKCORE)

| Métrique | Valeur |
|----------|--------|
| Modules backend | 25 |
| Pages frontend | 22 |
| FREK-IDs actifs | 130 |
| Événements / tracks | 231 |
| Blocs FREK-Chain | 1 263 |
| Ancrages OTS | 1 409 |
| Confirmations Bitcoin | 1 291 |

---

## 6. Feuille de route

### Phase 1 : FOM + .fk (immédiat)
- [ ] Valider FREK Object Model v0.1
- [ ] Spécifier format .fk v0.1
- [ ] Définir schemas JSON-LD
- [ ] Implémenter parser .fk (Python/JS)

### Phase 2 : Intégration FREKANSLA (court terme)
- [ ] Spécifier plugin DAW
- [ ] Intégrer DID:frek
- [ ] Générer .fk depuis DAW
- [ ] Publier vers FREKCORE

### Phase 3 : Luciole / FREK V3 (moyen terme)
- [ ] Spécifier VC matérielle
- [ ] Adapter crypto (Ed25519)
- [ ] Générer Golden Vectors
- [ ] Implémenter Rust verifier
- [ ] Prototype FPGA

### Phase 4 : Écosystème (long terme)
- [ ] Intégrer EUDI Wallet
- [ ] Intégrer ID4Africa
- [ ] Intégrer CARICOM
- [ ] Déployer FREK Verified
- [ ] Nouveaux types d'objets (vidéo, document, physical)

---

## 7. Message final

> **FREKCORE = infrastructure universelle.**  
> **FREK-ID = identité universelle.**  
> **FREK-Chain = preuve universelle.**  
> **FK = objet universel.**  
> **FREK Object Model = langage commun.**  
> **FREKANSLA = premier créateur.**  
> **Luciole = racine matérielle.**  
> **FREK Verified = signal public.**  
> 
> **KORA = consommatrice d'API, comme les autres.**  
> **Laurentia = artiste, propriétaire de ses créations.**  
> 
> **Tout objet FREK, quel que soit son type, parle le même langage.**  
> **Tout acteur FREK, quelle que soit sa nature, utilise la même infrastructure.**

---

*Document d'architecture intégrée — v0.2.0-integrated*  
*FOM + .fk + intégrations définies. V3 hardware réaligné. Écosystème complet.*
