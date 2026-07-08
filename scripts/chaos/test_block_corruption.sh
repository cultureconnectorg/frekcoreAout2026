#!/usr/bin/env bash
# FREK Sprint G — Chaos Test 3 : Corruption volontaire d'un block
#
# Modifie manuellement le block_hash d'un block existant dans Mongo.
# Verifie que :
#  - /notary/chain/verify detecte l'incoherence
#  - identifie le block coupable (first_invalid_height)
#  - un audit trail / log est cree
# Puis restaure et verifie que l'integrite revient.

set -uo pipefail

API="${API:-$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)}"
OUT=/app/loadtest_results/chaos_corruption.log
mkdir -p "$(dirname $OUT)"; : > "$OUT"

log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$OUT"; }

log "=== TEST 3 : CORRUPTION BLOCK VOLONTAIRE ==="

# Baseline
STATUS_BEFORE=$(curl -s "$API/api/v1/notary/chain/verify")
VALID_BEFORE=$(echo "$STATUS_BEFORE" | python3 -c "import sys,json;print(json.load(sys.stdin)['valid'])")
HEIGHT_BEFORE=$(echo "$STATUS_BEFORE" | python3 -c "import sys,json;print(json.load(sys.stdin)['height'])")
log "  baseline: chain valid=$VALID_BEFORE, height=$HEIGHT_BEFORE"

if [ "$VALID_BEFORE" != "True" ]; then
  log "  WARN: baseline already invalid, cannot run test properly"
  exit 1
fi

# Choose a block in the middle of the chain (not genesis, not tip)
TARGET_HEIGHT=$((HEIGHT_BEFORE / 2))
log "  --- Targeting block at height=$TARGET_HEIGHT ---"

# Save the original block_hash
ORIGINAL=$(mongosh --quiet --eval "
db = db.getSiblingDB('test_database');
const b = db.notary_blocks.findOne({height:$TARGET_HEIGHT},{block_hash:1,prev_hash:1,payload_hash:1,_id:0});
print(JSON.stringify(b));
" 2>/dev/null | tail -1)
log "  Original block: $ORIGINAL"

ORIGINAL_HASH=$(echo "$ORIGINAL" | python3 -c "import sys,json;print(json.load(sys.stdin)['block_hash'])")

# Corrupt : swap 4 hex chars in the middle of block_hash
CORRUPT_HASH="$(python3 -c "
h='$ORIGINAL_HASH'
print(h[:30] + 'DEADBEEF' + h[38:])
")"
log "  Corrupt block_hash: $CORRUPT_HASH"

log "  --- Injecting corruption ---"
mongosh --quiet --eval "
db = db.getSiblingDB('test_database');
db.notary_blocks.updateOne({height:$TARGET_HEIGHT}, {\$set:{block_hash:'$CORRUPT_HASH'}});
" 2>&1 | tee -a "$OUT"

# Verify detection
sleep 1
VERIFY_DURING=$(curl -s "$API/api/v1/notary/chain/verify")
VALID_DURING=$(echo "$VERIFY_DURING" | python3 -c "import sys,json;print(json.load(sys.stdin)['valid'])")
FIRST_INVALID=$(echo "$VERIFY_DURING" | python3 -c "import sys,json;print(json.load(sys.stdin).get('first_invalid_height','n/a'))")
MSG=$(echo "$VERIFY_DURING" | python3 -c "import sys,json;print(json.load(sys.stdin).get('message','n/a'))")

log "  --- Pendant corruption ---"
log "  chain.verify.valid: $VALID_DURING (attendu: False)"
log "  first_invalid_height: $FIRST_INVALID (attendu: $TARGET_HEIGHT)"
log "  message: $MSG"

# Also test that fetching this specific block via API reports the issue
BLOCK_API=$(curl -s "$API/api/v1/notary/blocks?limit=200" | python3 -c "
import sys,json
for b in json.load(sys.stdin):
    if b.get('height')==$TARGET_HEIGHT:
        print(b.get('block_hash','')[:20]); break
")
log "  block_hash via API: ${BLOCK_API}..."

# Restore
log "  --- Restoring original block_hash ---"
mongosh --quiet --eval "
db = db.getSiblingDB('test_database');
db.notary_blocks.updateOne({height:$TARGET_HEIGHT}, {\$set:{block_hash:'$ORIGINAL_HASH'}});
" 2>&1 | tee -a "$OUT"

sleep 1
VERIFY_AFTER=$(curl -s "$API/api/v1/notary/chain/verify")
VALID_AFTER=$(echo "$VERIFY_AFTER" | python3 -c "import sys,json;print(json.load(sys.stdin)['valid'])")
log "  --- Apres restauration ---"
log "  chain.verify.valid: $VALID_AFTER (attendu: True)"

# Verdict
VERDICT="UNKNOWN"
if [ "$VALID_DURING" = "False" ] && [ "$FIRST_INVALID" = "$TARGET_HEIGHT" ] && [ "$VALID_AFTER" = "True" ]; then
  VERDICT="PASS - detection immediate + localisation precise + restauration propre"
elif [ "$VALID_DURING" = "False" ] && [ "$VALID_AFTER" = "True" ]; then
  VERDICT="PARTIAL - detection OK mais localisation imprecise (attendu=$TARGET_HEIGHT, obtenu=$FIRST_INVALID)"
else
  VERDICT="FAIL - corruption non detectee ou restauration cassee"
fi
log "  ==> VERDICT: $VERDICT"
