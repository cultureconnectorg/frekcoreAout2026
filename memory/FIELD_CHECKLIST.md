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
