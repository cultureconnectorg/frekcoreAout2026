# FK Specification v1.0

**Cultural Object Container — Format de référence pour les objets culturels numériques**

Document confidentiel — FREKCORE / FREKANSLA
Version : 1.0 (specification vision pour implementation)
Date : 08 juillet 2026
Statut : NDA — Charte publique disponible séparément

---

## 0. Positionnement

**Phrase de présentation investisseurs / partenaires** :

> "FREKCORE crée l'infrastructure de preuve culturelle. FK est le format qui permet aux créations numériques de transporter leur identité, leur histoire et leur preuve à travers le temps."

---

## 1. Le problème à résoudre

Aujourd'hui, un fichier numérique contient principalement **une donnée** :

- un audio contient du son ;
- une image contient une image ;
- une vidéo contient une vidéo.

Mais il ne contient **pas naturellement** :

- l'histoire de création ;
- la provenance ;
- les contributeurs ;
- les versions ;
- le contexte culturel ;
- la preuve d'existence.

**FK ajoute la couche de mémoire et d'identité autour du contenu.**

---

## 2. Définition de FK

**FK = Cultural Object Container**

Un fichier FK n'est **PAS** un codec audio.
Ce n'est **PAS** un concurrent de WAV, MP3, FLAC ou MP4.

C'est un **conteneur narratif et probatoire**.

**Principe** :

```
MEDIA = ce qui est créé
FK    = l'histoire vérifiable de ce qui est créé
```

## 2.1 Ce que FK n'est PAS

- ❌ Un nouveau codec audio
- ❌ Un nouveau lecteur média
- ❌ Un remplacement de WAV / MP4 / PDF / JPEG
- ❌ Une blockchain
- ❌ Un système de stockage massif
- ❌ Un DRM

## 2.2 Ce que FK EST

- ✅ Un conteneur narratif léger, structuré, ouvert
- ✅ Un passeport de création vérifiable sur le temps long
- ✅ Un standard interopérable (import ET export vers formats existants)
- ✅ Un format source (comme un `.md` ou un `.blend`) dont on exporte vers les formats de diffusion

---

## 3. Architecture FK v1

Un fichier `.fk` est un **conteneur léger**.

### 3.1 Structure interne

```
creation.fk
├── manifest.fk.json
│
├── metadata/
│   ├── identity.json
│   ├── creators.json
│   └── timeline.json
│
├── media/
│   └── (fichiers originaux — ou références)
│
├── intelligence/
│   ├── fingerprints.json
│   ├── analysis.json
│   └── signatures.json
│
├── rights/
│   └── ownership.json
│
└── proof/
    └── frekcore-attestation.json
```

### 3.2 Choix technique : conteneur ZIP-based

Un `.fk` est un **archive ZIP renommée** avec extension `.fk` et structure interne normalisée.

**Pourquoi ZIP-based** (précédents : EPUB, USDZ, OOXML, ODF) :

- ✅ Outils standards (`unzip`, `zip`, tous OS) peuvent l'ouvrir et l'inspecter
- ✅ Streaming / accès partiel sans tout charger
- ✅ Compression native pour les métadonnées textuelles
- ✅ Adoption facilitée (pas de parseur binaire à écrire)
- ✅ Signature détachée possible sans réécrire le fichier

### 3.3 Extension et MIME

- **Extension** : `.fk`
- **MIME type** : `application/vnd.frek.culture+zip`
- **Magic bytes** : ZIP standard (`50 4B 03 04`) — un `.fk` reste un ZIP valide

### 3.4 Encoding / Locale

- Fichiers JSON : **UTF-8**, sans BOM
- Dates : **ISO 8601 avec timezone** (`2026-07-08T15:30:00+02:00`)
- Coordonnées géographiques : **WGS84**, précision optionnelle en mètres

---

## 4. Le principe clé — "FK comme Markdown"

**FK doit fonctionner comme Markdown.**

> Petit fichier. Grande capacité de narration.

**Objectif** :

Quelques kilo-octets peuvent raconter :

- qui
- quoi
- quand
- pourquoi
- comment
- quelles versions
- quelle preuve

Le média peut rester **externe**.
Le FK transporte **le sens**.

### 4.1 Deux modes de conteneur

| Mode | Description | Poids typique | Usage |
|---|---|---|---|
| **FK léger** | Le `.fk` contient uniquement les métadonnées + hashes + preuve. Les médias sont référencés par URI ou hash. | ~1 à 50 Ko | Circulation rapide, partage, catalogage |
| **FK autonome** | Le `.fk` embarque physiquement tous les médias. | Peut atteindre plusieurs Go | Archivage long terme, dépôt patrimonial |

