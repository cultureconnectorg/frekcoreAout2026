"""
FREK Health & Ops routes
"""
import os
import hmac
import json
import shutil
import asyncio
import subprocess
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Header

logger = logging.getLogger("frek.health")

health_router = APIRouter(prefix="/health", tags=["FREK Health"])
admin_ops_router = APIRouter(prefix="/admin", tags=["FREK Admin Ops"])

db = None
_START_TIME = datetime.now(timezone.utc)
ADMIN_KEY = os.environ.get("SECRET_KEY", "")
BACKUP_DIR = Path("/app/backups")
BACKUP_SCRIPT = Path("/app/scripts/backup_frekcore.sh")
KEY_PATH = Path("/app/backend/.passport_key.pem")


def set_db(database):
    global db
    db = database


def _require_admin(x_admin_key: Optional[str]):
    if not ADMIN_KEY or not x_admin_key or not hmac.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(401, "X-Admin-Key requis")


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Health ----------
@health_router.get("/live")
async def liveness():
    """K8s liveness probe — repond toujours si le process tourne."""
    return {"status": "alive", "at": _iso()}


@health_router.get("/ready")
async def readiness():
    """K8s readiness probe — verifie Mongo repond."""
    try:
        await db.command("ping")
        return {"status": "ready", "mongo": "ok", "at": _iso()}
    except Exception as e:
        raise HTTPException(503, f"not ready: {e}")


@health_router.get("/deep")
async def deep_health():
    """Sante complete : Mongo, Ed25519, disk, memory, notary chain, latest backup.

    Retourne toujours HTTP 200 (meme si degrade) avec le detail dans checks.
    Le champ 'status' agrege : 'healthy' | 'degraded'. Un monitor externe doit
    lire ce champ et non le code HTTP.
    """
    import asyncio
    checks: dict = {"at": _iso(), "checks": {}}

    # 1. Mongo — timeout court pour ne pas hanger le health check
    try:
        # Wrap dans wait_for pour garantir un timeout dur en 3s max
        async def _mongo_probe():
            await db.command("ping")
            n_frek = await db.frek_identities.count_documents({})
            n_blocks = await db.notary_blocks.count_documents({})
            return n_frek, n_blocks

        n_frek, n_blocks = await asyncio.wait_for(_mongo_probe(), timeout=3.0)
        checks["checks"]["mongo"] = {
            "ok": True,
            "frek_identities": n_frek,
            "notary_blocks": n_blocks,
        }
    except asyncio.TimeoutError:
        checks["checks"]["mongo"] = {"ok": False, "error": "timeout (>3s) — Mongo probablement down"}
    except Exception as e:
        checks["checks"]["mongo"] = {"ok": False, "error": str(e)[:200]}

    # 2. Cle Ed25519 (critique !)
    try:
        if not KEY_PATH.exists():
            checks["checks"]["ed25519_key"] = {"ok": False, "error": "key file missing"}
        else:
            import hashlib
            with open(KEY_PATH, "rb") as f:
                key_bytes = f.read()
            key_hash = hashlib.sha256(key_bytes).hexdigest()
            st = KEY_PATH.stat()
            checks["checks"]["ed25519_key"] = {
                "ok": True,
                "sha256": key_hash,
                "size_bytes": st.st_size,
                "mode_octal": oct(st.st_mode & 0o777),
                "mode_secure": (st.st_mode & 0o077) == 0,  # not readable by group/other
            }
    except Exception as e:
        checks["checks"]["ed25519_key"] = {"ok": False, "error": str(e)}

    # 3. Disk
    try:
        du = shutil.disk_usage("/app")
        checks["checks"]["disk"] = {
            "ok": du.free > 500 * 1024 * 1024,  # > 500MB free
            "total_gb": round(du.total / 1e9, 2),
            "free_gb": round(du.free / 1e9, 2),
            "used_pct": round(du.used * 100 / du.total, 1),
        }
    except Exception as e:
        checks["checks"]["disk"] = {"ok": False, "error": str(e)}

    # 4. Memory
    try:
        import resource
        # Peak RSS in KB on Linux
        rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        checks["checks"]["memory"] = {"ok": True, "peak_rss_mb": round(rss_kb / 1024, 1)}
    except Exception as e:
        checks["checks"]["memory"] = {"ok": False, "error": str(e)}

    # 5. Notary chain integrity (light check : last block prev_hash chain)
    try:
        async def _chain_probe():
            last3 = await db.notary_blocks.find({}, {"_id": 0, "height": 1, "prev_hash": 1, "block_hash": 1}) \
                .sort("height", -1).limit(3).to_list(3)
            chain_ok = True
            for i in range(len(last3) - 1):
                if last3[i]["prev_hash"] != last3[i + 1]["block_hash"]:
                    chain_ok = False
                    break
            return chain_ok, last3[0]["height"] if last3 else 0

        chain_ok, last_height = await asyncio.wait_for(_chain_probe(), timeout=3.0)
        checks["checks"]["notary_chain"] = {
            "ok": chain_ok,
            "last_height": last_height,
        }
    except asyncio.TimeoutError:
        checks["checks"]["notary_chain"] = {"ok": False, "error": "timeout probing chain"}
    except Exception as e:
        checks["checks"]["notary_chain"] = {"ok": False, "error": str(e)}

    # 6. Last backup
    try:
        marker = BACKUP_DIR / ".last_backup.json"
        if marker.exists():
            data = json.loads(marker.read_text())
            checks["checks"]["last_backup"] = {
                "ok": True,
                "at": data.get("at"),
                "size": data.get("size"),
                "encrypted": data.get("encrypted"),
            }
        else:
            checks["checks"]["last_backup"] = {"ok": False, "error": "no backup yet"}
    except Exception as e:
        checks["checks"]["last_backup"] = {"ok": False, "error": str(e)}

    # 7. Uptime
    uptime_s = (datetime.now(timezone.utc) - _START_TIME).total_seconds()
    checks["uptime_seconds"] = int(uptime_s)
    checks["uptime_human"] = f"{int(uptime_s // 3600)}h{int((uptime_s % 3600) // 60)}m"

    # Overall
    all_ok = all(v.get("ok", False) for v in checks["checks"].values())
    checks["status"] = "healthy" if all_ok else "degraded"
    return checks


