# Ce qui manque — Honnêteté architecturale
## FREK V3 v0.1 — Points non résolus

**Date :** 2026-08-10  
**Statut :** Spécification verrouillée, mais incomplète sur les points suivants

---

## Ce qui EST fait (✅)

1. Architecture conceptuelle tricouche (V3 / Core / Brain)
2. Protocole d'attestation binaire (283 octets, L0/L1/L2)
3. Architecture cryptographique (PUF → HKDF → DRK → AK/FK/CK)
4. Threat model qualitatif
5. Implémentation Python de référence (16 tests passés)
6. Golden Test Vectors générés

---

## Ce qui manque encore (⬜)

### 1. Rust Cross-Implementation ⬜ CRITIQUE

**Problème :** Une seule implémentation (Python) existe. Le protocole n'est pas prouvé implémentation-agnostique.

**Pourquoi c'est important :** Deux implémentations indépendantes qui produisent les mêmes résultats prouvent que la spec est correcte, pas que le code Python est correct.

**Quand le faire :** Avant le FPGA. C'est le prochain livrable.

---

### 2. Golden Vectors déterministes ⬜ CRITIQUE

**Problème :** Les vecteurs de test changent à chaque exécution car les clés sont générées aléatoirement.

**Pourquoi c'est important :** Le FPGA doit pouvoir reproduire exactement les mêmes vecteurs. Il faut des clés de test fixes (hardcodées mais marquées "TEST ONLY").

**Quand le faire :** En même temps que le Rust verifier.

---

### 3. Spécification du DSP / Fingerprint ⬜ IMPORTANT

**Problème :** On sait que le DSP fait FFT/MFCC/RMS/ZCR, mais on ne sait pas :
- Combien de bandes MFCC ? (13 ? 26 ? 40 ?)
- Taille de la fenêtre FFT ? (2048 ? 4096 ?)
- Hop size ? (512 ? 1024 ?)
- Format de sortie du fingerprint ? (vecteur de floats ? de ints ? normalisé comment ?)
- Quel algorithme de fingerprint exact ? (Shazam-like ? Neural embedding ?)

**Pourquoi c'est important :** Sans ça, le FPGA ne sait pas quoi implémenter dans le bloc DSP. Et le `FINGERPRINT_HASH` dans la preuve dépend de ce format.

**Quand le faire :** Avant le prototype FPGA. C'est un choix produit, pas technique.

---

### 4. Spécification des interfaces matérielles ⬜ IMPORTANT