**La preuve reste indépendante du poids du conteneur.** C'est le hash qui est ancré, pas le binaire.

---

## 5. Les couches — détail

### 5.1 `manifest.fk.json` (racine)

Point d'entrée obligatoire. Déclare la version, les couches présentes, et l'attestation.

```json
{
  "fk_version": "1.0",
  "frek_id": "fk-a5f8b3c9d1e2-8f3c",
  "object_type": "musical_work",
  "created_at": "2026-07-08T15:30:00+00:00",
  "layers": {
    "identity": "metadata/identity.json",
    "creators": "metadata/creators.json",
    "timeline": "metadata/timeline.json",
    "media": "media/",
    "intelligence": "intelligence/",
    "rights": "rights/ownership.json",
    "proof": "proof/frekcore-attestation.json"
  },
  "attestation_ref": {
    "block_hash": "5a9587ad...",
    "signature_algo": "ed25519"
  }
}
```

### 5.2 `metadata/identity.json` — Identité de l'objet

```json
{
  "frek_id": "fk-a5f8b3c9d1e2-8f3c",
  "title": "Concert au Bataclan — 12 mars 2026",
  "object_type": "live_performance",
  "context": {
    "location": "Bataclan, Paris",
    "coordinates": { "lat": 48.863, "lon": 2.371 },
    "date": "2026-03-12T21:30:00+01:00",
    "institution": "Le Bataclan"
  },
  "external_refs": {
    "isni": null,
    "iswc": null,
    "doi": null,
    "wikidata": null
  }
}
```

### 5.3 `metadata/creators.json` — Créateurs et contributeurs

```json
{
  "primary_creator": {
    "name": "Artiste X",
    "role": "primary_creator",
    "isni": "0000-0001-2345-6789"
  },
  "contributors": [
    { "name": "Musicien A", "role": "guitarist" },
    { "name": "Ingénieur son B", "role": "sound_engineer" }
  ]
}
```

### 5.4 `metadata/timeline.json` — Versions et évolutions

```json
{
  "versions": [
    {
      "version": "1.0",
      "created_at": "2026-03-12T23:16:00+01:00",
      "note": "Captation initiale",
      "hash": "sha256:...",
      "frek_block": "5a9587ad..."
    },
    {
      "version": "1.1",
      "based_on": "1.0",
      "created_at": "2026-03-15T14:00:00+01:00",
      "note": "Restauration audio + master",
      "hash": "sha256:...",
      "frek_block": "9c3e1f42..."
    }
  ]
}
```

### 5.5 `media/` — Fichiers originaux ou référencés

Convention : sous-dossiers par type.

```
media/
├── audio/           # WAV, FLAC, MP3, stems, master
├── video/           # MP4, MOV
├── image/           # JPEG, PNG, planches PDF
└── docs/            # PDF, texte, partitions
```

Chaque média peut être :
- **Inclus** physiquement dans le ZIP.
- **Référencé** dans `manifest.fk.json` via URI + hash (le fichier vit ailleurs).

### 5.6 `intelligence/` — Couche apportée par FREKANSLA

C'est ici que **FREKANSLA** dépose sa valeur ajoutée créative.

```
intelligence/
├── fingerprints.json    # Audio fingerprint (chromaprint, etc.)
├── analysis.json        # BPM, structure musicale, tonalité, spectral
└── signatures.json      # Signatures créatives (patterns, style, corpus)
```

Exemple `analysis.json` :

```json
{
  "audio": {
    "bpm": 128.4,
    "key": "A minor",
    "duration_seconds": 236.7,
    "structure": [
      { "part": "intro", "start": 0, "end": 12.3 },
      { "part": "verse_1", "start": 12.3, "end": 45.1 }
    ]
  }
}
```

### 5.7 `rights/ownership.json` — Droits et cessions

```json
{
  "owner": {
    "name": "Artiste X",
    "isni": "0000-0001-2345-6789",
    "share_percent": 100
  },
  "co_owners": [],
  "licenses": [],
  "transfers": []
}
```

### 5.8 `proof/frekcore-attestation.json` — Attestation FREKCORE

Le cœur souverain du format. Signée Ed25519. Vérifiable offline.

```json
{
  "frek_id": "fk-a5f8b3c9d1e2-8f3c",
  "issued_at": "2026-03-12T23:16:00+01:00",
  "issuer": "frekcore-notary-v1",
  "signature_algo": "ed25519",
  "public_key_ref": "https://frekcore.io/.well-known/notary-pubkey.json",
  "signature": "base64:...",
  "layer_hashes": {
    "manifest": "sha256:...",
    "identity": "sha256:...",
    "creators": "sha256:...",
    "timeline": "sha256:...",
    "media_manifest": "sha256:...",
    "intelligence": "sha256:...",
    "rights": "sha256:..."
  },
  "root_hash": "sha256:...",
  "block": {
    "block_hash": "5a9587ad...",
    "height": 1324
  },
  "btc_anchor": {
    "enabled": false,
    "ots_file": null,
    "confirmed_at": null
  }
}
```

