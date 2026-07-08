# FREKCORE — Runbook Operationnel (RC v1.0 Sprint A+B)

## Statut Semaine 1 — Vital sécurité ✅

- [x] Backup Mongo automatique (script + scheduler daemon)
- [x] Backup clé Ed25519 (avec vérification sha256)
- [x] Chiffrement GPG symétrique AES256
- [x] Restore-test end-to-end validé
- [x] Health checks profonds (`/health/live`, `/ready`, `/deep`)
- [x] Admin backup API (trigger, status, restore-test)

---

## 1. Backups — Où / Quand / Comment

### Emplacement
- **Répertoire** : `/app/backups/`
- **Format** : `frekcore-YYYY-MM-DDThh-mm-ssZ.tar.gz[.gpg]`
- **Rétention** : 30 jours (configurable via `BACKUP_RETENTION_DAYS`)

### Fréquence automatique
Daemon supervisor `frek_backup` — 03:00 UTC quotidien.

```bash
# Voir status
sudo supervisorctl status frek_backup

# Log
tail -f /var/log/supervisor/frek_backup.out.log
```

### Chiffrement GPG (RECOMMANDÉ prod)
Poser dans supervisor config `/etc/supervisor/conf.d/frek_backup.conf` :

```ini
environment=BACKUP_GPG_PASSPHRASE="ta-passphrase-tres-longue",FREK_BACKUP_HOUR_UTC="3"
```

Puis :
```bash
sudo supervisorctl restart frek_backup
```

**⚠️ Sans passphrase = archive en clair. En prod obligatoire.**

### Backup manuel
```bash
BACKUP_GPG_PASSPHRASE="xxx" /app/scripts/backup_frekcore.sh
```

### Via API (admin)
```bash
ADMIN_KEY=$(grep '^SECRET_KEY=' /app/backend/.env | cut -d= -f2)
curl -X POST "$API_URL/api/v1/admin/backup/trigger?gpg_passphrase=xxx" \
  -H "X-Admin-Key: $ADMIN_KEY"
```

---

## 2. Restauration

### Test qu'un backup est restaurable (safe, DB temporaire)
```bash
BACKUP_GPG_PASSPHRASE="xxx" \
  /app/scripts/restore_test.sh /app/backups/frekcore-XXXX.tar.gz.gpg
```

Ou via API :
```bash
curl -X POST "$API/api/v1/admin/backup/restore-test/<archive>?gpg_passphrase=xxx" \
  -H "X-Admin-Key: $ADMIN_KEY"
```

### Restauration réelle (procédure d'urgence)
```bash
# 1. Dechiffrer si .gpg
gpg --batch --yes --passphrase "xxx" -o backup.tar.gz -d frekcore-XXX.tar.gz.gpg

# 2. Extraire
tar -xzf backup.tar.gz

# 3. Restaurer clé Ed25519 EN PREMIER (critique !)
cp frekcore-XXX/passport_key.pem /app/backend/.passport_key.pem
chmod 600 /app/backend/.passport_key.pem

# 4. Restaurer Mongo
mongorestore --uri="$MONGO_URL" --drop --dir=frekcore-XXX/mongo

# 5. Restart backend
sudo supervisorctl restart backend
```

---

## 3. Health Monitoring

### Endpoints publics
| Endpoint | Usage |
|---|---|
| `GET /api/v1/health/live` | Liveness — repond toujours |
| `GET /api/v1/health/ready` | Readiness — verifie Mongo |
| `GET /api/v1/health/deep` | Deep check (Mongo, Ed25519, disk, memory, notary chain, last backup) |

### Monitoring externe recommandé (gratuit)
1. **UptimeRobot** (uptimerobot.com) :
   - Monitor 1 : `GET /api/v1/health/live` toutes les 5 min
   - Monitor 2 : `GET /api/v1/health/ready` toutes les 5 min
   - Alertes email + push mobile
   
2. **Better Stack (Logtail)** — logs + uptime combinés

3. **cronjob.org** (backup) :
   - Ping `/api/v1/health/deep` toutes les heures
   - Alerte si `status != "healthy"`

---

## 4. Clé Ed25519 — La règle d'or

**Fichier** : `/app/backend/.passport_key.pem` (119 bytes, mode 0o600)  
**SHA-256 actuel** : `496a69437acd86d5dcc42f79c59fa951786c47ad8fb84e21b9028fd28f6e9088`

⚠️ Si cette clé disparaît, **tous les passeports Ed25519 émis deviennent non-régénérables**. Toute nouvelle clé casse la continuité de confiance.

### Vérification quotidienne
```bash
curl "$API/api/v1/health/deep" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['checks']['ed25519_key'])"
```

### Backup manuel hors-site (recommandé)
```bash
# Copie sur un support isole (USB chiffre, cle Yubikey, cloud avec 2FA)
gpg --symmetric --cipher-algo AES256 /app/backend/.passport_key.pem
# Puis copier .passport_key.pem.gpg sur un support hors du serveur
```

---

## 5. Alertes critiques à surveiller

| Signal | Cause probable | Action |
|---|---|---|
| `/health/live` HTTP != 200 | Backend crash | supervisor auto-restart, vérif logs |
| `/health/ready` HTTP != 200 | Mongo down | `sudo supervisorctl status mongodb` |
| `/health/deep.status == degraded` | Backup manquant, disk plein, clé absente | voir `checks` |
| `ed25519_key.ok == false` | Clé absente ! | RESTAURATION URGENTE depuis backup |
| `disk.used_pct > 85` | Disque saturé | purge `/app/backups/frekcore-*` anciens |
| `notary_chain.ok == false` | Corruption chaîne | vérification integrite complète |

---

## 6. Checklist RC v1.0 (issue user)

- [x] **Backup automatique quotidien** (Sprint A)
- [x] **Backup Ed25519** (Sprint A)
- [x] **Health checks profonds** (Sprint B)
- [x] **Restore testé** (Sprint A)
- [ ] Monitoring externe configuré (UptimeRobot — action user)
- [ ] Alertes email actives (action user)
- [ ] Sentry configuré (Sprint B optionnel)
- [ ] Audit souveraineté complet (Sprint D+E)
- [ ] Load test (Sprint F)
- [ ] Test résilience (Sprint G)
- [ ] Dry-run terrain (Sprint H)
