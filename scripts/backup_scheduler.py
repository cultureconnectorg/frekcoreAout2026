#!/usr/bin/env python3
"""
FREK Backup Scheduler — daemon leger qui declenche backup_frekcore.sh
tous les jours a 03:00 UTC (configurable).

Manage par supervisor : redemarre auto si crash.
Log : /var/log/supervisor/frek_backup.*.log
"""
import os
import time
import subprocess
from datetime import datetime, timezone, timedelta

BACKUP_SCRIPT = "/app/scripts/backup_frekcore.sh"
BACKUP_HOUR_UTC = int(os.environ.get("FREK_BACKUP_HOUR_UTC", "3"))
BACKUP_MINUTE = int(os.environ.get("FREK_BACKUP_MINUTE", "0"))
PASSPHRASE_FILE = os.environ.get("BACKUP_PASSPHRASE_FILE", "/root/.frekcore/backup_passphrase")

# Lecture passphrase depuis fichier root-only (doctrine RC v1.0)
GPG_PASS = os.environ.get("BACKUP_GPG_PASSPHRASE", "")
if not GPG_PASS and os.path.exists(PASSPHRASE_FILE):
    try:
        with open(PASSPHRASE_FILE) as f:
            GPG_PASS = f.read().strip()
    except Exception:
        pass


def next_run() -> datetime:
    now = datetime.now(timezone.utc)
    target = now.replace(hour=BACKUP_HOUR_UTC, minute=BACKUP_MINUTE, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def run_backup():
    env = os.environ.copy()
    if GPG_PASS:
        env["BACKUP_GPG_PASSPHRASE"] = GPG_PASS
    try:
        result = subprocess.run(
            [BACKUP_SCRIPT],
            capture_output=True, text=True, timeout=600, env=env,
        )
        if result.returncode == 0:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Backup OK", flush=True)
            print(result.stdout[-500:], flush=True)
        else:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Backup FAILED code={result.returncode}", flush=True)
            print(result.stderr[-500:], flush=True)
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).isoformat()}] Backup EXCEPTION: {e}", flush=True)


def main():
    print(f"[frek-backup-scheduler] Started. Backup at {BACKUP_HOUR_UTC:02d}:{BACKUP_MINUTE:02d} UTC daily. GPG={'yes' if GPG_PASS else 'no'}", flush=True)
    while True:
        nxt = next_run()
        wait_s = max(1, int((nxt - datetime.now(timezone.utc)).total_seconds()))
        print(f"[frek-backup-scheduler] Next run at {nxt.isoformat()} (in {wait_s}s)", flush=True)
        time.sleep(wait_s)
        run_backup()


if __name__ == "__main__":
    main()