---

## 6. Relation avec FREKANSLA

**FREKANSLA est le laboratoire de création.**

Il produit :

```
DAW / outil créatif
       ↓
   FREKANSLA
       ↓
       FK
```

**FREKANSLA apporte** (dans la couche `intelligence/` du `.fk`) :

- fingerprint audio ;
- analyse spectrale ;
- BPM ;
- structure musicale ;
- versions ;
- métadonnées créatives.

FREKANSLA est un **producteur de FK**. Il ne fait pas la preuve — il fait le sens.

---

## 7. Relation avec FREKCORE

**FREKCORE est la couche de confiance.**

Il apporte :

- identité FREK-ID ;
- attestation Ed25519 ;
- historique vérifiable ;
- preuve durable (FREK-Chain + ancrage Bitcoin optionnel).

**Architecture générale** :

```
Création (artiste, institution, événement)
       ↓
FREKANSLA (intelligence, structure, versions)
       ↓
FK Cultural Object (.fk)
       ↓
FREKCORE Attestation (Ed25519 + block)
       ↓
Ancrage public (FREK-Chain + Bitcoin OTS optionnel)
       ↓
Distribution / Archivage / Vérification
```

---

## 8. Principe de sécurité — Ne jamais bloquer les autres formats

**FK est bidirectionnel.**

### 8.1 Import (autres formats → FK)

```
WAV, AIFF, MP3, FLAC
MP4, MOV
JPEG, PNG, PDF
DATA (JSON, CSV)
              ↓
             FK
              ↓
        FREKCORE
```

Tout format média existant peut être **importé** dans un `.fk`. L'import ajoute le sens autour du média.

### 8.2 Export (FK → autres formats)

```
FK
 ↓
WAV / MP3 / STEMS
VIDEO
ARCHIVE ZIP
JSON-LD (métadonnées structurées)
```

**L'export d'un `.fk` vers un WAV perd de l'information** : identité, versions, preuve disparaissent. C'est là que se trouve la puissance du format — il ne se laisse pas reconstituer à partir de ses exports.

**FK est le format maître de contexte.**

---

## 9. Cas d'usage prioritaires

### 9.1 Musique

Un artiste ne livre plus uniquement :

```
song.wav
```

Il livre :

```
song.fk
```

qui contient :

- œuvre (WAV/FLAC embarqué ou référencé)
- auteurs (créateur + contributeurs)
- versions (v1 démo → v2 mix → v3 master)
- historique (dates, sessions)
- preuve (attestation FREKCORE)

### 9.2 Label

Un catalogue devient :

```
album.fk
```

avec :

- masters de chaque piste
- crédits complets
- droits et pourcentages
- évolutions (repress, remaster, réédition)

### 9.3 Festival

Un événement devient :

```
event.fk
```

avec :

- performances (captations audio/vidéo)
- artistes présents
- médias (photos, affiches, programmes)
- témoignages (interviews, retours)

### 9.4 Patrimoine

Une œuvre patrimoniale numérisée devient :

```
heritage.fk
```

avec :

- origine (provenance, date, contexte historique)
- histoire (restaurations, expositions, cessions)
- transmission (institutions successives, ayants droit)

---

## 10. Objectif produit

**Ne pas créer un logiciel fermé.**

**Créer un standard.**

**La vision** :

> "Dans le futur, une création culturelle numérique importante doit pouvoir exister avec son passeport FK."

---

## 11. Ce qu'il ne faut PAS construire maintenant

**NE PAS construire** :

- ❌ codec audio
- ❌ nouveau lecteur média
- ❌ blockchain complète
- ❌ stockage massif

## 12. Ce qu'il faut construire (roadmap technique)

**Construire, dans cet ordre**, sur signal réel :

| Ordre | Composant | Description |
|---|---|---|
| 1 | **Modèle FK JSON** | Schémas JSON validables (JSON Schema draft 2020-12) pour manifest + chaque couche |
| 2 | **Générateur FK** | Fonction Python/JS qui produit un `.fk` valide à partir d'un dossier de médias + métadonnées |
| 3 | **Validateur FK** | Vérifie qu'un `.fk` respecte le schéma + signatures + hashes |
| 4 | **Import média existant** | Wrappers WAV/MP4/PDF/IMAGE → FK (avec extraction de métadonnées natives) |
| 5 | **Génération fingerprint** | Pipeline audio → chromaprint / analyse spectrale / BPM (partagé avec FREKANSLA) |
| 6 | **Connexion API FREKCORE** | Signature Ed25519 + création de block + ancrage optionnel |
| 7 | **Export `.fk`** | Packaging final du ZIP avec les 7 couches |