# ---------- Admin backup ops ----------
@admin_ops_router.get("/backup/status")
async def backup_status(x_admin_key: Optional[str] = Header(None)):
    _require_admin(x_admin_key)
    marker = BACKUP_DIR / ".last_backup.json"
    last: Optional[dict] = None
    if marker.exists():
        try:
            last = json.loads(marker.read_text())
        except Exception:
            last = None

    archives = []
    if BACKUP_DIR.exists():
        for p in sorted(BACKUP_DIR.glob("frekcore-*.tar.gz*"), reverse=True)[:20]:
            st = p.stat()
            archives.append({
                "name": p.name,
                "size_bytes": st.st_size,
                "size_mb": round(st.st_size / 1e6, 2),
                "encrypted": p.suffix == ".gpg",
                "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            })

    return {
        "backup_dir": str(BACKUP_DIR),
        "script_present": BACKUP_SCRIPT.exists(),
        "archives_count": len(archives),
        "last": last,
        "archives": archives,
    }


@admin_ops_router.post("/backup/trigger")
async def backup_trigger(
    gpg_passphrase: Optional[str] = None,
    x_admin_key: Optional[str] = Header(None),
):
    """Declenche un backup immediat.
    Si gpg_passphrase fourni, chiffre l'archive.
    """
    _require_admin(x_admin_key)
    if not BACKUP_SCRIPT.exists():
        raise HTTPException(500, "backup script missing")

    env = os.environ.copy()
    if gpg_passphrase:
        env["BACKUP_GPG_PASSPHRASE"] = gpg_passphrase

    def _run():
        return subprocess.run(
            [str(BACKUP_SCRIPT)],
            capture_output=True, text=True, timeout=300, env=env,
        )

    proc = await asyncio.to_thread(_run)
    if proc.returncode != 0:
        logger.error(f"Backup failed: {proc.stderr[-500:]}")
        raise HTTPException(500, f"backup failed: {proc.stderr[-300:]}")

    marker = BACKUP_DIR / ".last_backup.json"
    last = json.loads(marker.read_text()) if marker.exists() else None
    return {"ok": True, "last": last, "stdout_tail": proc.stdout[-500:]}


@admin_ops_router.post("/backup/restore-test/{archive_name}")
async def backup_restore_test(
    archive_name: str,
    gpg_passphrase: Optional[str] = None,
    x_admin_key: Optional[str] = Header(None),
):
    """Verifie qu'une archive donnee est reellement restaurable (dans une DB temporaire, auto-nettoyee)."""
    _require_admin(x_admin_key)
    # Sanitize
    if "/" in archive_name or ".." in archive_name:
        raise HTTPException(400, "invalid archive name")
    archive = BACKUP_DIR / archive_name
    if not archive.exists():
        raise HTTPException(404, "archive not found")

    script = Path("/app/scripts/restore_test.sh")
    if not script.exists():
        raise HTTPException(500, "restore script missing")

    env = os.environ.copy()
    if gpg_passphrase:
        env["BACKUP_GPG_PASSPHRASE"] = gpg_passphrase

    def _run():
        return subprocess.run(
            [str(script), str(archive)],
            capture_output=True, text=True, timeout=180, env=env,
        )

    proc = await asyncio.to_thread(_run)
    ok = proc.returncode == 0
    return {
        "ok": ok,
        "archive": archive_name,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-1500:],
        "stderr": proc.stderr[-800:],
    }
