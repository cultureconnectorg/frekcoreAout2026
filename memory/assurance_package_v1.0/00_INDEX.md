# FREKCORE Assurance Package v1.0

**Version** : 1.0.0-rc
**Gel** : 2026-07-08T13:24:00Z
**Auteur** : FREKCORE
**Statut global** : 7/10 documents remplis, 3/10 templates ou vides (voir §3)

---

## Contenu du package

| # | Document | Statut | SHA-256 (voir 10) |
|---|---|---|---|
| **01** | Architecture Overview | ✅ Rempli | `eb1ded3b...` |
| **02** | Security Model | ✅ Rempli | `69ad1d5e...` |
| **03** | Proof of Existence Audit | ✅ Rempli (Sprint E) | `2694d9de...` |
| **04** | Performance Audit | ✅ Rempli (Sprint F) | `ebd89a8c...` |
| **05** | Resilience Audit | ✅ Rempli (Sprint G + 4 P1 fixes) | `7c3ec9d6...` |
| **06** | Field Test Report | 🟡 TEMPLATE (H1 non exécuté) | `1c0b54ae...` |
| **07** | Business Model | ✅ Rempli (cadre chiffré, pas de vente) | `13b373db...` |
| **08** | External Review | 🔴 VIDE (aucune revue externe encore) | `30008f5f...` |
| **09** | Version History | ✅ Rempli | `eef1af91...` |
| **10** | Hash Registry | ✅ Rempli (auto-hashé `5b79e9fb...`) | — |

---

## 1. À qui ce package s'adresse

- **Investisseur due diligence** : lire 01 + 02 + 03 + 04 + 05 + 10.
- **Régulateur / notariat** : lire 01 + 02 + 03 + 09.
- **Partenaire commercial B2B** : lire 01 + 03 + 07 + 06 (quand rempli).
- **Développeur externe** : lire 01 + 09 + spec `/api/v1/spec/`.
- **Auditeur de sécurité** : lire 02 + 08 (grille de revue) + 10.
- **Auditeur SOC 2 / ISO 27001** : lire 01 + 02 + 05 + 08 + 09.

---

## 2. Comment lire ce package

**Lecture rapide (20 minutes)** :
1. `01_Architecture_Overview.md` — vue en 5 minutes de ce qu'est FREKCORE.
2. `10_Hash_Registry.md` — vérifier l'intégrité du package.
3. Choisir 1 audit (03, 04 ou 05) selon centre d'intérêt.

**Lecture complète (2 heures)** :
Lire les 10 documents dans l'ordre.

**Vérification cryptographique** :
```bash
# Recalculer les hashes
sha256sum 0*_*.md 1*_*.md

# Comparer avec 10_Hash_Registry.md
```

---

## 3. Ce que ce package NE contient PAS

- ❌ **Preuve d'usage réel en production** (Sprint H1 pas encore exécuté).
- ❌ **Preuve de traction commerciale** (aucun contrat signé, aucun euro encaissé).
- ❌ **Revue externe** (aucun regard indépendant encore reçu).
- ❌ **Audit certifiant SOC 2 / ISO 27001** (documentation prête, audit non réalisé).
- ❌ **Bug bounty** (pas encore ouvert).

Ces lacunes sont **assumées et documentées**.
Elles définissent le périmètre de ce package v1.0.

---

## 4. Prochaines étapes vers v1.0 (Production Candidate)

- 🟠 Exécuter Sprint H1 (labo 5 personnes) → remplir `06_Field_Test_Report.md`.
- 🟠 Solliciter 1 peer review → commencer à remplir `08_External_Review.md`.
- 🟠 Signer 1 pilote payant → clore Sprint I.
- 🟡 Envisager pentest boutique (500-1500 €) → renforcer 02 + 08.
- 🟢 (Optionnel) Notariser ce package sur FREK-Chain (procédure dans `10 §7`).

---

## 5. Contact & suite

**Documentation technique** : `GET /api/v1/spec/`
**Verifier standalone** : `GET /api/v1/passport/verifier/python`
**Clé publique** : `GET /.well-known/jwks.json`
**Explorer public** : `/explorer` (frontend)

Pour toute question sur ce package :
- Envoyer un email à FREKCORE en joignant le hash `5b79e9fb...` (registre §10) pour identifier la version exacte.

---

## 6. Note honnête finale

Ce package v1.0 est **le premier livrable formel de FREKCORE**.

Il fixe un état, il documente une doctrine, il expose ses forces **et ses lacunes**.

Il n'est pas une plaquette commerciale. Il est un objet auditable.

Toute divergence future (bug, incident, évolution) doit produire une nouvelle version numérotée
(v1.0.1, v1.1.0, v2.0.0) avec son propre Assurance Package correspondant.

FREKCORE devient ainsi son propre notaire : chaque version de l'infrastructure
est authentifiée par son propre paquet de preuves.

---

**Auto-hash SHA-256 de ce fichier INDEX** : à calculer après finalisation.

```bash
sha256sum 00_INDEX.md
```

**SHA-256 INDEX** : `415300092982e6538ba660710cedd40162439a6b987c20d8c20e9792d62688e7`
