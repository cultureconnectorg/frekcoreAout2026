# FREK DSP & Fingerprint Specification v0.1
## Objectifs, Paramètres et Contraintes du Pipeline Audio

**Version :** 0.1.0-draft  
**Date :** 2026-08-10  
**Statut :** DRAFT — Décision produit requise avant verrouillage  
**Dépend de :** FAP v0.1, Crypto Review v0.1, Engineering Exploded View v0.2

---

## Principe fondateur

> **Le vrai choix n'est pas « combien de MFCC ? »**  
> **Le vrai choix est : quelle propriété FREK veut-elle mesurer ?**

Cette spécification part des **objectifs stratégiques** pour dériver les **paramètres techniques**.  
Aucun paramètre n'est figé avant que l'objectif ne le soit.

---

## 1. Quatre objectifs stratégiques

### A. Identification
**Question :** « Est-ce exactement le même enregistrement ? »

**Usage :** Détection de copie, matching exact, traçabilité d'un fichier.

**Caractéristiques :**
- Très sensible aux différences (même un bit changé = fingerprint différent)
- Ne tolère AUCUNE transformation (re-encodage, égalisation, etc.)
- Utilisé pour : preuve légale de copie exacte, watermarking alternatif

**Exemple :** Un label veut prouver qu'un morceau leaké est identique au master.

---

### B. Similarité
**Question :** « Est-ce une œuvre acoustiquement proche ? »

**Usage :** Recommandation, clustering, recherche dans un catalogue.

**Caractéristiques :**
- Tolère les variations de qualité, de mix, de mastering
- Ne tolère PAS les transformations structurelles (remix, sample, mashup)
- Utilisé pour : « trouver des morceaux similaires », organiser un catalogue

**Exemple :** Un utilisateur veut trouver des morceaux "dans le style de X".

---

### C. Provenance
**Question :** « Puis-je démontrer qu'un signal provient de la même capture ? »

**Usage :** Certification légale, preuve de capture, anti-deepfake audio.

**Caractéristiques :**
- Tolère le re-encodage, la compression, l'égalisation
- Ne tolère PAS le re-enregistrement (nouvelle capture)
- Utilisé pour : « ce son vient bien de ce micro à cet instant »

**Exemple :** Un journaliste veut prouver qu'un enregistrement n'a pas été fabriqué.

---

### D. Résistance aux transformations
**Question :** « Survit-il à MP3, AAC, égalisation, compression, bruit, reverb ? »

**Usage :** Robustesse réelle dans un écosystème de streaming et de partage.

**Caractéristiques :**
- Tolère TOUTES les transformations courantes
- Risque de faux positifs plus élevé
- Utilisé pour : matching dans un monde de fichiers compressés et transformés

**Exemple :** Un morceau est uploadé sur YouTube (AAC 128 kbps), Spotify (Ogg Vorbis), et téléchargé en MP3 320. Le fingerprint doit matcher les trois.

---

## 2. Décision produit requise

**FREK V3 doit choisir UN objectif principal.**

| Objectif | Tolérance | Faux positifs | Faux négatifs | Complexité DSP |
|----------|-----------|---------------|---------------|----------------|
| A. Identification | Aucune | Très bas | Très bas | Faible |
| B. Similarité | Moyenne | Bas | Moyen | Moyenne |
| C. Provenance | Élevée | Bas | Bas | Élevée |
| D. Résistance | Très élevée | Moyen | Bas | Très élevée |

**Recommandation architecturale :**

> **Objectif C (Provenance) comme objectif principal de FREK V3.**

