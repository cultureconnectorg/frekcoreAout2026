# FREK — Credentials de test

## API Client (FREK v1)

`POST /api/v1/auth/token` avec `{"client_id":"...","client_secret":"...","grant_type":"client_credentials"}`

Valeurs depuis `/app/backend/.env` :
- **client_id (emit/stage/stats)** : `FREK_CLIENT_KILTIKONET_ID` (defaut: `kiltikonet-cc2026`)
- **client_secret** : `FREK_CLIENT_KILTIKONET_SECRET`
- **client_id (stats only)** : `FREK_CLIENT_CVLBRAIN_ID` (defaut: `cvl-brain`)
- **client_secret** : `FREK_CLIENT_CVLBRAIN_SECRET`

## PWA Scanner Staff (auth PIN)

`POST /api/v1/staff/login` avec `{"agent_id":"...","pin":"...."}`

Comptes seedes au demarrage seulement lorsque chaque variable `FREK_STAFF_*_PIN`
est configuree. Aucun PIN par defaut n'est accepte en production. Les PINs de
demonstration historiques ne peuvent etre actives qu'en developpement avec
`FREK_ALLOW_INSECURE_DEV_STAFF_PINS=true`; ils ne doivent jamais etre utilises
hors environnement local :

| agent_id        | PIN  | role             | permissions                                              | zones                  |
|-----------------|------|------------------|----------------------------------------------------------|------------------------|
| SUPERVISEUR-01  | `$FREK_STAFF_SUPERVISEUR_PIN` | superviseur      | scan_access, scan_cashless, emit_walkin, view_stats      | toutes                 |
| EMISSION-01     | `$FREK_STAFF_EMISSION_PIN`    | agent_emission   | scan_access, scan_cashless, emit_walkin                  | ENTREE                 |
| ACCES-01        | `$FREK_STAFF_ACCES_PIN`       | agent_acces      | scan_access                                              | ENTREE, SCENE          |
| CASHLESS-01     | `$FREK_STAFF_CASHLESS_PIN`    | agent_cashless   | scan_access, scan_cashless                               | EXPOSANTS              |

## Recuperer un token rapidement (bash)

```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)

# Client kiltikonet
CID=$(grep FREK_CLIENT_KILTIKONET_ID /app/backend/.env | cut -d '=' -f2)
CSEC=$(grep FREK_CLIENT_KILTIKONET_SECRET /app/backend/.env | cut -d '=' -f2)
KTOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d "{\"client_id\":\"$CID\",\"client_secret\":\"$CSEC\",\"grant_type\":\"client_credentials\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Staff superviseur (la valeur du PIN doit provenir d'un gestionnaire de secrets)
STOKEN=$(curl -s -X POST "$API_URL/api/v1/staff/login" \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\":\"SUPERVISEUR-01\",\"pin\":\"$FREK_STAFF_SUPERVISEUR_PIN\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
```

## Dashboard prive

- Route : `/dashboard` (acces via lien discret "ops" dans le footer)
- Aucune auth UI

## PWA Scanner Staff

- Route : `/scan` (redirige vers `/scan/login` si pas de token)
- Manifest : `/scan-manifest.webmanifest` · Service worker : `/scan-sw.js`

## Stripe

- Cle restricted live : `STRIPE_SECRET_KEY` (rk_live_...) dans `/app/backend/.env`

## AWS SES

- Region : eu-west-1
- Sender : `frekcore@gmail.com` (verification SES Sandbox cote utilisateur)
- Mode fallback (`logged`) tant que sender non verifie


## Sync Baserow (Admin)

`X-Admin-Key: $SECRET_KEY` requis. Token `BASEROW_TOKEN` actuellement 401 (a regenerer cote baserow.io).

```bash
ADMIN_KEY=$(grep "^SECRET_KEY=" /app/backend/.env | cut -d '=' -f2)
curl -s "$API_URL/api/v1/sync/baserow/status" -H "X-Admin-Key: $ADMIN_KEY"
```

## SMTP frekcore.com (en attente creds utilisateur)

Variables a definir dans `/app/backend/.env` :
- `SMTP_HOST` (ex: ssl0.ovh.net, mail.gandi.net)
- `SMTP_PORT` (465 SSL ou 587 STARTTLS)
- `SMTP_USER` (ex: noreply@frekcore.com)
- `SMTP_PASSWORD`
- `SMTP_FROM` (ex: "FrekCore <noreply@frekcore.com>")
