# FREK — Credentials de test

## API Client (FREK v1)

Utilisez ces credentials pour obtenir un access_token via :
`POST /api/v1/auth/token`
Body : `{"client_id": "...", "client_secret": "...", "grant_type": "client_credentials"}`

Les valeurs sont chargees depuis `/app/backend/.env` :

- **client_id** : `FREK_CLIENT_KILTIKONET_ID` (defaut: `kiltikonet-cc2026`)
- **client_secret** : `FREK_CLIENT_KILTIKONET_SECRET`
- Permissions : `emit`, `stage`, `stats`

- **client_id stats-only** : `FREK_CLIENT_CVLBRAIN_ID` (defaut: `cvl-brain`)
- **client_secret** : `FREK_CLIENT_CVLBRAIN_SECRET`
- Permissions : `stats`

## Recuperer rapidement (bash)

```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
CID=$(grep FREK_CLIENT_KILTIKONET_ID /app/backend/.env | cut -d '=' -f2)
CSEC=$(grep FREK_CLIENT_KILTIKONET_SECRET /app/backend/.env | cut -d '=' -f2)
TOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d "{\"client_id\":\"$CID\",\"client_secret\":\"$CSEC\",\"grant_type\":\"client_credentials\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
```

## Dashboard prive

- Route : `/dashboard` (acces via lien discret "ops" dans le footer)
- Aucune auth UI (deploiement prive)

## Stripe

- Cle restricted live : `STRIPE_SECRET_KEY` (rk_live_...) dans `/app/backend/.env`

## AWS SES

- Region : eu-west-1 (config `/app/backend/.env`)
- Sender : `frekcore@gmail.com` (verification SES Sandbox cote utilisateur)
- Mode fallback (`logged`) tant que sender non verifie