**Justification :**
- C'est l'objectif le plus aligné avec la promesse de FREK : *"cet appareil a capturé ce son"*
- Il tolère les transformations courantes (compression, égalisation) sans tolérer la falsification
- Il est compatible avec une preuve cryptographique (la preuve atteste la capture, pas l'identité exacte du fichier)
- Il est réalisable en DSP programmable sans nécessiter de modèle neural complexe

**Objectifs secondaires possibles :**
- A (Identification) peut être un mode optionnel (fingerprint "strict")
- D (Résistance) peut être une évolution V4 avec modèle neural edge

---

## 3. Paramètres techniques dérivés (Objectif C — Provenance)

### 3.1 Entrée audio

| Paramètre | Valeur proposée | Justification |
|-----------|-----------------|---------------|
| **Fréquence d'échantillonnage** | 48 kHz | Standard broadcast/pro audio. Compatible 44,1 kHz (oversampling possible) |
| **Profondeur** | 24 bits | Dynamic range suffisante pour le traitement. 16 bits acceptable en fallback |
| **Canaux** | Mono | Stéréo = 2× le traitement. Le fingerprint mono est suffisant pour la provenance |
| **Format d'entrée** | I²S ou PDM | Architecture A (codec externe) |

### 3.2 Prétraitement

| Paramètre | Valeur proposée | Justification |
|-----------|-----------------|---------------|
| **Pré-accentuation** | Non | Pas nécessaire pour la provenance (contrairement à la reconnaissance vocale) |
| **Filtre passe-bande** | 20 Hz — 20 kHz | Élimine les infrasons et ultrasons non audibles |
| **Normalisation du gain** | RMS-based | Compense les variations de volume sans déformer le signal |

### 3.3 Fenêtrage et FFT

| Paramètre | Valeur proposée | Justification |
|-----------|-----------------|---------------|
| **Taille de fenêtre** | 2048 samples | À 48 kHz = 42,7 ms. Bon compromis résolution temps/fréquence |
| **Fonction de fenêtrage** | Hann | Bonne réduction des lobes latéraux, pas de distorsion de phase |
| **Hop size** | 1024 samples (50% overlap) | Redondance suffisante pour la stabilité temporelle |
| **Taille FFT** | 2048 points | Même que la fenêtre (pas de zero-padding nécessaire) |
| **Fréquence de sortie** | ~46,9 Hz (48 kHz / 1024) | Une frame toutes les 21,3 ms |

### 3.4 Bandes fréquentielles

| Paramètre | Valeur proposée | Justification |
|-----------|-----------------|---------------|
| **Échelle** | Mel-scale | Mimétique de la perception humaine. Plus robuste que linéaire |
| **Nombre de bandes** | 40 | Suffisant pour capturer la signature spectrale sans sur-apprendre |
| **Plage Mel** | 0 — 8000 Mel | Couvre 20 Hz — 20 kHz en échelle perceptuelle |
| **Largeur des bandes** | Triangulaire, overlap 50% | Lissage naturel, robustesse au bruit |

### 3.5 MFCC

| Paramètre | Valeur proposée | Justification |
|-----------|-----------------|---------------|
| **Nombre de coefficients** | 13 | Standard. Les 13 premiers capturent l'enveloppe spectrale |
| **Énergie (c0)** | Incluse | Nécessaire pour la normalisation du niveau |
| **Delta / Delta-delta** | Non (V3) | Augmente la dimensionalité. Peut être ajouté en V4 |
| **Liftrage** | Non | Pas nécessaire pour la provenance (contrairement à l'ASR) |

### 3.6 Features additionnelles

| Feature | Usage | Calcul |
|---------|-------|--------|
| **RMS** | Niveau global | sqrt(mean(x²)) par frame |
| **ZCR** | Caractère tonal / bruité | Zero-crossing rate |
| **Spectral Centroid** | "Brillance" du son | mean(freq × magnitude) |
| **Spectral Flux** | Variation temporelle | norm(diff(magnitude)) |
| **Spectral Rolloff** | Bande passante effective | Fréquence où 85% de l'énergie est contenue |

**Vecteur de features par frame :**
```
[MFCC_0, MFCC_1, ..., MFCC_12, RMS, ZCR, Centroid, Flux, Rolloff]
= 13 + 5 = 18 dimensions par frame
```

### 3.7 Agrégation temporelle (fingerprint global)

| Paramètre | Valeur proposée | Justification |
|-----------|-----------------|---------------|
| **Durée d'analyse** | 3-5 secondes | Suffisant pour capturer la signature sans être trop long |
| **Agrégation** | Mean + Std par feature | Résumé statistique robuste |
| **Quantification** | 8 bits par coefficient | Réduction mémoire, tolérance au bruit |
| **Normalisation** | Z-score (mean=0, std=1) | Invariance au niveau global |

**Fingerprint final :**
```
18 features × 2 stats (mean, std) = 36 valeurs
36 valeurs × 8 bits = 288 bits = 36 octets
```

**Taille du FINGERPRINT_HASH :** SHA-256(36 octets) = 32 octets (déjà dans FAP v0.1)

### 3.8 Tolérances et robustesse

| Transformation | Tolérance attendue | Test requis |
|----------------|-------------------|-------------|
| **MP3 128 kbps** | ✅ Match | Test A/B sur corpus |
| **MP3 320 kbps** | ✅ Match | Test A/B sur corpus |
| **AAC 128 kbps** | ✅ Match | Test A/B sur corpus |
| **Ogg Vorbis** | ✅ Match | Test A/B sur corpus |
| **Égalisation ±6 dB** | ✅ Match | Test paramétrique |
| **Changement de gain ±12 dB** | ✅ Match | Normalisation RMS |
| **Bruit blanc (SNR > 20 dB)** | ✅ Match | Test sur corpus bruité |
| **Reverb légère** | ⚠️ Match partiel | Test sur corpus reverberé |
| **Pitch shift ±5%** | ❌ No match | Hors scope V3 |
| **Time stretch ±10%** | ❌ No match | Hors scope V3 |
| **Re-enregistrement** | ❌ No match | C'est le but (provenance) |

---

## 4. Contraintes DSP / Hardware

### 4.1 Coût de calcul

| Opération | Complexité | Cycles DSP estimés (48 kHz) |
|-----------|-----------|----------------------------|
| Fenêtrage (Hann, 2048) | O(N) | ~2K / frame |
| FFT 2048 (radix-2) | O(N log N) | ~20K / frame |
| Mel-filterbank (40 bandes) | O(N × M) | ~10K / frame |
| DCT (MFCC 13) | O(M²) | ~500 / frame |
| Features (RMS, ZCR, etc.) | O(N) | ~1K / frame |
| **Total par frame** | | **~33,5K cycles** |
| **Frames par seconde** | | **~47 frames/s** |
| **Total par seconde** | | **~1,6M cycles/s** |

**À 100 MHz DSP :** ~1,6% de charge CPU. Très faible.

### 4.2 Mémoire nécessaire

| Zone | Taille | Usage |
|------|--------|-------|
| **Buffer audio** | 2048 × 3 octets = 6 Ko | Triple buffering (capture, processing, output) |
| **FFT twiddle factors** | 2048 × 4 octets = 8 Ko | Précalculés (sin/cos) |
| **Mel-filterbank** | 40 × 128 × 4 octets = 20 Ko | Coefficients triangulaires |
| **DCT matrix** | 13 × 40 × 4 octets = 2 Ko | Précalculée |
| **Frame buffer** | 47 × 18 × 4 octets = 3,4 Ko | Features par frame (1 seconde) |
| **Fingerprint temporaire** | 36 octets | Résultat final |
| **TOTAL SRAM DSP** | | **~40 Ko** |

**SRAM totale du SoC :** 40 Ko (DSP) + 32 Ko (firmware) + 16 Ko (stack/heap) = **~90 Ko minimum**

### 4.3 Latence

| Étape | Latence |
|-------|---------|
| Capture 3 secondes | 3000 ms |
| Traitement (3s × 47 frames) | ~10 ms |
| Hash + signature | < 1 ms |
| **Total** | **~3011 ms** |

**Objectif < 200 ms de la spec conceptuelle :** Non atteint avec 3s d'analyse.  
**Solutions :**
- Mode "rapide" : 1 seconde d'analyse → ~1011 ms
- Mode "streaming" : preuve incrémentale (nouvelle preuve toutes les N frames)
- **Décision produit requise :** latence acceptable vs qualité du fingerprint

---

## 5. Métriques de qualité

### 5.1 Collision target

| Métrique | Valeur cible | Commentaire |
|----------|--------------|-------------|
| **Collision probability** | < 10⁻¹² | SHA-256 garantit ça nativement |
| **False Positive Rate (FPR)** | < 0,1% | Deux captures différentes matchées par erreur |
| **False Negative Rate (FNR)** | < 1% | Même capture non matchée après transformation |

### 5.2 Corpus de test

Pour valider ces métriques, il faut un corpus :

| Type | Taille | Usage |
|------|--------|-------|
| **Musique (stéréo, 48kHz/24bit)** | 1000 morceaux, 3-5 min | Base de référence |
| **Voix (mono, 48kHz/16bit)** | 500 enregistrements | Broadcast, interview |
| **Environnement** | 200 captures | IoT, monitoring |
| **Transformations** | 5× le corpus | MP3, AAC, gain, bruit, reverb |

---

## 6. Décisions à prendre avant verrouillage

| # | Décision | Options | Recommandation |
|---|----------|---------|----------------|
| 1 | **Objectif principal** | A/B/C/D | **C (Provenance)** |
| 2 | **Durée d'analyse** | 1s / 3s / 5s | **3s** (compromis qualité/latence) |
| 3 | **Nombre de MFCC** | 13 / 20 / 26 | **13** (standard, suffisant) |
| 4 | **Delta/delta-delta** | Oui / Non | **Non** (V3, ajoutable V4) |
| 5 | **Features additionnelles** | 0 / 3 / 5 | **5** (RMS, ZCR, Centroid, Flux, Rolloff) |
| 6 | **Quantification** | 8 bits / 16 bits / float | **8 bits** (robustesse + mémoire) |
| 7 | **Mode rapide** | Oui / Non | **Oui** (1s pour latence < 1s) |
| 8 | **Mode streaming** | Oui / Non | **À évaluer** (complexité protocolaire) |

---

## 7. Checklist avant FPGA

| Élément | Statut | Bloque le FPGA ? |
|---------|--------|------------------|
| Objectif principal choisi | ⏳ À décider | **OUI** |
| Durée d'analyse fixée | ⏳ À décider | **OUI** |
| Paramètres FFT/MFCC verrouillés | ⏳ À décider | **OUI** |
| Corpus de test défini | ⏳ À créer | Non (validation post-FPGA) |
| Métriques FPR/FNR validées | ⏳ À mesurer | Non (validation post-FPGA) |
| Latence mesurée | ⏳ À mesurer | Non (validation post-FPGA) |
| SRAM estimée | 🟡 90 Ko | Non (à vérifier sur FPGA) |

---

## 8. Synthèse

```
OBJECTIF C — PROVENANCE
│
├── Entrée : 48 kHz / 24-bit / Mono / I²S
│
├── Prétraitement : Filtre 20-20kHz, Normalisation RMS
│
├── Fenêtrage : Hann 2048, Hop 1024, FFT 2048
│
├── Spectre : Mel-scale 40 bandes
│
├── Features : 13 MFCC + RMS + ZCR + Centroid + Flux + Rolloff
│     = 18 dimensions / frame
│
├── Agrégation : 3 secondes, Mean + Std, Z-score
│     = 36 valeurs × 8 bits = 36 octets
│
├── Hash : SHA-256(36 octets) = FINGERPRINT_HASH
│
└── Contraintes : ~40 Ko SRAM, ~1,6M cycles/s, ~3s latence
```

---

*Document DRAFT — DSP Spec v0.1*  
*Aucun paramètre n'est verrouillé avant décision produit sur l'objectif principal.*
