# FREK V3 — Architecture Review Final
## Synthèse post-session du 2026-08-10

**Auteur :** Direction produit / Architecture FREK  
**Statut :** Verrouillé — Prochaine phase : Engineering

---

## Correction fondamentale

> **La faisabilité technique n'est PAS encore prouvée.**  
> Elle est suffisamment définie pour être testée.

C'est une nuance critique pour tout investisseur ou ingénieur semiconductor. On a prouvé que le protocole est cohérent. On n'a pas prouvé qu'il tient dans du silicium.

---

## Les trois niveaux de maturité

| Niveau | Description | Statut |
|--------|-------------|--------|
| **1. Concept** | « Une puce pourrait certifier un signal » | ❌ Dépassé |
| **2. Architecture** | Hardware + crypto + DSP + Core fonctionnent ensemble | ✅ On est ici |
| **3. Engineering** | Bits exacts, timings, RTL, consommation, résultats expérimentaux | ⏳ Prochaine phase |

Le FPGA est le pont entre les niveaux 2 et 3.

---

## Ordre figé des prochaines étapes

```
FAP v0.1
    ↓
Crypto Review v0.1
    ↓
CE_QUI_MANQUE.md
    ↓
┌─────────────────────────┐
│ 🔴 GOLDEN VECTORS       │  ← Priorité absolue
│ + Rust Verifier         │
└─────────────────────────┘
    ↓
BIT-EXACT SPEC (Python = Rust)
    ↓
┌─────────────────────────┐
│ 🟡 DSP SPEC v0.1        │  ← Décision produit critique
│ Fingerprint             │
└─────────────────────────┘
    ↓
FPGA Prototype
    ↓
Benchmarks (power / latency / surface)
    ↓
ASIC Specification
    ↓
Fab / Design House
```

---

## 🔴 Priorité 1 : Golden Vectors

Jeu de données totalement déterministe :

```
TEST DEVICE
│
├── DEVICE_ID          (fixe)
├── P-256 private key  (fixe, TEST ONLY)
├── P-256 public key   (fixe)
├── PUF test seed      (fixe)
├── firmware hash      (fixe)
├── counter            (fixe)
├── nonce              (fixe)
├── device time        (fixe)
├── audio hash         (fixe)
├── fingerprint hash   (fixe)
├── context hash       (fixe)
└── expected signature (fixe)
```

**Règle :** Les clés de test ne doivent JAMAIS être des clés de production.

**Objectif :** Python → résultat X, Rust → résultat X, FPGA → résultat X.  
Si les trois convergent, on a une référence interopérable.

---

## 🔴 Priorité 2 : Rust Verifier

**Ce n'est PAS une traduction ligne par ligne du Python.**

C'est une implémentation indépendante qui interprète la même spécification.  
Si Python et Rust divergent, on découvre une ambiguïté dans le protocole.

**Le but n'est pas d'avoir deux logiciels.**  
**Le but est d'avoir deux interprétations indépendantes qui convergent.**

---

## 🟡 Priorité 3 : DSP & Fingerprint Specification v0.1

**Le vrai choix n'est pas « combien de MFCC ? »**

Le vrai choix est : **quelle propriété FREK veut-elle mesurer ?**

### Quatre objectifs possibles

| Objectif | Question | Usage |
|----------|----------|-------|
| **A. Identification** | « Est-ce exactement le même enregistrement ? » | Détection de copie, matching exact |
| **B. Similarité** | « Est-ce une œuvre acoustiquement proche ? » | Recommandation, clustering |
| **C. Provenance** | « Prouve-t-on que le signal vient de la même capture ? » | Certification légale |
| **D. Résistance** | « Survit-il à MP3, égalisation, compression, bruit, reverb ? » | Robustesse réelle |

**Ces objectifs ne produisent pas le même fingerprint.**

### Ce que doit contenir la spec DSP

- Fréquence d'échantillonnage
- Profondeur (bits)
- Mono / stéréo
- Taille de fenêtre
- Fonction de fenêtrage
- Taille FFT
- Hop size
- Bandes fréquentielles
- MFCC ou alternative
- Quantification
- Normalisation
- Taille finale du fingerprint
- Tolérance au bruit
- Tolérance aux codecs
- Tolérance au gain
- Tolérance au pitch/time stretch
- Collision target
- False-positive rate
- False-negative rate
- Coût CPU/DSP
- SRAM nécessaire

---

## 🟡 Certification — Ne pas choisir trop tôt

**Erreur à éviter :** Sur-certifier le silicium dès le départ.

**Approche correcte :** Définir le produit et le marché d'abord.

### Profils possibles

```
FREK V3
│
├── Consumer / IoT
│     └── Certification légère (PSA Certified L2)
│
├── Professional Audio
│     └── Certification renforcée (FIPS 140-3 L2)
│
├── Government / Institutional
│     └── Exigences élevées (Common Criteria EAL4+)
│
└── Financial / High Assurance
      └── Exigences spécifiques (FIPS 140-3 L3+)
```

Le niveau de certification détermine les contre-mesures matérielles et le NRE.  
Choisir avant de connaître le marché = risque de surcoût inutile.

---

## Ce qu'on ne fait PAS maintenant

| ❌ Ne pas faire | Pourquoi |
|-----------------|----------|
| Contacter un fondeur | L'architecture n'est pas encore mesurée |
| Chiffrer un NRE | Pas de données FPGA = pas de chiffrage fiable |
| Choisir une certification finale | Le marché cible n'est pas défini |
| Figer l'algorithme de fingerprint | Le DSP spec n'est pas écrit |
| Promettre un tape-out | On n'a pas encore de RTL |

---

## Ce qu'on fait maintenant

1. ✅ **FAP v0.1** — Verrouillé
2. ✅ **Crypto Review v0.1** — Verrouillé
3. ✅ **CE_QUI_MANQUE.md** — Documenté
4. ⏳ **Golden Vectors + Rust Verifier** — Prochain livrable
5. ⏳ **DSP Spec v0.1** — Décision produit
6. ⏳ **FPGA Prototype** — Pont vers l'engineering
7. ⏳ **Benchmarks** — Mesures réelles
8. ⏳ **ASIC Spec** — Après preuve FPGA
9. ⏳ **Fab / Design House** — Dernière étape

---

## Message clé

> **FREK V3 n'est plus au stade « est-ce qu'on peut imaginer cette puce ? »**  
> **Il est au stade « prouvons expérimentalement que cette architecture mérite d'être transformée en silicium ».**

---

*Document verrouillé. Toute modification nécessite une revue formelle.*
