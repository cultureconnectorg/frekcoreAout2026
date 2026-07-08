# FIELD_CHECKLIST — Sprint H1 Labo FREKCORE

**Version** : 1.0
**Date** : à compléter (jour J)
**Durée totale** : 1h30 max

---

## 1. Personnes requises (5)

| Rôle | Prénom | Fonction pendant le labo |
|---|---|---|
| Organisateur | \_\_\_\_\_\_\_\_ | Anime, chronomètre, note les incidents |
| Opérateur 1 | \_\_\_\_\_\_\_\_ | Staff scanner PWA — zone ENTRÉE |
| Opérateur 2 | \_\_\_\_\_\_\_\_ | Staff scanner PWA — zone SCÈNE |
| Porteur 1 | \_\_\_\_\_\_\_\_ | Utilisateur final naïf, non technique |
| Porteur 2 | \_\_\_\_\_\_\_\_ | Utilisateur final naïf, non technique |

---

## 2. Matériel

- [ ] 1 ordinateur connecté à FREKCORE (organisateur, écran de contrôle)
- [ ] 2 smartphones ou tablettes pour les opérateurs (Chrome/Safari récent, PWA installée sur `/scan`)
- [ ] 2 smartphones pour les porteurs (peu importe la marque)
- [ ] 4 badges NFC OU 4 codes QR imprimés (sinon codes 6 chiffres fictifs)
- [ ] 1 impression papier de ce document + du protocole
- [ ] 1 chronomètre (téléphone de l'organisateur)
- [ ] 1 stylo par personne
- [ ] Grille de mesure `FIELD_RESULTS.csv` imprimée

---

## 3. Pré-vol (à faire la veille — organisateur)

- [ ] Vérifier `curl https://<API>/api/v1/health/deep` → status = "healthy"
- [ ] Vérifier `chain integrity: True`
- [ ] Créer 2 comptes staff PIN via `/api/v1/staff` (ex: PIN 1234 et 5678)
- [ ] Générer 4 FREK-IDs vierges pour les porteurs (ou laisser l'émission se faire pendant le test)
- [ ] Charger complètement les batteries de tous les appareils
- [ ] Tester le Wi-Fi du lieu (ou 4G partagée en backup)

---

## 4. Déroulé (1h30)

### T+0 → 10 min — Accueil et briefing

- Expliquer aux porteurs UNIQUEMENT : *"On va tester une nouvelle façon de valider ton entrée dans un événement."* **Ne pas expliquer la crypto**.
- Expliquer aux opérateurs : *"Vous scannez, vous validez, comme un contrôleur de billets."*
- Sortir les tickets ou badges NFC/QR.

### T+10 → 30 min — Test 1 : Création FREK-ID (porteurs)

Chaque porteur :
1. Ouvre le site FREKCORE sur son smartphone
2. Va sur `/creer-mon-frek` (ou équivalent public — **si pas encore existant, on utilise `/scan` en mode saisie manuelle**)
3. Saisit son prénom + son email
4. Reçoit son FREK-ID (afficher clairement à l'écran)

**Mesures** :
- ⏱️ Temps entre "clic démarrer" et "FREK-ID reçu"
- 🚫 Nombre d'échecs (page qui rame, formulaire cassé, non compris)
- 🗣️ Verbatims sur la compréhension (*"c'est quoi ça ?"*, *"pourquoi ils me demandent mon email ?"*)

### T+30 → 55 min — Test 2 : Scan d'accès (opérateurs)

Chaque opérateur ouvre son PWA `/poste`, se connecte avec son PIN, choisit une zone.
Chaque porteur passe devant chaque opérateur, avec badge NFC OU code QR affiché à l'écran de son propre smartphone.

**Faire au moins 4 scans par opérateur = 8 scans total**.

**Mesures** :
- ⏱️ Temps par scan (du moment où l'opérateur touche l'appareil au moment où le résultat s'affiche)
- 🚫 Nombre de rescans nécessaires
- 🚫 Nombre de scans refusés à tort
- 🚫 Nombre de scans acceptés à tort (badge invalide accepté)
- 🗣️ Retour opérateur : *"quand le scan ne marche pas, tu comprends pourquoi ?"*

### T+55 → 70 min — Test 3 : Vérification indépendante (organisateur)

Pour chaque porteur :
1. Ouvrir `/verify/{frek_id}` sur l'ordinateur de l'organisateur
2. Vérifier que la page affiche : nom, événement, date, statut, hash notarisation, badge de validité
3. Copier le `passport.json` (bouton Export)
4. Le vérifier via `python3 verify_passport.py --passport passport.json --public-key-b64 XXX` — doit répondre `valid: true`

**Mesures** :
- ⏱️ Temps de vérification par identité
- 🚫 Nombre d'erreurs
- 🗣️ Est-ce compréhensible pour un tiers non technique ?

### T+70 → 90 min — Débriefing collectif

Poser aux 5 personnes (par écrit sur `FIELD_RESULTS.csv`) :
1. **Sur une échelle de 1 à 5**, à quel point c'était clair ?
2. **Un mot pour décrire l'expérience** ?
3. **Un point que tu changerais** ?
4. **Est-ce que tu recommanderais** ce système à un ami organisateur ?
5. **Utiliserais-tu FREKCORE** pour ton propre événement / usage ?

Prendre des photos discrètes des visages (avec accord) pour capter les micro-expressions — c'est la donnée qualitative la plus honnête.

---

## 5. Après le labo (organisateur, dans les 24h)

- [ ] Compléter `FIELD_RESULTS.csv` avec toutes les mesures
- [ ] Rédiger 5 verbatims par catégorie dans `FIELD_REPORT_v1.0.md`
- [ ] Lister les 3 problèmes les plus fréquents observés
- [ ] Décider : quelles corrections **AVANT** d'ouvrir à 50 personnes (H2) ?
- [ ] Fixer une date pour H2

**Règle d'or** : ne corriger que ce que le terrain a explicitement révélé. Pas de spéculation.

---

## 6. Critères de succès H1

| Métrique | Seuil minimum |
|---|---|
| Temps moyen création FREK-ID | < 60 secondes |
| Taux de succès création (aucune assistance) | > 60 % |
| Temps moyen par scan | < 5 secondes |
| Taux de succès scan (badge valide accepté) | > 90 % |
| Taux d'erreur scan (badge invalide accepté à tort) | 0 % |
| Note globale des porteurs (1-5) | > 3 |

Si l'un de ces seuils n'est pas atteint : **PAS de H2 avant correction**.

Si tous atteints : **feu vert pour H2** (50-100 utilisateurs).

---

## 7. Ce qu'on N'attend PAS de ce labo

- Chiffres statistiques (5 personnes = pas d'échantillon)
- Preuve de scalabilité (déjà validée en Sprint F)
- Validation économique (c'est Sprint I)
- Test de résilience réseau (déjà validé en Sprint G)

**Ce labo teste UNIQUEMENT l'ergonomie et la compréhension humaine.**
# FIELD_TEST_PROTOCOL — Sprint H1 Labo FREKCORE

**Objectif** : mesurer si un humain non-technique peut utiliser FREKCORE dans une situation réelle.

**Question fermée par ce test** : *"L'UX de FREKCORE est-elle adaptée à un usage grand public sans formation préalable ?"*

---

## 1. Design du protocole

Ce protocole suit une logique "**observation muette**" :
- L'organisateur observe, chronomètre, note.
- **Il n'aide pas** les porteurs et opérateurs, sauf en cas de blocage total (>60s sans progression).
- Chaque coup de main donné est un **point de friction UX à noter**.

C'est plus important que les résultats bruts.

---

## 2. Parcours 1 — Création FREK-ID (porteur autonome)

### Consigne à lire au porteur

> *"Tu vas participer à un événement culturel. Pour valider ton entrée, on te demande de créer ton identifiant FREKCORE. Vas sur cette URL sur ton smartphone : [URL du site]. Tu as 3 minutes."*

### Ne pas dire

- Ne pas expliquer ce qu'est FREKCORE.
- Ne pas dire où cliquer.
- Ne pas expliquer les termes techniques (Ed25519, notarisation, etc.).

### Observer

| Signal | Signification | Points |
|---|---|---|
| Le porteur trouve le bouton "Créer mon FREK" en < 15s | Nav claire | ✅ +2 |
| Le porteur cherche > 30s | Nav pas claire | ❌ -1 |
| Le porteur pose une question | Point de friction | ❌ -1 |
| Le porteur abandonne | Blocage total | ❌ -3 |
| Le porteur voit son FREK-ID à l'écran et sait ce que c'est | Feedback OK | ✅ +2 |
| Le porteur voit son FREK-ID et demande "c'est tout ?" | Feedback pauvre | ❌ -1 |

### Mesurer

- **T_création** = temps entre "clic démarrer" et "FREK-ID visible"
- **Nb_questions** posées à l'organisateur
- **Nb_hésitations** > 5s

---

## 3. Parcours 2 — Scan d'accès (opérateur autonome)

### Consigne à lire à l'opérateur

> *"Tu es contrôleur d'entrée. Sur cette tablette, tu vas scanner les badges des invités et vérifier qu'ils peuvent entrer. Tu as un code PIN : [1234]. La zone que tu contrôles est [ENTRÉE / SCÈNE]."*

### Ne pas dire

- Ne pas expliquer où est le bouton scan.
- Ne pas expliquer les messages d'erreur.
- Ne pas dire quoi faire si le scan échoue.

### Observer

| Signal | Points |
|---|---|
| Login PIN < 10s | ✅ +2 |
| Login PIN > 30s | ❌ -1 |
| Trouve le bouton scan en < 5s | ✅ +2 |
| Réussit scan valide au 1er essai | ✅ +2 |
| Réussit scan valide après retry | 🟡 0 |
| Accepte un badge invalide | ❌ -3 (grave) |
| Refuse un badge valide | ❌ -2 |
| Comprend le message d'erreur | ✅ +1 |

### Mesurer

- **T_scan** = temps entre "voir le badge" et "résultat affiché"
- **Nb_rescans** par scan
- **Nb_false_positive** (badges invalides acceptés)
- **Nb_false_negative** (badges valides refusés)

---

## 4. Parcours 3 — Vérification indépendante (organisateur)

### Consigne à soi-même

> *"Je suis un journaliste sceptique. J'ai reçu la promesse que FREKCORE certifie cet événement. Je veux vérifier — sans aider FREKCORE — que cette promesse est tenue."*

### Étapes

1. Ouvrir `/verify/{frek_id}` sur un ordinateur.
2. Copier le passport (bouton Export).
3. Se placer HORS-LIGNE (Wi-Fi coupé).
4. Exécuter localement `python3 verify_passport.py --passport passport.json --public-key-b64 XXX`.
5. Constater la réponse.

### Observer

| Signal | Points |
|---|---|
| Page `/verify` claire | ✅ +2 |
| Export fonctionne | ✅ +2 |
| Verifier hors-ligne répond `valid: true` | ✅ +3 (souveraineté validée) |
| Un tiers non-technique comprend la page verify | ✅ +2 |

### Mesurer

- **T_verify** = temps entre "voir le lien /verify" et "confirmation valid: true"

---

## 5. Débriefing collectif — 20 minutes

### Format

Assis en cercle. Pas de PowerPoint. Chacun parle 2 minutes maximum.

### Questions posées à chaque personne

1. Sur une échelle de 1 à 5, qu'avez-vous pensé de l'expérience ?
2. Un mot pour la décrire ?
3. Un point à changer ?
4. Le recommanderiez-vous ?
5. Utiliseriez-vous FREKCORE pour votre propre usage / événement ?

### Prendre note

Écrire chaque réponse dans `FIELD_RESULTS.csv` colonne "verbatim".

**Ce qui vaut plus que les chiffres** : les silences, les hésitations, les rires nerveux. Notez-les.

---

## 6. Décision post-labo

Une fois `FIELD_REPORT_v1.0.md` complété (dans les 24h après le labo) :

- Si **tous les critères de succès sont atteints** (voir `FIELD_CHECKLIST.md` §6) : **passer à H2** (50-100 utilisateurs).
- Si **un ou plusieurs critères sont manqués** : **corriger avant H2**. Un critère manqué = une correction. Pas de refonte spéculative.
- Si **plus de 3 critères sont manqués** : **retour en Sprint UX** (redesign des points de blocage), pas H2.

---

## 7. Anti-patterns à éviter

- ❌ Aider en cours de test (fausse les mesures)
- ❌ Sur-interpréter les silences (attendre 60s avant intervention)
- ❌ Faire 2 labos successifs le même jour (fatigue observationnelle)
- ❌ Choisir des porteurs déjà familiers avec FREKCORE
- ❌ Modifier le code entre les 5 tests (chaque porteur voit la même version)
- ❌ Rédiger le rapport avant d'avoir toutes les données brutes

---

## 8. Attitude générale

L'organisateur doit rester **neutre et silencieux**. Si un porteur galère, ne pas sauver la face de FREKCORE. Le but n'est pas de valider le produit, c'est de découvrir ses défauts.

**Un labo H1 qui révèle 5 défauts est un succès.**
**Un labo H1 qui révèle 0 défaut est un labo mal fait.**
# FIELD_REPORT — Sprint H1 Labo FREKCORE

**Version** : à compléter (v1.0 après labo)
**Date labo** : \_\_\_\_\_\_\_\_
**Lieu** : \_\_\_\_\_\_\_\_
**Version FREKCORE testée** : 1.0.0-rc
**Baseline chain** : height=\_\_\_\_, integrity ok
**Organisateur** : \_\_\_\_\_\_\_\_

---

## 1. Participants (5)

| # | Rôle | Prénom | Profil (âge/tech-savviness) |
|---|---|---|---|
| 1 | Organisateur | | |
| 2 | Opérateur | | |
| 3 | Opérateur | | |
| 4 | Porteur | | |
| 5 | Porteur | | |

---

## 2. Résumé exécutif (à écrire APRÈS)

**En 3 phrases max** : *ce qui a marché / ce qui a bloqué / quelle décision*.

...

---

## 3. Résultats bruts

### 3.1 Parcours 1 — Création FREK-ID

| Porteur | Temps (s) | Nb questions | Nb hésitations | Succès sans aide | Note |
|---|---|---|---|---|---|
| P1 | | | | ☐ | /5 |
| P2 | | | | ☐ | /5 |

**Moyenne T_création** : \_\_\_\_\_\_\_ secondes
**Seuil cible** : < 60 s
**Verdict** : ☐ PASS ☐ FAIL

### 3.2 Parcours 2 — Scan d'accès

| Opérateur | Nb scans | T_scan moyen (s) | Rescans | False positive | False negative | Succès |
|---|---|---|---|---|---|---|
| O1 | | | | | | |
| O2 | | | | | | |

**Moyenne T_scan** : \_\_\_\_\_\_\_ secondes
**Seuil cible** : < 5 s
**Faux positifs** : \_\_\_\_ (seuil : 0)
**Verdict** : ☐ PASS ☐ FAIL

### 3.3 Parcours 3 — Vérification offline

| Passport vérifié | Temps (s) | Résultat verifier standalone | Compréhensible par tiers |
|---|---|---|---|
| P1.passport | | ☐ valid ☐ invalid | ☐ oui ☐ non |
| P2.passport | | ☐ valid ☐ invalid | ☐ oui ☐ non |

**Verdict souveraineté** : ☐ PASS ☐ FAIL

---

## 4. Analyse qualitative

### 4.1 Verbatims marquants (min. 5)

- "..." — [rôle / prénom]
- "..." — [rôle / prénom]
- "..." — [rôle / prénom]
- "..." — [rôle / prénom]
- "..." — [rôle / prénom]

### 4.2 Notes globales (1-5)

| Participant | Note | Un mot |
|---|---|---|
| P1 | /5 | |
| P2 | /5 | |
| O1 | /5 | |
| O2 | /5 | |
| Org | /5 | |

**Moyenne** : \_\_\_\_\_\_
**Seuil cible** : > 3

### 4.3 Recommanderaient (oui/non/peut-être)

- P1 : ☐ oui ☐ non ☐ peut-être
- P2 : ☐ oui ☐ non ☐ peut-être
- O1 : ☐ oui ☐ non ☐ peut-être
- O2 : ☐ oui ☐ non ☐ peut-être

### 4.4 Utiliseraient pour leur propre usage

- P1 : ☐ oui ☐ non
- P2 : ☐ oui ☐ non
- O1 : ☐ oui ☐ non
- O2 : ☐ oui ☐ non

---

## 5. Points de blocage identifiés

Lister les incidents observés. **Un incident = une ligne**.

| # | Parcours | Symptôme observé | Cause probable | Sévérité |
|---|---|---|---|---|
| 1 | | | | ☐ P0 bloquant ☐ P1 gênant ☐ P2 mineur |
| 2 | | | | |
| 3 | | | | |

---

## 6. Verdict global sur les critères de succès

| Critère | Seuil | Mesuré | Verdict |
|---|---|---|---|
| Temps moyen création | < 60 s | | ☐ PASS ☐ FAIL |
| Taux succès création | > 60 % | | ☐ PASS ☐ FAIL |
| Temps moyen scan | < 5 s | | ☐ PASS ☐ FAIL |
| Taux succès scan | > 90 % | | ☐ PASS ☐ FAIL |
| Faux positifs | 0 | | ☐ PASS ☐ FAIL |
| Note globale porteurs | > 3 | | ☐ PASS ☐ FAIL |

**Verdict H1** : ☐ TOUS PASS → feu vert H2 ☐ 1-2 FAIL → correction ciblée ☐ 3+ FAIL → retour Sprint UX

---

## 7. Actions décidées

Uniquement ce que le terrain a révélé. **Pas de spéculation**.

- [ ] Action 1 (P0/P1/P2) : ...
- [ ] Action 2 : ...
- [ ] Action 3 : ...

---

## 8. Décision pour H2

- ☐ Aller à H2 dans l'état actuel (50-100 utilisateurs)
- ☐ Corriger les points ci-dessus, puis H2 dans [X jours]
- ☐ Retour Sprint UX avant H2

**Date estimée H2** : \_\_\_\_\_\_\_\_
**Événement pilote pour H2** : \_\_\_\_\_\_\_\_

---

## 9. Reliability Report v1.0 — état d'avancement

- [E] Proof of Existence ✅
- [F] Performance ✅
- [G] Resilience ✅
- **[H1] Terrain labo** ☐ (ce document une fois rempli)
- [H2] Terrain pilote 50-100 ⏭️
- [I] Business viability ⏭️

---

**SHA-256 de ce rapport** : à calculer une fois rempli via
`sha256sum FIELD_REPORT_v1.0.md`

**Rapport lui-même notarisable via** `/api/v1/notary/notarize` pour figer sa date.
