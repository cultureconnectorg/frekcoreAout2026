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
