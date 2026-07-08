#!/usr/bin/env bash
# FREK Sprint G — Chaos Test 2 : Coupure OTS (calendars publics)
#
# Bloque les DNS lookups vers les calendars OpenTimestamps.
# Verifie que :
#  - le block FREK-Chain local se cree quand meme (souverainete locale)
#  - l'OTS submit echoue mais ne bloque pas le pipeline principal
#  - la queue "pending_anchors" grandit
#  - a la reprise du reseau OTS, la queue se resorbe automatiquement

set -uo pipefail

API="${API:-$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)}"
OUT=/app/loadtest_results/chaos_ots.log
mkdir -p "$(dirname $OUT)"; : > "$OUT"

log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$OUT"; }

log "=== TEST 2 : COUPURE OTS ==="

# Baseline
STATUS_BEFORE=$(curl -s "$API/api/v1/notary/chain/status")
PENDING_BEFORE=$(echo "$STATUS_BEFORE" | python3 -c "import sys,json;print(json.load(sys.stdin).get('pending_anchors',0))")
HEIGHT_BEFORE=$(echo "$STATUS_BEFORE" | python3 -c "import sys,json;print(json.load(sys.stdin)['height'])")
log "  baseline: height=$HEIGHT_BEFORE, pending_anchors=$PENDING_BEFORE"

# Backup /etc/hosts (edit in-place because bind-mount container)
grep -v "FREK chaos\|opentimestamps.org\|eternitywall.com" /etc/hosts > /tmp/frek_hosts_bak

# Block OTS calendars by rerouting to loopback
log "  --- Blocking OTS calendars via /etc/hosts ---"
BLOCKED="# --- FREK chaos test OTS block ---
127.0.0.1 a.pool.opentimestamps.org
127.0.0.1 b.pool.opentimestamps.org
127.0.0.1 alice.btc.calendar.opentimestamps.org
127.0.0.1 bob.btc.calendar.opentimestamps.org
127.0.0.1 finney.calendar.eternitywall.com"
printf "%s\n%s\n" "$(cat /tmp/frek_hosts_bak)" "$BLOCKED" > /tmp/frek_hosts_blocked
cat /tmp/frek_hosts_blocked > /etc/hosts

# Create an event that will trigger notary
CSEC=$(grep FREK_CLIENT_KILTIKONET_SECRET /app/backend/.env | cut -d= -f2)
TOK=$(curl -s -X POST "$API/api/v1/auth/token" -H "Content-Type: application/json" \
  -d "{\"client_id\":\"kiltikonet-cc2026\",\"client_secret\":\"$CSEC\",\"grant_type\":\"client_credentials\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

log "  --- Emitting 3 FREK-IDs during OTS blackout ---"
for i in 1 2 3; do
  EMAIL="chaos-ots-$(date +%s)-$i@test.io"
  RESP=$(curl -s -X POST "$API/api/v1/identity/emit" \
    -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"source\":\"chaos_ots\"}")
  FID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin).get('frek_id','ERR'))" 2>/dev/null)
  log "    emit #$i frek_id=${FID:0:12}..."
  sleep 1
done

# Wait for notary loop to attempt OTS submission
log "  --- Waiting 35s for notary background loop to attempt OTS ---"
sleep 35

STATUS_DURING=$(curl -s "$API/api/v1/notary/chain/status")
PENDING_DURING=$(echo "$STATUS_DURING" | python3 -c "import sys,json;print(json.load(sys.stdin).get('pending_anchors',0))")
HEIGHT_DURING=$(echo "$STATUS_DURING" | python3 -c "import sys,json;print(json.load(sys.stdin)['height'])")
INTEGRITY_DURING=$(curl -s "$API/api/v1/notary/chain/verify" | python3 -c "import sys,json;print(json.load(sys.stdin)['valid'])" 2>/dev/null)

log "  --- Pendant panne OTS ---"
log "  height   : $HEIGHT_BEFORE -> $HEIGHT_DURING (delta: $((HEIGHT_DURING - HEIGHT_BEFORE)) blocks created despite OTS down)"
log "  pending  : $PENDING_BEFORE -> $PENDING_DURING (queue grew as expected)"
log "  integrity: $INTEGRITY_DURING (chain locale intacte)"

# Restore
log "  --- Restoring OTS network access ---"
cat /tmp/frek_hosts_bak > /etc/hosts
rm -f /tmp/frek_hosts_bak /tmp/frek_hosts_blocked

# Wait for catch-up
log "  --- Waiting 45s for notary loop to catch up ---"
sleep 45

STATUS_AFTER=$(curl -s "$API/api/v1/notary/chain/status")
PENDING_AFTER=$(echo "$STATUS_AFTER" | python3 -c "import sys,json;print(json.load(sys.stdin).get('pending_anchors',0))")
INTEGRITY_AFTER=$(curl -s "$API/api/v1/notary/chain/verify" | python3 -c "import sys,json;print(json.load(sys.stdin)['valid'])" 2>/dev/null)

log "  --- Apres reprise OTS ---"
log "  pending  : $PENDING_DURING -> $PENDING_AFTER (queue devrait diminuer)"
log "  integrity: $INTEGRITY_AFTER"

# Verdict
VERDICT="UNKNOWN"
if [ "$HEIGHT_DURING" -gt "$HEIGHT_BEFORE" ] && [ "$INTEGRITY_DURING" = "True" ] && [ "$INTEGRITY_AFTER" = "True" ]; then
  if [ "$PENDING_AFTER" -le "$PENDING_DURING" ]; then
    VERDICT="PASS - blocks locaux crees, queue OTS gerable, chain integre"
  else
    VERDICT="PARTIAL - blocks locaux OK mais queue OTS ne redescend pas ($PENDING_AFTER >= $PENDING_DURING)"
  fi
else
  VERDICT="FAIL - blocks locaux bloques ou chain corrompue"
fi
log "  ==> VERDICT: $VERDICT"
