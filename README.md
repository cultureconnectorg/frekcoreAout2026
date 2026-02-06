# FREK v0.4 — Infrastructure de Preuve Audio Locale

## Qu'est-ce que FREK ?

FREK est un **standard de traçabilité, d'intégrité et de reconnaissance technique du geste DJ**.

FREK n'est PAS :
- Un réseau social
- Une plateforme
- Un outil de surveillance
- Un système de scoring

FREK EST :
- Une spécification ouverte
- Un format de preuve cryptographique
- Un outil de vérification local-first
- Un standard anti-capture

## Installation

### Prérequis
- Node.js >= 18
- Yarn

### Développement local

```bash
# Frontend
cd frontend
yarn install
yarn start
```

Le frontend démarre sur `http://localhost:3000`.

**Note**: Le backend est optionnel et désactivé par défaut. FREK fonctionne entièrement dans le navigateur.

## Structure du Projet

```
/app
├── frontend/                 # Application React
│   ├── src/
│   │   ├── components/      # Composants UI
│   │   ├── pages/           # Pages de l'application
│   │   ├── lib/             # Utilitaires et validation
│   │   └── App.js           # Point d'entrée
│   └── package.json
├── backend/                  # API FastAPI (optionnel)
└── README.md
```

## Routes Disponibles

| Route | Description |
|-------|-------------|
| `/` | Page d'accueil |
| `/docs` | Manifeste et principes |
| `/architecture` | Pipeline technique |
| `/spec` | Spécification .frek.json |
| `/governance` | Modèle de gouvernance |
| `/changelog` | Historique des versions |
| `/verify` | Module de vérification |

## Format .frek.json

```json
{
  "frek_version": "0.4",
  "fingerprint": "sha256:<hex64>",
  "segments": [
    {"t0": 0, "t1": 5, "h": "sha256:<hex64>"}
  ],
  "metadata": {
    "timestamp": "ISO8601",
    "duration": 3600,
    "source_type": "live|studio|rehearsal|dispute"
  },
  "signature": "ed25519:<base64>",
  "public_key": "<base64>"
}
```

## Module de Vérification

Le module `/verify` permet de :

1. **Valider** la structure JSON contre le schéma v0.4
2. **Vérifier** la signature Ed25519
3. **Comparer** le fingerprint avec un fichier audio (optionnel)
4. **Exporter** un rapport de vérification

**Important** : Aucune donnée ne quitte le navigateur. Vérifiable dans les DevTools (onglet Network).

## Limites

- Le fingerprint "demo" utilise SHA-256 sur les données brutes (pas d'analyse spectrale complète)
- La version 0.4 est en phase de développement
- Les segments sont optionnels

## Principes Non Négociables

1. FREK ne juge pas la musique
2. FREK ne classe pas les artistes
3. FREK ne collecte pas de données personnelles
4. FREK ne devient jamais une plateforme
5. FREK fonctionne hors-ligne par défaut

## Licence

Standard ouvert sous licence copyleft.

---

*FREK reconnaît un fait technique, dans un contexte précis.*
