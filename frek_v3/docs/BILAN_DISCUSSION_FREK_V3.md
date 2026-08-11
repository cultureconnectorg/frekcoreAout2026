# Bilan — Discussion FREK V3 Architecture & Protocole
## Session du 2026-08-10

---

## 1. Contexte de départ

L'utilisateur disposait d'une architecture initiale pour FREK (Frequency Authority) mélangeant hardware, software et services. La discussion a porté sur la conceptualisation de **FREK V3** : une puce propriétaire (SoC) dédiée à la certification cryptographique de l'origine d'un signal audio.

**Pivot conceptuel clé :**  
FREK ne prétend pas établir la propriété intellectuelle. Il affirme : *"cet appareil identifié cryptographiquement a produit cette observation à cet instant, et cette preuve n'a pas été altérée depuis"*.

---

## 2. Architecture tricouche validée

```
┌─────────────────────────────────────────┐
│  FREK V3                                │
│  Perception + Identité matérielle       │
│  (SoC audio + DSP + Secure Element)     │
└─────────────────────────────────────────┘
              ↓  FREK-ID signé
┌─────────────────────────────────────────┐
│  FREK Core                              │
│  Mémoire + Réseau + Vector search       │
│  (Backend, base de données, graphe)     │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  CVL Brain                              │
│  Intelligence + Analyse culturelle      │
│  (IA, institutions, analytics)          │
└─────────────────────────────────────────┘
```

---

## 3. Livrables produits

### Document 1 — FREK Attestation Protocol v0.1
**Fichier :** `FREK_Attestation_Protocol_v0.1.md` (800 lignes)

**Contenu :**
- Format binaire de la preuve L2 (283 octets fixes)
- 3 niveaux d'attestation : L0 (software), L1 (device), L2 (hardware attested)
- Protocole de communication I²C/SPI/UART (commandes TLV)
- Gestion du temps (DEVICE_TIME vs VERIFIER_TIME vs EXTERNAL_TIMESTAMP)
- Compteur monotone uint64 + nonce challenge-response
- Vérification autonome (pas de cloud requis)
- 5 vecteurs de test

**Décisions verrouillées :**
- Preuve L2 vérifiable sans FREK Cloud
- Challenge-response mode privilégié, mode autonome en fallback
- Timestamp informatif, pas vérité absolue

---

### Document 2 — FREK Cryptographic Architecture Review v0.1
**Fichier :** `FREK_Cryptographic_Architecture_Review_v0.1.md` (806 lignes)

**Contenu :**
- PUF SRAM + Fuzzy Extractor (BCH, FER < 10⁻⁹)
- Device Root Key (DRK) immuable, dérivée du PUF uniquement
- Séparation des clés : DRK → AK / FK / CK via HKDF-SHA-256
- ECDSA P-256 raw (r‖s, 64 octets, pas DER)
- Génération du nonce k : TRNG hardware privilégié, RFC 6979 fallback
- Compteur monotone en NVM (MRAM préférée, redondance triple en fallback)
- Secure Boot (ROM → Bootloader → Firmware)
- Threat model complet (extraction, probing, fault injection, side-channel, replay, clonage)
- Key lifecycle (fabrication, enrollment, activation, révocation, destruction)

**Correction majeure au FAP v0.1 :**
> La clé de signature (AK) ne dépend PAS du compteur ni du firmware hash.  
> Le compteur et le firmware hash sont des **données signées**, pas des paramètres de KDF.  
> La DRK est immuable. L'AK est stable. Cela évite la fragilité de gestion de clés.

---

### Document 3 — FREK Reference Verifier (Python)
**Dossier :** `frek_reference_verifier/` (10 fichiers)

**Fichiers :**
| Fichier | Rôle |
|---------|------|
| `frek_constants.py` | Constantes du protocole (MAGIC=0x46, tailles, courbes) |
| `frek_types.py` | Dataclasses : FrekProof, DeviceState, VerificationResult |
| `frek_crypto.py` | SHA-256, HKDF, ECDSA P-256 raw, encodage canonique |
| `frek_parser.py` | Parser/serializer binaire strict (283 octets) |
| `frek_registry.py` | État par device : counter, clé publique, firmware whitelist |
| `frek_verifier.py` | Pipeline complet : parse → crypto → policy → ACCEPT/REJECT |
| `frek_device_sim.py` | Device FREK V3 simulé (génération de preuves valides) |
| `test_frek_verifier.py` | 16 tests + Golden Test Vectors export |
| `README.md` | Documentation d'utilisation |

**5 points verrouillés :**
1. **DEVICE_ID** = Truncate(SHA-256(AK_pub), 16)
2. **Signature** = r‖s, 64 octets raw (pas DER)
3. **MESSAGE** = SHA-256(DOMAIN ‖ VERSION ‖ LEVEL ‖ ... ‖ AK_PUB) avec encodage canonique strict
4. **Séparation crypto/policy** : signature d'abord, puis counter/nonce/firmware
5. **Isolation PUF** : le vérificateur ne voit jamais DRK/IKM/PUF

**16 tests passés :**
1. Proof valide → ACCEPT
2. Signature modifiée → INVALID_SIGNATURE
3. AUDIO_HASH modifié → INVALID_SIGNATURE
4. NONCE incorrect → NONCE_MISMATCH
5. Counter inférieur → REPLAY
6. Counter identique → REPLAY
7. DEVICE_ID inconnu → UNKNOWN_DEVICE
8. AK_pub remplacée → IDENTITY_MISMATCH
9. Firmware hash non autorisé → FIRMWARE_REJECTED
10. Mauvais MAGIC → MALFORMED
11. Mauvaise VERSION → UNSUPPORTED_VERSION
12. Champ tronqué → MALFORMED
13. Bit-flip sur 11 champs individuellement → rejet
14. Counter gap trop grand → COUNTER_GAP_TOO_LARGE
15. Device révoqué → DEVICE_REVOKED
16. Mode autonome (pas de nonce) → ACCEPT

