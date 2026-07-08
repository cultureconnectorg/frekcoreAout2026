# 08 — External Review

**FREKCORE Assurance Package v1.0** — Document 08
**Version** : 1.0.0-rc
**Date** : 2026-07-08
**Statut** : 🔴 **PENDING — aucune revue externe encore réalisée**

---

## 1. Objet

Ce document doit consigner les revues externes reçues par FREKCORE :
- Revue de code / architecture par un pair.
- Audit sécurité par un tiers indépendant.
- Retour d'un partenaire pilote.
- Regard académique / institutionnel.

**Aucune revue n'a encore été menée au moment de la publication de ce package v1.0.**

C'est la lacune assumée du présent Assurance Package :
Les audits E/F/G sont **internes**, techniques, honnêtes, mais **auto-produits**.

Une revue externe est nécessaire pour transformer une auto-évaluation en **évaluation certifiante**.

---

## 2. Ce qu'on ne peut PAS s'auto-décerner

- ✅ *"On a mesuré 216 RPS en lecture."* — reproductible, factuel, non contestable.
- ❌ *"FREKCORE est sécurisé."* — nécessite un pentest externe.
- ❌ *"FREKCORE est conforme SOC 2."* — nécessite un audit certifiant.
- ❌ *"L'UX est claire."* — nécessite un test avec vrais utilisateurs (Sprint H1).
- ❌ *"Le business model tient."* — nécessite un premier euro encaissé (Sprint I).

---

## 3. Formats de revue externe pertinents

### 3.1 Peer review technique (recommandé en premier)
**Objectif** : un développeur senior indépendant relit le code + l'architecture pendant 4-8h.

**Livrable attendu** : liste de bugs, de points d'attention, de bonnes pratiques manquantes.

**Coût typique** : 500–1500 € (freelance senior) ou gratuit si peer.

**Où trouver** : LinkedIn / réseau perso / plateforme (Malt, Comet).

### 3.2 Pentest ciblé
**Objectif** : test d'intrusion boîte noire sur l'API publique + tentative de bypass des rate limits + fuzzing.

**Livrable attendu** : rapport de vulnérabilités (CVSS), plan de remédiation.

**Coût typique** : 3 000–10 000 € HT.

**Où trouver** : Yes We Hack, HackerOne (bug bounty programme), ou audit boutique française.

### 3.3 Revue académique / cryptographique
**Objectif** : un chercheur en cryptographie valide la conception (Ed25519 + Merkle + JCS + OTS).

**Livrable attendu** : rapport publié ou lettre de non-conformité + suggestions.

**Coût typique** : gratuit si université / laboratoire intéressé, sinon 2 000–5 000 €.

**Où trouver** : Inria, ENS, contact universitaire local.

### 3.4 Feedback partenaire pilote (H1/H2)
**Objectif** : le premier partenaire qui utilise FREKCORE remplit un formulaire de retour.

**Livrable attendu** : score NPS + verbatims + points d'amélioration.

**Coût** : 0 €, inclus dans le pilote.

**Où trouver** : le premier partenaire commercial (Sprint I).

### 3.5 Regard institutionnel (long terme)
**Objectif** : dépôt du protocole FREK auprès d'un organisme (INPI, ETSI, IETF).

**Livrable attendu** : reconnaissance officielle, publication de la spec dans un canal standard.

**Coût** : temps administratif + éventuel frais de dépôt.

**Où trouver** : ETSI (standards européens), INPI (marque + spec), IETF (RFC draft si applicable).

---

## 4. Grille de revue proposée (à remplir par un tiers)

Template pour un futur reviewer. À intégrer dans ce document une fois complété.

```
Reviewer : ____________
Date : ____________
Format (peer / pentest / academic / partner) : ____________
Durée investie : _____ heures

===============================================
SECTION 1 — Architecture (§ doc 01)
===============================================
- Structure globale claire : [OUI / NON / PARTIELLEMENT]
- Séparation des responsabilités : ____
- Documentation lisible : ____

Remarques : ____________
Suggestions : ____________

===============================================
SECTION 2 — Sécurité (§ doc 02)
===============================================
- Modèle de menaces exhaustif : [OUI / NON]
- Contrôles crypto corrects : ____
- Contrôles d'accès robustes : ____
- Gestion clé Ed25519 acceptable : ____
- Backup + restore fiable : ____
- Zero PII vérifié : ____

Vulnérabilités critiques (P0) : ____________
Points d'attention (P1) : ____________

===============================================
SECTION 3 — Preuve d'existence (§ doc 03)
===============================================
- Verifier standalone fonctionne : ____
- Preuve OTS vérifiable indépendamment : ____
- Argumentation souveraineté convaincante : ____

===============================================
SECTION 4 — Performance (§ doc 04)
===============================================
- Méthodologie reproductible : ____
- Chiffres cohérents : ____
- Goulots identifiés pertinents : ____

===============================================
SECTION 5 — Résilience (§ doc 05)
===============================================
- Scénarios chaos pertinents : ____
- Verdicts crédibles : ____

===============================================
CONCLUSION GLOBALE
===============================================
Note globale (1-10) : ____
Recommandé pour production : [OUI / NON / AVEC RÉSERVES]
Réserves : ____________

Signature reviewer : ____________
```

---

## 5. Prochaines actions concrètes

Pour transformer ce document en revue externe **effective** :

- 🟠 **Étape 1** : choisir 1 peer developer parmi ton réseau, lui envoyer le Assurance Package v1.0 par email → obtenir 2h de retour dans les 15 jours.
- 🟠 **Étape 2** (optionnel) : sollicitier un pentest léger (~1500 € boutique française).
- 🟠 **Étape 3** : au premier partenaire pilote, insérer la grille de revue en fin de contrat.
- 🟢 **Étape 4** (long terme) : envisager un dépôt ETSI / INPI pour la spec FREK.

---

## 6. Ce document répond à

- *Qui a validé FREKCORE de manière indépendante ?* → **Personne encore. Voir §3 pour les formats disponibles.**
- *Comment obtenir cette validation ?* → §3 + §5
- *Quel format utiliser ?* → §4 (grille prête à envoyer)

---

## 7. Note honnête

Ce document existe **précisément parce qu'il est vide**.

Un Assurance Package sérieux ne peut pas prétendre à la complétude sans avoir été confronté à un regard externe. Le vide de ce document 08 est le point le plus fragile — et le plus honnête — du package v1.0.

C'est aussi la prochaine action prioritaire du fondateur.