**Problème :** On a défini I²C/SPI/UART, mais pas :
- Pinout exact (quels pins, quelles fonctions)
- Timing I²C (400 kHz, mais quelle latence max ?)
- Protocole SPI (mode 0, mais CPOL/CPHA exacts ?)
- Séquence de power-up (ordre des rails d'alimentation)
- Signaux d'interruption (quand la preuve est prête ?)
- Consommation par mode (sleep, capture, processing, idle)

**Pourquoi c'est important :** Le fabricant de micros (le client de la puce) a besoin de ça pour intégrer FREK V3 dans son design.

**Quand le faire :** Pendant la phase FPGA (on mesure les timings réels).

---

### 5. Plan de certification ⬜ IMPORTANT

**Problème :** Aucun niveau de certification cible n'est défini.

**Questions ouvertes :**
- FIPS 140-3 niveau 2 ? 3 ? 4 ?
- Common Criteria EAL4+ ? EAL5+ ?
- PSA Certified Level 2 ? 3 ?
- SESIP ?

**Pourquoi c'est important :** Le niveau de certification détermine les contre-mesures matérielles (mesh anti-probing, shielding, détecteurs de glitch) et donc le coût du silicium.

**Quand le faire :** Avant le choix du fondeur. C'est une décision business.

---

### 6. Analyse de coût ⬜ IMPORTANT

**Problème :** Aucun chiffrage.

**Questions ouvertes :**
- Coût NRE (Non-Recurring Engineering) pour 22nm ? ($500K ? $2M ? $5M ?)
- Coût du mask set ?
- Coût unitaire en volume (100K ? 1M ? 10M unités) ?
- Coût de certification ?
- Coût de l'IP (RISC-V core, crypto accelerator, PUF) ?

**Pourquoi c'est important :** Sans ça, pas de business plan. Le modèle économique en 3 couches reste théorique.

**Quand le faire :** Après contact avec un fondeur ou design house.

---

### 7. Modèle de menaces quantifié ⬜ MOYEN

**Problème :** Le threat model est qualitatif ("l'attaquant peut faire X"), pas quantifié.

**Ce qui manque :**
- Budget d'attaque (combien coûte une attaque par DPA ?)
- Temps moyen avant compromission (MTBC)
- Scénarios de faille (qu'est-ce qui se passe si le PUF a un BER de 20% ?)
- Analyse de risque formelle (FAIR, OCTAVE, ou équivalent)

**Pourquoi c'est important :** Pour convaincre un client institutionnel (label, broadcasteur) que FREK est suffisamment sûr.

**Quand le faire :** Avant la première vente B2B.

---

### 8. Procédure d'enrollment et provisioning ⬜ MOYEN

**Problème :** L'enrollment est décrit conceptuellement, mais pas opérationnellement.

**Questions ouvertes :**
- Qui fait l'enrollment ? (FREK Authority ? Le fondeur ? L'OSAT ?)
- Où se fait l'enrollment ? (Usine ? Labo FREK ?)
- Comment transporte-t-on les Helper Data de l'usine au client ?
- Quel est le processus de factory reset ?
- Comment gère-t-on les dies rejetés (PUF weak) ?

**Pourquoi c'est important :** C'est la partie la plus sensible de la supply chain. Une fuite à l'enrollment compromet toute la chaîne.

**Quand le faire :** Avant le premier tape-out.

---

### 9. Protocole de mise à jour firmware (OTA) ⬜ MOYEN

**Problème :** Le secure boot est décrit, mais pas le protocole de mise à jour.

**Questions ouvertes :**
- Comment le host envoie-t-il le nouveau firmware ?
- Quel est le format du firmware signé ?
- Comment gère-t-on le rollback autorisé (recovery) ?
- Quelle est la taille max du firmware ?
- Comment vérifie-t-on l'intégrité pendant le transfert ?

**Pourquoi c'est important :** Un firmware non patchable est un firmware mort. Un firmware patchable sans sécurité est une porte ouverte.

**Quand le faire :** Avant le prototype FPGA.

---

### 10. Scénarios d'usage concrets ⬜ MOYEN

**Problème :** On a des exemples (studio, festival), mais pas de scénarios détaillés.

**Ce qui manque :**
- Cas d'usage 1 : Microphone de studio (connecté, challenge-response)
- Cas d'usage 2 : Microphone de terrain (offline, autonome, sync tardive)
- Cas d'usage 3 : Broadcast live (latence critique, preuve par batch)
- Cas d'usage 4 : IoT / Smart home (ultra low power, wake-on-sound)
- Cas d'usage 5 : Smartphone (intégration dans le SoC existant)

**Pourquoi c'est important :** Chaque scénario a des contraintes différentes (latence, puissance, connectivité) qui influencent le design hardware.

**Quand le faire :** Avant le choix du package et du pinout.

---

### 11. Benchmarks de performance ⬜ FAIBLE

**Problème :** Aucune mesure.

**Ce qui manque :**
- Latence capture → preuve (ms ?)
- Consommation pendant capture (mW ?)
- Consommation en sleep (µW ?)
- Débit max de preuves par seconde
- Taille mémoire SRAM nécessaire

**Pourquoi c'est important :** Pour dimensionner le SoC et convaincre les clients que ça tient dans leur BOM.

**Quand le faire :** Sur le FPGA prototype (mesures réelles).

---

### 12. Documentation visuelle ⬜ FAIBLE

**Problème :** Tout est texte. Pas de schéma.

**Ce qui manque :**
- Diagramme de flux de données (audio → preuve)
- Diagramme de séquence (challenge-response)
- Schéma du Trust Domain (PUF → KDF → Crypto)
- Floorplan conceptuel du SoC
- Timeline de développement (Gantt)

**Pourquoi c'est important :** Pour les présentations aux investisseurs et aux partenaires.

**Quand le faire :** Dès que possible (outils de diagramme existants).

---

## Synthèse : priorités

| Priorité | Élément | Bloqueur pour |
|----------|---------|---------------|
| 🔴 CRITIQUE | Rust verifier | FPGA, confiance dans la spec |
| 🔴 CRITIQUE | Golden Vectors fixes | Validation FPGA |
| 🟡 IMPORTANT | Spec DSP / Fingerprint | Prototype FPGA |
| 🟡 IMPORTANT | Spec interfaces matérielles | Intégration client |
| 🟡 IMPORTANT | Plan de certification | Choix fondeur, coût |
| 🟡 IMPORTANT | Analyse de coût | Business plan, fundraising |
| 🟢 MOYEN | Threat model quantifié | Vente B2B institutionnelle |
| 🟢 MOYEN | Enrollment / Provisioning | Supply chain sécurisée |
| 🟢 MOYEN | OTA firmware | Prototype FPGA |
| 🟢 MOYEN | Scénarios d'usage | Design hardware |
| ⚪ FAIBLE | Benchmarks | Mesures sur FPGA |
| ⚪ FAIBLE | Documentation visuelle | Présentations |

---

## Ce que ça change pour toi

**Tu n'as pas besoin de tout faire maintenant.** Ce qui est livré (FAP v0.1 + Crypto Review + Python verifier) suffit pour :
- ✅ Montrer à un investisseur que le projet est sérieux
- ✅ Recruter un ingénieur hardware (il aura une spec claire)
- ✅ Décider si tu continues (la faisabilité technique est prouvée)

**Ce qui bloque le FPGA :** Les points 🔴 CRITIQUE (Rust verifier + Golden Vectors fixes).

**Ce qui bloque l'ASIC :** Les points 🟡 IMPORTANT (DSP, interfaces, certification, coût).

---

*Document d'honnêteté. Ne pas montrer aux investisseurs sans contexte. Servir de feuille de route interne.*