---

### Document 4 — Instructions pour l'équipe
**Fichier :** `INSTRUCTIONS_EMERGENT.md`

Instructions transmissibles à l'équipe technique pour :
- Créer la structure de dossiers (`frek_v3/` à côté de `frekcore/`)
- Exécuter les tests de validation
- Comprendre ce qu'il ne faut pas faire (ne pas modifier, ne pas intégrer dans frekcore)
- Savoir ce qui est prévu ensuite (Rust verifier, FPGA, ASIC)

---

## 4. Décisions architecturales clés

| Décision | Justification |
|----------|---------------|
| **PUF intégré** (pas secure element externe) | Identité liée au silicium physique, pas de supply chain externe |
| **SRAM PUF** (pas RO PUF) | Réutilise la SRAM existante, pas de surface additionnelle en ULP |
| **ECDSA P-256** (pas BLS/Ed25519) | Maturité hardware, FIPS 186-4, accélérateurs disponibles |
| **22-40 nm** (pas 5 nm) | Coût, analogique, longévité, ULP. TSMC 22ULL cible idéale |
| **Ultra Low Power** | La puce doit "disparaître dans les objets", pas être un ordinateur |
| **Pas de radio intégrée** (V1) | I²C/SPI/GPIO suffisent. Wi-Fi/BLE/NFC en version future |
| **DSP programmable** (pas algorithme figé) | FFT+MFCC aujourd'hui, neural embeddings demain |
| **3 niveaux L0/L1/L2** | Permet adoption progressive sans hardware dès le départ |
| **Vérification autonome** | La preuve L2 ne nécessite pas le cloud FREK |

---

## 5. Modèle économique validé

```
Couche 1 — Silicon        → Vente de puces (marge faible, volume élevé)
Couche 2 — Certification  → Attestation par appareil/volume (revenus récurrents)
Couche 3 — Network        → Graph, analytics, institutions (haute marge)
```

La puce est le **cheval de Troie industriel** qui verrouille l'écosystème.

---

## 6. Feuille de route validée

```
┌─────────────────────────────────────────────────────────────┐
│  1. Crypto Review v0.1           ✅ FAIT                   │
│     → PUF, HKDF, ECDSA, threat model, key lifecycle         │
├─────────────────────────────────────────────────────────────┤
│  2. Reference Verifier (Python)  ✅ FAIT                   │
│     → 16 tests passés, Golden Vectors générés             │
├─────────────────────────────────────────────────────────────┤
│  3. Rust Cross-Implementation    ⬜ À FAIRE                │
│     → Mêmes entrées → mêmes sorties que Python            │
│     → Vérifier avec les Golden Vectors Python             │
├─────────────────────────────────────────────────────────────┤
│  4. Intégration frekcore         ⬜ À FAIRE                │
│     → Crate Rust importé par frekcore                     │
│     → frekcore peut valider les preuves FREK              │
├─────────────────────────────────────────────────────────────┤
│  5. FPGA Prototype               ⬜ À FAIRE                │
│     → Soft-core RISC-V + FFT IP + crypto soft/HSM         │
│     → Produire preuves que le Rust verifier accepte       │
├─────────────────────────────────────────────────────────────┤
│  6. ASIC Specification           ⬜ À FAIRE                │
│     → Mesures conso/latence/surface sur FPGA              │
│     → Chiffrage NRE, tape-out, production                 │
│     → Spécification RTL complète                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Ce que l'utilisateur doit faire maintenant

1. **Valider l'exécution** : Lancer `python test_frek_verifier.py` dans `frek_v3/reference_verifier/`
2. **Archiver les docs** : Placer les 2 documents Markdown dans `frek_v3/docs/`
3. **Transmettre à l'équipe** : Envoyer `INSTRUCTIONS_EMERGENT.md` à Emergent.sh
4. **Décider du recrutement** : Ingénieur hardware (FPGA → ASIC) ou design house
5. **Ne pas modifier les specs** : Le protocole est verrouillé jusqu'à revue formelle

---

## 8. Métaphores utilisées pendant la discussion

| Métaphore | Concept technique |
|-----------|-------------------|
| "Notaire hardware" | La puce signe une preuve, pas un simple témoin |
| "Cheval de Troie industriel" | La puce verrouille l'écosystème par le hardware |
| "Maquette numérique" | Le code Python simule la puce avant de la construire |
| "Oracle de référence" | Le vérificateur Python est la vérité pour le FPGA |
| "Disparaître dans les objets" | Ultra low power, pas un ordinateur minuscule |

---

## 9. Fichiers disponibles au téléchargement

| Fichier | Lien |
|---------|------|
| ZIP complet (docs + code) | `FREK_v0.1_Complete_Deliverables.zip` |
| Instructions équipe | `INSTRUCTIONS_EMERGENT.md` |
| FAP v0.1 | `FREK_Attestation_Protocol_v0.1.md` |
| Crypto Review v0.1 | `FREK_Cryptographic_Architecture_Review_v0.1.md` |

---

*Session archivée le 2026-08-10. Protocole verrouillé v0.1. Aucune modification sans revue formelle du Cryptography Review Board.*
