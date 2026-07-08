> ⚠️ **CONFIDENTIAL — FREKCORE Internal**
> Distribution restricted. NDA required for external sharing.
> Ce document appartient au niveau Vault (Level 3) de la doctrine IP FREKCORE.

---


# BUSINESS_MODEL — FREKCORE v1.0

**Version** : 1.0
**Date** : 2026-07-08
**Objectif** : répondre à *"combien coûte une preuve FREK et combien peut-on la facturer ?"*

Ce document ne vise pas à modéliser 50 scénarios. Il donne un cadre chiffré simple pour préparer un premier rendez-vous partenaire.

---

## 1. Structure de coûts marginaux (par preuve)

### 1.1 Coûts fixes mensuels de FREKCORE (à répartir)

| Poste | Coût mensuel estimé | Notes |
|---|---|---|
| Hosting production (K8s, 2 replicas, 8 GB RAM) | ~ 80 € | Emergent ou équivalent OVH |
| MongoDB Atlas M20 (avec backup) | ~ 90 € | 20 GB, réplique auto |
| Bande passante | ~ 15 € | 100 GB / mois |
| Nom de domaine + certificats | ~ 5 € | frekcore.com |
| Monitoring (Sentry, UptimeRobot free tier) | 0 € | Free tier suffit v1 |
| **Total fixe** | **~ 190 € / mois** | ≈ 2 300 € / an |

### 1.2 Coûts variables par preuve

| Opération | Coût unitaire technique |
|---|---|
| 1 FREK-ID émis (Mongo write + Ed25519 signature) | < 0,0001 € (CPU + RAM) |
| 1 block FREK-Chain notarisé | < 0,0001 € (CPU + Mongo) |
| 1 soumission OpenTimestamps (batch groupé) | 0 € (calendars publics gratuits) |
| 1 ancrage Bitcoin (via un batch OTS de 100+ blocks) | 0 € (couvert par les calendars publics ; option relayer premium : ~ 5 € / mois) |
| 1 scan staff PWA | < 0,0001 € |
| 1 vérification passport offline | 0 € (côté client) |

**Coût marginal réel d'une preuve FREK complète : < 0,001 €.**

C'est un ordre de grandeur inférieur à un timbre. La rareté n'est pas dans la production — elle est dans la certification, la doctrine, et la confiance.

---

## 2. Coût réel amorti selon volume

Répartir les 190 €/mois de coûts fixes sur le volume mensuel de preuves émises :

| Volume mensuel | Coût amorti par preuve | Coût amorti par événement (moyen : 1 000 preuves) |
|---|---|---|
| 100 preuves / mois | **1,90 €** | 1 900 € |
| 1 000 preuves / mois | **0,19 €** | 190 € |
| 10 000 preuves / mois | **0,019 €** | 19 € |
| 100 000 preuves / mois | **0,0019 €** | 1,90 € |

Le modèle a une **économie d'échelle brutale**. À partir de 10 000 preuves / mois, la préservation d'une preuve coûte moins de 2 centimes.

---

## 3. Trois cas type

### CAS A — Petit événement culturel (1 nuit, 500 participants)

**Profil** : concert associatif, festival de quartier, vernissage.

**Volume** : 500 FREK-IDs + 1 500 scans (entrée + zone + sortie) + 500 passeports.

**Coût technique marginal** : < 0,50 €
**Coût amorti (si volume mensuel = 500)** : 190 €
**Prix cible facturé** : **500 € forfait** (0,50–1 €/participant + certification incluse)

**Marge brute** : 62 % (190 € / 500 €)

**Argument de vente** :
> *"Chaque participant repart avec une empreinte culturelle certifiée sur Bitcoin, exportable et vérifiable à vie. Vous devenez notaire de vos propres événements."*

---

### CAS B — Événement moyen (festival 3 jours, 10 000 participants)

**Profil** : festival régional, événement pro, colloque international.

**Volume** : 10 000 FREK-IDs + 40 000 scans + génération passeports/DID pour les VIP (~ 200).

**Coût technique marginal** : ~ 10 € (Mongo + hosting fluctuation)
**Coût amorti (si volume mensuel = 10 000)** : 190 €
**Prix cible facturé** : **8 000 € forfait** (0,80 € / participant + suivi J-1 à J+7 inclus)

**Marge brute** : 97,5 % (200 € / 8 000 €)

**Argument de vente** :
> *"Votre événement devient une donnée culturelle permanente et vérifiable par tout tiers, y compris pour votre communication post-événement. Preuve d'impact culturel, subventionnable."*

---

### CAS C — Institution / opérateur culturel (contrat annuel)

**Profil** : ministère de la Culture, mairie, opérateur culturel régional, plateforme éducative, festival annuel majeur.

**Volume** : 100 000+ preuves/an, plusieurs événements, API accès continu.

