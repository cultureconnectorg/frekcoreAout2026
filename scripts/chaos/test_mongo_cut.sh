#!/usr/bin/env bash
# FREK Sprint G — Chaos Test 1 : Coupure MongoDB
#
# Simule une panne de la base de donnees pendant N secondes,
# mesure la reaction de l'API (erreurs propres ? file d'attente ? crash ?)
# puis restaure et verifie la coherence.

set -uo pipefail

API="${API:-$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)}"
DOWN_DURATION=15
OUT=/app/loadtest_results/chaos_mongo.log
mkdir -p "$(dirname $OUT)"; : > "$OUT"

log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$OUT"; }

log "=== TEST 1 : COUPURE MONGO (${DOWN_DURATION}s) ==="

# Baseline
BASELINE_BLOCKS=$(curl -s "$API/api/v1/notary/chain/status" | python3 -c "import sys,json;print(json.load(sys.stdin)['height'])" 2>/dev/null)
BASELINE_HEALTH=$(curl -s "$API/api/v1/health/deep" | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])" 2>/dev/null)
log "  baseline: height=$BASELINE_BLOCKS, health=$BASELINE_HEALTH"

# Stop Mongo
log "  --- STOPPING mongodb ---"
sudo supervisorctl stop mongodb 2>&1 | tee -a "$OUT"

sleep 2

# Probe API pendant que Mongo est down
log "  --- Probing API while Mongo DOWN ---"
LIVE=$(curl -s -o /dev/null -w "%{http_code}" "$API/api/v1/health/live")
READY=$(curl -s -o /dev/null -w "%{http_code}" "$API/api/v1/health/ready")
DEEP_HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$API/api/v1/health/deep")
DEEP_STATUS=$(curl -s "$API/api/v1/health/deep" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','n/a'))" 2>/dev/null)
PULSE_HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$API/api/core/ecosystem/pulse")

log "  /health/live  -> $LIVE (expected 200 : liveness = process only)"
log "  /health/ready -> $READY (expected 503 : Mongo down)"
log "  /health/deep  -> $DEEP_HTTP status=$DEEP_STATUS (expected: degraded, mongo.ok=false)"
log "  /pulse        -> $PULSE_HTTP (expected 500/503 propre, pas de crash)"

# Emit attempt while Mongo down
CSEC=$(grep FREK_CLIENT_KILTIKONET_SECRET /app/backend/.env | cut -d= -f2)
EMIT_ATTEMPT=$(curl -s -o /tmp/emit_body -w "%{http_code}" --max-time 5 \
  -X POST "$API/api/v1/identity/emit" \
  -H "Content-Type: application/json" \
  -d '{"email":"chaos-mongo@test.io","source":"chaos"}')
log "  POST /identity/emit (no auth) -> $EMIT_ATTEMPT (attendu 401)"

# Wait remaining time then restart
sleep $DOWN_DURATION

log "  --- STARTING mongodb ---"
sudo supervisorctl start mongodb 2>&1 | tee -a "$OUT"

# Give Mongo time to accept connections
sleep 5

# Verify recovery
RECOVER_LIVE=$(curl -s -o /dev/null -w "%{http_code}" "$API/api/v1/health/live")
RECOVER_READY=$(curl -s -o /dev/null -w "%{http_code}" "$API/api/v1/health/ready")
RECOVER_HEIGHT=$(curl -s "$API/api/v1/notary/chain/status" | python3 -c "import sys,json;print(json.load(sys.stdin)['height'])" 2>/dev/null)
RECOVER_INTEGRITY=$(curl -s "$API/api/v1/notary/chain/verify" | python3 -c "import sys,json;print(json.load(sys.stdin)['valid'])" 2>/dev/null)

log "  --- APRES REPRISE ---"
log "  /health/live   -> $RECOVER_LIVE (expected 200)"
log "  /health/ready  -> $RECOVER_READY (expected 200)"
log "  chain height   : $BASELINE_BLOCKS -> $RECOVER_HEIGHT"
log "  chain integrity: $RECOVER_INTEGRITY (expected True)"

# Verdict
VERDICT="UNKNOWN"
if [ "$LIVE" = "200" ] && [ "$READY" = "503" ] && [ "$RECOVER_READY" = "200" ] && [ "$RECOVER_INTEGRITY" = "True" ]; then
  VERDICT="PASS"
elif [ "$RECOVER_INTEGRITY" != "True" ]; then
  VERDICT="FAIL - chain integrity broken after recovery"
else
  VERDICT="PARTIAL - live=$LIVE ready=$READY recover=$RECOVER_READY"
fi
log "  ==> VERDICT: $VERDICT"