**Rien ne démarre sans signal réel.**

---

## 13. Vérification d'un `.fk`

### 13.1 Vérification offline (sans serveur)

1. Ouvrir le ZIP `.fk`.
2. Lire `manifest.fk.json`.
3. Recalculer les hash SHA-256 de chaque couche → comparer avec `proof/frekcore-attestation.json > layer_hashes`.
4. Vérifier la signature Ed25519 avec la clé publique FREKCORE (embarquée ou récupérée via `.well-known`).
5. Si `btc_anchor.enabled` : vérifier `proof/ots/proof.ots` contre la Bitcoin blockchain.

### 13.2 Vérification en ligne (via FREKCORE)

```
GET /api/v1/fk/verify/{frek_id}
GET /api/v1/fk/detail/{frek_id}
```

Endpoint public, retourne l'attestation et l'état de l'ancrage.

---

## 14. Politique de diffusion (aligné IP Protection Strategy)

| Niveau | Contenu | Audience |
|---|---|---|
| **Public** | Sections 0-2, 9, 10 (vision, définition, cas d'usage, objectif) — via `/spec/fk` sur le site + charte téléchargeable | Tous |
| **Sous NDA — Partenaire** | Sections 3-8, 11-13 (structure, schémas, roadmap, vérification) | Labels, musées, institutions signataires, DAW partenaires |
| **Vault interne** | Clés de signature, seeds, procédures de rotation, code d'implémentation | Équipe FREKCORE core |

---

## 15. Prochaines étapes (gouvernées par signal réel)

Aucune ligne de code n'est écrite avant qu'un signal réel ne l'exige. La spec est publiée en interne.

| Signal réel attendu | Déclenchera |
|---|---|
| Un artiste demande d'exporter son œuvre en `.fk` | Générateur `.fk` v0.1 + CLI Python |
| Une institution demande de vérifier un `.fk` | Endpoint `/api/v1/fk/verify` + page publique |
| Un DAW / outil créatif accepte d'intégrer FK | SDK Python / JavaScript minimal |
| Un musée demande d'archiver un `.fk` | Procédure d'archivage long terme + audit |
| Un label demande un `album.fk` complet | Schéma étendu multi-pistes + interface batch |

---

## Annexe A — Glossaire

| Terme | Définition |
|---|---|
| **FK** | Cultural Object Container — le format lui-même |
| **`.fk`** | Extension d'un fichier FK (ZIP renommé, MIME `application/vnd.frek.culture+zip`) |
| **FREK-ID** | Identifiant unique cryptographique d'un objet FK. Format `fk-{12hex}-{4hex}` |
| **FREKCORE** | Infrastructure de preuve (signature, blocks, ancrage) |
| **FREKANSLA** | Laboratoire de création (intelligence, structure, versions) |
| **FREK-Chain** | Chaîne de blocks souveraine notariée par FREKCORE |
| **Attestation** | Signature Ed25519 des hashes de couches, prouvant intégrité et paternité |
| **Anchor** | Ancrage Bitcoin via OpenTimestamps, prouvant l'antériorité temporelle |
| **Couche** | Section fonctionnelle du `.fk` (Identité, Créateurs, Timeline, Média, Intelligence, Droits, Preuve) |
| **FK léger** | `.fk` contenant uniquement métadonnées + hashes (médias référencés) |
| **FK autonome** | `.fk` embarquant physiquement tous les médias |

---

## Annexe B — Phrase de rendez-vous type

> "FREKCORE crée l'infrastructure de preuve culturelle. FK est le format qui permet aux créations numériques de transporter leur identité, leur histoire et leur preuve à travers le temps.
>
> Un fichier audio contient un son. Un fichier vidéo contient une image en mouvement. Un fichier FK contient l'histoire vérifiable d'une création — qui, quoi, quand, pourquoi, comment, quelles versions, quelle preuve.
>
> Nous ne remplaçons pas les formats existants — nous les enveloppons pour leur ajouter le sens qui leur manquait. Un artiste, un label, un musée, une institution peuvent produire, échanger, archiver et vérifier un `.fk` sans changer leurs outils actuels."

---

**Fin du document FK Specification v1.0**

*Document vivant. Toute évolution doit être signée par FREKCORE et versionnée dans une chaîne d'historique du document lui-même.*

*Priorité actuelle : cette spec est le référentiel. Aucun développement ne démarre sans signal réel documenté.*