**Coût technique marginal** : ~ 500 €/an (fluctuations d'infrastructure)
**Coût amorti** : 2 300 € (les frais fixes annuels)
**Prix cible facturé** : **30 000 – 80 000 € / an** (SaaS + support + JCC prépayés)

**Marge brute** : 88–96 %

**Argument de vente** :
> *"Vous obtenez une infrastructure de preuve culturelle souveraine, auditable, notariée sur Bitcoin. Le compteur universel de votre écosystème devient vérifiable indépendamment. Vous ne dépendez d'aucune plateforme US ou chinoise."*

---

## 4. Modèle économique — 3 canaux

### Canal 1 — Forfait événementiel B2B

- Une facturation forfaitaire par événement (Cas A et B).
- Simple à commercialiser.
- Marge brute 60–97 %.

### Canal 2 — Contrat annuel institutionnel

- SaaS annuel + accès API + JCC prépayés (Cas C).
- Récurrence forte.
- Marge brute 88–96 %.

### Canal 3 — API publique métered (auto-inscription)

- Après H2, ouvrir une page tarifs publique.
- Modèle métré : X € par 1 000 FREK-IDs émis.
- Aucun accompagnement, self-serve.
- Idéal pour longue traîne (petits organisateurs, apps tierces).

**Recommandation phase 1** : concentrer sur canaux 1 et 2. Le canal 3 s'ouvre après validation opérationnelle H2 + I.

---

## 5. Seuil de rentabilité

**Point mort à couvrir les coûts fixes (190 €/mois = 2 300 €/an)** :

- 5 événements type "petit" (cas A) par an = 2 500 €
- OU 1 événement type "moyen" (cas B) par an = 8 000 €
- OU 1 contrat institutionnel (cas C, entrée de gamme) = 30 000 €

**FREKCORE est rentable dès le premier contrat institutionnel.**

---

## 6. Comparaison marché

| Concurrent | Modèle | Prix moyen /événement | Souveraineté crypto |
|---|---|---|---|
| Weezevent / Yurplan | Billetterie SaaS | 1–3 % du CA | ❌ Non |
| Blockchain notary services (US) | Notarisation ponctuelle | 20–200 $ / doc | ✅ Oui mais opaque |
| SmartCert (blockchain FR) | Certifs professionnelles | 0,50 € / certif | 🟡 Partiel |
| **FREKCORE** | Infrastructure culturelle souveraine | **0,50–8 €/participant** | ✅ Complète offline |

**Positionnement unique** : personne d'autre ne combine "notariat Bitcoin + verifier offline + doctrine culturelle" à ce prix.

---

## 7. Facturation JCC (Kiltikonet)

Doctrine actuelle : **FrekCore ne touche jamais Stripe côté porteur**. Les paiements B2B passent par Kiltikonet.

Modalités JCC :
- 1 JCC = 1 € HT (ratio 1:1 simple pour v1).
- Recharge Pro via Kiltikonet (Stripe/virement/crypto).
- Consommation API FrekCore = déduction JCC.
- Rapport de consommation mensuel via `/api/v1/admin/metering/{client_id}` (endpoint à ajouter).

**Coût API en JCC** (indicatif) :
- 1 FREK-ID émis : 0,10 JCC
- 1 scan validé : 0,01 JCC
- 1 batch counter (jusqu'à 1 000 events) : 1 JCC
- 1 export passeport signé + notarisé : 0,50 JCC

Ces prix seront ajustés selon les retours partenaires.

---

## 8. Ce que ce document ne fait PAS

- ❌ Pas de simulateur interactif (à construire seulement si un partenaire le demande explicitement).
- ❌ Pas de projection pluriannuelle (spéculatif tant qu'aucun contrat n'est signé).
- ❌ Pas de CAC / LTV (données non disponibles avant plusieurs cycles de vente).
- ❌ Pas de plan de levée de fonds.

**Ce document répond à UNE question** : *"combien ça coûte, combien on facture, combien on garde"*. Rien de plus.

---

## 9. Prochaines actions concrètes

1. 🟠 **Identifier un premier partenaire concret** (Cas A, B ou C).
2. 🟠 **Ouvrir la conversation** avec un pitch de 15 lignes maximum.
3. 🟠 **Adapter les chiffres** au cas réel proposé par ce partenaire.
4. 🟠 **Signer un pilote payant** (même 500 €).
5. 🟠 **Utiliser ce pilote** comme livrable Sprint I terminé.

**Sprint I est fermé quand : un premier euro est encaissé pour une preuve FREK réelle.**

Pas avant.

---

## 10. Endpoint metering à ajouter (Sprint I dev)

Pour préparer le rapport de consommation Pro, ajouter :

```
GET /api/v1/admin/metering/{client_id}?since=YYYY-MM&until=YYYY-MM
→ {
    "client_id": "...",
    "period": {"since": "...", "until": "..."},
    "usage": {
      "identity_emit": N,
      "identity_status_reads": N,
      "passport_generations": N,
      "did_reads": N,
      "vc_reads": N,
      "scans_access": N,
      "counter_events": N,
      "notary_blocks": N
    },
    "jcc_consumed": X,
    "current_balance": Y,
    "invoice_lines": [...]
  }
```

Ce endpoint sera consommé par Kiltikonet pour établir la facturation.

**Effort de dev** : ~ 2h. À faire APRÈS le premier rendez-vous partenaire (pour l'adapter à ses besoins réels).

---

## 11. Reliability Report v1.0 — état d'avancement

- [E] Proof of Existence ✅
- [F] Performance ✅
- [G] Resilience ✅
- [H1] Terrain labo ⏭️ (documents prêts)
- [H2] Terrain pilote ⏭️
- **[I] Business viability** 🟡 (ce document = cadre, mais fermeture ≠ document, fermeture = 1er euro encaissé)

---

**SHA-256 auto-audit** : à calculer via `sha256sum BUSINESS_MODEL_v1.0.md` après review.
