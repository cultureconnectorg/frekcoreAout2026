#!/usr/bin/env bash
# FREKCORE Backup Script — Souverainete des donnees
#
# Sauvegarde :
#  1. MongoDB complete (mongodump)
#  2. Cle Ed25519 (.passport_key.pem) — SEULE cle qui signe TOUT
#  3. Fichiers .env (sans les inclure dans git)
#
# Sortie chiffree GPG (symetrique) si BACKUP_GPG_PASSPHRASE defini.
#
# Utilisation :
#   /app/scripts/backup_frekcore.sh                    # dump local /app/backups/
#   BACKUP_DEST=/mnt/nfs /app/scripts/backup_frekcore.sh
#   BACKUP_GPG_PASSPHRASE="xxxx" /app/scripts/backup_frekcore.sh
#
# Cron recommande (03:00 UTC quotidien) :
#   0 3 * * * BACKUP_GPG_PASSPHRASE="xxxx" /app/scripts/backup_frekcore.sh >> /var/log/frek-backup.log 2>&1

set -euo pipefail

# --- Config ---
BACKUP_DEST="${BACKUP_DEST:-/app/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
STAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
WORK="${BACKUP_DEST}/frekcore-${STAMP}"

MONGO_URL="$(grep '^MONGO_URL=' /app/backend/.env | cut -d= -f2- | tr -d '"')"
DB_NAME="$(grep '^DB_NAME=' /app/backend/.env | cut -d= -f2- | tr -d '"')"
KEY_PATH="/app/backend/.passport_key.pem"

mkdir -p "$WORK"

# --- 1. MongoDB dump ---
echo "[$(date -u +%FT%TZ)] MongoDB dump $DB_NAME -> $WORK/mongo/"
mongodump \
  --uri="$MONGO_URL" \
  --db="$DB_NAME" \
  --out="$WORK/mongo" \
  --quiet

# --- 2. Cle Ed25519 (critique !) ---
if [[ -f "$KEY_PATH" ]]; then
  cp -p "$KEY_PATH" "$WORK/passport_key.pem"
  # Empreinte pour audit (hash SHA-256 de la cle)
  sha256sum "$KEY_PATH" > "$WORK/passport_key.sha256"
  echo "[$(date -u +%FT%TZ)] Ed25519 key backed up (sha256: $(cat "$WORK/passport_key.sha256" | awk '{print $1}'))"
else
  echo "[$(date -u +%FT%TZ)] WARN: no passport_key.pem found" >&2
fi

# --- 3. .env (sans commit dans git) ---
cp -p /app/backend/.env "$WORK/backend.env" 2>/dev/null || true
cp -p /app/frontend/.env "$WORK/frontend.env" 2>/dev/null || true

# --- 4. Manifest ---
cat > "$WORK/MANIFEST.json" <<EOF
{
  "created_at": "${STAMP}",
  "db_name": "${DB_NAME}",
  "hostname": "$(hostname)",
  "frek_version": "1.0.0-rc",
  "components": {
    "mongo_dump": "mongo/",
    "ed25519_key": "passport_key.pem",
    "backend_env": "backend.env",
    "frontend_env": "frontend.env"
  }
}
EOF

# --- 5. Archive ---
ARCHIVE="${BACKUP_DEST}/frekcore-${STAMP}.tar.gz"
tar -czf "$ARCHIVE" -C "$BACKUP_DEST" "frekcore-${STAMP}"
rm -rf "$WORK"

# --- 6. Chiffrement GPG OBLIGATOIRE ---
# Doctrine RC v1.0 : aucune archive en clair ne quitte le systeme.
if [[ -z "${BACKUP_GPG_PASSPHRASE:-}" ]]; then
  # Fallback : lecture depuis fichier root-only
  if [[ -f /root/.frekcore/backup_passphrase ]]; then
    BACKUP_GPG_PASSPHRASE="$(cat /root/.frekcore/backup_passphrase)"
  fi
fi
if [[ -z "${BACKUP_GPG_PASSPHRASE:-}" ]]; then
  echo "[FATAL] BACKUP_GPG_PASSPHRASE requis. Doctrine RC v1.0 : chiffrement obligatoire." >&2
  rm -f "$ARCHIVE"
  exit 10
fi

echo "[$(date -u +%FT%TZ)] Encrypting with GPG AES256..."
gpg --batch --yes --passphrase "$BACKUP_GPG_PASSPHRASE" \
    --symmetric --cipher-algo AES256 \
    -o "${ARCHIVE}.gpg" "$ARCHIVE"
rm -f "$ARCHIVE"
ARCHIVE="${ARCHIVE}.gpg"

# --- 7. Retention (purge > RETENTION_DAYS) ---
find "$BACKUP_DEST" -maxdepth 1 -name 'frekcore-*.tar.gz*' -type f \
    -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true

SIZE="$(du -h "$ARCHIVE" | awk '{print $1}')"
echo "[$(date -u +%FT%TZ)] BACKUP OK: ${ARCHIVE} (${SIZE})"

# --- 8. Ecrit metadata pour endpoint /admin/backup/status ---
mkdir -p /app/backups
if [[ -n "${BACKUP_GPG_PASSPHRASE:-}" ]]; then
  ENC_JSON="true"
else
  # Chiffrement obligatoire — si on arrive ici, c'est qu'on a lu depuis /root/.frekcore/
  ENC_JSON="true"
fi
cat > /app/backups/.last_backup.json <<EOF
{
  "at": "${STAMP}",
  "archive": "${ARCHIVE}",
  "size": "${SIZE}",
  "encrypted": ${ENC_JSON},
  "db_name": "${DB_NAME}",
  "retention_days": ${RETENTION_DAYS}
}
EOF

echo "[$(date -u +%FT%TZ)] Done."
