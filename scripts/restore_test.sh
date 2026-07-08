#!/usr/bin/env bash
# FREKCORE Restore Test — verifie qu'une sauvegarde est reellement restaurable
#
# Utilisation :
#   /app/scripts/restore_test.sh /app/backups/frekcore-XXX.tar.gz[.gpg]
#
# Restaure dans une DB temporaire, verifie les collections cles, PUIS supprime.
# Ne touche JAMAIS la DB de prod.

set -euo pipefail

ARCHIVE="${1:-}"
if [[ -z "$ARCHIVE" || ! -f "$ARCHIVE" ]]; then
  echo "Usage: $0 <backup-archive.tar.gz[.gpg]>" >&2
  exit 1
fi

MONGO_URL="$(grep '^MONGO_URL=' /app/backend/.env | cut -d= -f2- | tr -d '"')"
DB_NAME="$(grep '^DB_NAME=' /app/backend/.env | cut -d= -f2- | tr -d '"')"
RESTORE_DB="${DB_NAME}_restore_test_$(date -u +%s)"

TMP="$(mktemp -d)"
trap "rm -rf $TMP; mongosh --quiet '${MONGO_URL}' --eval 'db.getSiblingDB(\"${RESTORE_DB}\").dropDatabase()' 2>/dev/null || true" EXIT

# 1. Dechiffrer si .gpg
if [[ "$ARCHIVE" == *.gpg ]]; then
  if [[ -z "${BACKUP_GPG_PASSPHRASE:-}" ]]; then
    echo "ERROR: BACKUP_GPG_PASSPHRASE requis pour dechiffrer" >&2
    exit 2
  fi
  echo "[restore-test] Decrypting..."
  gpg --batch --yes --passphrase "$BACKUP_GPG_PASSPHRASE" \
      -o "$TMP/backup.tar.gz" -d "$ARCHIVE"
  TARBALL="$TMP/backup.tar.gz"
else
  TARBALL="$ARCHIVE"
fi

# 2. Extraire
echo "[restore-test] Extracting..."
tar -xzf "$TARBALL" -C "$TMP"
DUMP_DIR="$(find "$TMP" -maxdepth 2 -type d -name mongo | head -1)"
[[ -d "$DUMP_DIR" ]] || { echo "ERROR: mongo/ dump not found in archive" >&2; exit 3; }

# 3. Verifier cle Ed25519 presente
KEY_BAK="$(find "$TMP" -maxdepth 2 -name passport_key.pem | head -1)"
if [[ -f "$KEY_BAK" ]]; then
  KEY_HASH_BAK="$(sha256sum "$KEY_BAK" | awk '{print $1}')"
  KEY_HASH_LIVE="$(sha256sum /app/backend/.passport_key.pem | awk '{print $1}')"
  if [[ "$KEY_HASH_BAK" == "$KEY_HASH_LIVE" ]]; then
    echo "[restore-test] Ed25519 key: MATCH (sha256=$KEY_HASH_BAK)"
  else
    echo "[restore-test] Ed25519 key: DIFFERS (bak=$KEY_HASH_BAK live=$KEY_HASH_LIVE) — normal si key rotated"
  fi
else
  echo "[restore-test] WARN: no passport_key.pem in archive" >&2
fi

# 4. Restaurer dans DB temporaire
echo "[restore-test] Restoring to $RESTORE_DB..."
mongorestore \
  --uri="$MONGO_URL" \
  --nsFrom="${DB_NAME}.*" \
  --nsTo="${RESTORE_DB}.*" \
  --dir="$DUMP_DIR" \
  --quiet

# 5. Verifier collections critiques
CRITICAL_COLLECTIONS=(frek_identities frek_stages notary_blocks frek_clients)
FAILED=0
for coll in "${CRITICAL_COLLECTIONS[@]}"; do
  COUNT=$(mongosh --quiet "$MONGO_URL" --eval "db.getSiblingDB('${RESTORE_DB}').${coll}.countDocuments({})" 2>/dev/null || echo "ERR")
  echo "[restore-test] ${coll}: ${COUNT} docs"
  if [[ "$COUNT" == "ERR" || "$COUNT" == "0" ]]; then
    [[ "$coll" == "frek_identities" || "$coll" == "notary_blocks" ]] && FAILED=1
  fi
done

if [[ $FAILED -eq 1 ]]; then
  echo "[restore-test] FAIL: critical collection missing/empty"
  exit 4
fi

echo "[restore-test] OK — backup is restorable."
