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
