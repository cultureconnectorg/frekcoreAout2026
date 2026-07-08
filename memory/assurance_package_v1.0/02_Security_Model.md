# 02 — Security Model

**FREKCORE Assurance Package v1.0** — Document 02
**Version** : 1.0.0-rc
**Date** : 2026-07-08

---

## 1. Modèle de menaces (threat model)

### 1.1 Ce qu'on protège

| Actif | Sensibilité | Impact si compromis |
|---|---|---|
| **Clé Ed25519 racine** (`.passport_key.pem`) | 🔴 CRITIQUE | Toutes les signatures deviennent contrefaisables |
| **Intégrité FREK-Chain** | 🔴 CRITIQUE | Perte de crédibilité totale du "notariat" |
| **Backups GPG** | 🟠 HAUTE | Restauration impossible sans passphrase |
| **Client secrets** (Kiltikonet, CVL) | 🟠 HAUTE | Émissions frauduleuses au nom d'un partenaire |
| **PIN staff** | 🟡 MOYENNE | Scans frauduleux limités à la session |
| **Emails porteurs** | 🟢 BASSE | **Jamais stockés en clair** (uniquement sha256+salt) |

### 1.2 Ce dont on se protège

| Menace | Vecteur | Mitigation |
|---|---|---|
| Vol de la clé Ed25519 | Compromission serveur | Backup GPG chiffré hors serveur + doc de restauration |
| Émission frauduleuse | Client secret leaké | Rate limit (100/h) + rotation via `/admin/clients/{id}/rotate` |
| Brute force login staff | 100k tentatives sur PIN | bcrypt cost 12 + lockout 5 essais / 15 min |
| Corruption chain | Access DB direct | `chain_watchdog` (6h) + alerte `security_events` |
| DoS API | 10k RPS d'un même IP | Rate limit sliding window (300 req/min IP) |
| Fuite PII | Backend leak | **Zero PII en clair** — uniquement hash |
| MitM | Proxy hostile | HTTPS obligatoire (via ingress K8s) |
| Rejeu de scan | Même badge deux fois | Idempotence par `client_uuid` (24h TTL) |
| Injection Mongo | Payload malicieux | Pydantic + Motor safe params |
| Chain forgery | Falsification block | SHA-256 chaining + OpenTimestamps immutable + BTC anchor |

### 1.3 Hors périmètre

- Attaque physique sur le hardware serveur (responsabilité hébergeur).
- Compromission de l'hôte Kubernetes (responsabilité Emergent / hébergeur).
- Attaque sur la blockchain Bitcoin (hors périmètre absolu).
- Vol d'un smartphone d'un staff en session (mitigation UX : timeout auto, logout distant admin).

---

## 2. Contrôles cryptographiques

### 2.1 Signature Ed25519
- **Algorithme** : Ed25519 (RFC 8032), courbe Edwards25519
- **Clé privée** : générée à l'initialisation, stockée `/app/backend/.passport_key.pem` chmod 0600
- **Clé publique** : exposée sur 3 canaux (JWKS, DID, PEM)
- **Rotation** : possible mais impacte tous les passeports existants → jamais utilisée en v1.0

### 2.2 Hachage SHA-256
- Utilisé pour : Merkle root passport, chain link, hash email, canonical JCS
- Aucun MD5/SHA-1 nulle part

### 2.3 Bcrypt (staff auth)
- Cost 12 (~200 ms/hash sur 4 vCPU)
- ⚠️ Sprint F a révélé : login surge 100 simultanés = 20s file. Mitigation opérationnelle : onboarding T-30 min.

### 2.4 GPG AES256 (backups)
- Chiffrement symétrique via passphrase 32 bytes urlsafe
- Passphrase stockée `/root/.frekcore/backup_passphrase` chmod 0600
- Rotation manuelle : renouveler passphrase → chiffrer nouveaux backups → informer opérateurs

### 2.5 JCS + Multibase (VC)
- Canonicalization RFC 8785 → hash déterministe
- Multicodec ed25519-pub (0xed01) + multibase base58btc

---

## 3. Contrôles d'accès

### 3.1 OAuth2 Client Credentials
- Flow : `POST /api/v1/auth/token` avec `client_id` + `client_secret`
- Token JWT signé HS256 avec `SECRET_KEY`
- TTL : 1h
- Scope : `permissions` du client (`emit`, `read`, `admin`)

### 3.2 Staff PIN
- `POST /api/v1/staff/login` avec `agent_id` + PIN
- Bcrypt verify (cost 12)
- Lockout automatique : 5 échecs → 15 min
- Session token JWT HS256, TTL 8h (durée d'un événement)

### 3.3 X-Admin-Key
- Header pour endpoints admin (`/admin/backup/*`, `/admin/security/*`, `/admin/clients/*`, `/sync/*`)
- Comparaison via `hmac.compare_digest` (constant-time, anti-timing attack)
- Rotation manuelle via `.env` `SECRET_KEY`

### 3.4 Rate limits

| Endpoint | Limite | Fenêtre | Action si dépassé |
|---|---|---|---|
| `POST /identity/emit` | 100 | 1 heure / client | 429 silencieux (pas de Retry-After — anti-scanner) |
| `POST /auth/token` | 30 | 1 minute / IP | 429 |
| Toutes routes | 300 | 1 minute / IP | 429 |
| `POST /staff/login` | 5 | 15 min / agent_id | Lockout compte |

Rate limit implémenté via Mongo `rate_limits` collection (sliding window).

---

## 4. Contrôles opérationnels

### 4.1 Isolation processus
- Supervisor gère : backend, frontend, mongodb, frek_backup, frek_chain_watchdog
- Chaque process autonome, autorestart activé
- Backend en mode --workers 1 --reload en dev, à passer en --workers 4 en prod

### 4.2 Logs & audit
- **Structured logs** dans `/var/log/supervisor/backend.*.log`
- **Security events** dans Mongo (`security_events` collection) : rate_limit, brute_force, chain_integrity_*
- **Audit trail public** : `/api/v1/audit/{frek_id}` (lecture libre, événements notarisés)

### 4.3 Backup & restore
- **Quotidien 03:00 UTC** : mongodump + Ed25519 + .env → tar.gz → GPG AES256
- **Rétention** : 30 jours automatique
- **Restore-test** : peut être déclenché à tout moment via API
- **Non-régression** : chaque restore vérifie sha256 Ed25519 = key active

### 4.4 Monitoring
- **Interne** : `/api/v1/health/{live,ready,deep}` (probes prêts pour K8s + monitoring externe)
- **Externe recommandé** : UptimeRobot / Better Stack / cronjob.org (documenté dans RUNBOOK.md)
- **Watchdog** : `chain_watchdog` daemon vérifie intégrité toutes les 6h

---

## 5. Doctrine "Zéro PII"

FREKCORE ne stocke JAMAIS d'informations personnelles en clair.

| Donnée d'entrée | Ce qui est stocké |
|---|---|
| Email | `sha256(email + salt)` uniquement |
| Prénom / nom | Optionnel, uniquement dans `frek_stages.metadata` chiffré si besoin |
| Coordonnées GPS | Réduit à H3 hex + Plus Code (imprécis, ~10m) |
| Numéro de badge | Hash + client_uuid |

**RGPD by design** :
- Article 5 : minimisation des données ✅
- Article 25 : privacy by design ✅
- Article 32 : chiffrement + pseudonymisation ✅
- Droit à l'effacement : révocation FREK-ID = flag `revoked`, hash email conservé (car anonyme)

---

## 6. Contrôles de gouvernance

### 6.1 Clé Ed25519 — la règle d'or
- **1 personne** connaît l'existence de la clé.
- **Backup GPG** hors serveur (password manager humain).
- **Rotation** : jamais en v1.0 (invaliderait tous les passeports).
- **Compromission suspectée** = alerte critique + arrêt d'urgence + audit forensic.

### 6.2 Passphrase GPG
- Stockage : password manager humain (1Password / Bitwarden).
- Copie serveur : `/root/.frekcore/backup_passphrase` root-only.
- Rotation : manuelle, non automatisée v1.0.

### 6.3 Client secrets
- Stockage bcrypt dans Mongo (`frek_clients.client_secret_hash`).
- Rotation par API : `POST /admin/clients/{id}/rotate`.
- Client informé du nouveau secret UNE seule fois.

### 6.4 X-Admin-Key
- Une seule valeur = `SECRET_KEY` de `.env`.
- Partage : 1 personne max en v1.0.
- Future v1.1 : multi-key avec expiration + audit trail par admin.

---

## 7. Réponse à incident

### 7.1 Incident "clé Ed25519 compromise"

**Priorité** : P0 CRITIQUE.

Procédure :
1. Isoler le serveur (revoke accès public).
2. Vérifier intégrité chain via `/notary/chain/verify`.
3. Restaurer la clé depuis backup GPG (sha256 doit MATCH).
4. Si sha256 différent → attaque avérée → **rotation obligatoire** :
   - Générer nouvelle clé Ed25519.
   - Publier annonce publique (blog, git, X).
   - Marquer tous les anciens passeports "legacy" (vérifiable avec ancienne clé publique, archivée).
   - Émettre nouvelles preuves avec nouvelle clé.
5. Post-mortem écrit dans `INCIDENTS.md` + notarisé sur FREK-Chain.

### 7.2 Incident "corruption chain détectée"

Procédure :
1. Watchdog alerte via `security_events` (severity=critical).
2. Consulter `first_invalid_height` retourné par `/notary/chain/verify`.
3. Investiguer : le block est-il un tampering intentionnel ou une erreur ?
4. Si tampering → restaurer depuis backup daily précédant.
5. Publier alerte publique + notarisation post-incident.

### 7.3 Incident "MongoDB données perdues"

Procédure :
1. Arrêter le backend (`supervisorctl stop backend`).
2. Récupérer dernier backup GPG (`/app/backups/`).
3. Décrypter + extraire.
4. Restaurer clé Ed25519 en PREMIER (`chmod 600 .passport_key.pem`).
5. Restaurer Mongo (`mongorestore --drop`).
6. Vérifier `chain integrity` post-restore.
7. Redémarrer backend.
8. Documenter dans `INCIDENTS.md`.

---

## 8. Écart connu / dette de sécurité

Rien de bloquant pour v1.0. Sur la roadmap post-v1.0 :

- 🟡 Multi-key admin avec expiration + audit par admin
- 🟡 Rotation automatique client secrets (annuelle par défaut)
- 🟡 Support HSM (Hardware Security Module) pour clé Ed25519 en production
- 🟡 Isolation multi-tenant lecture (Sprint M')
- 🟢 Support Yubikey pour login admin (nice-to-have)
- 🟢 SIEM externe pour agrégation logs (Splunk / Datadog / Sentry)

---

## 9. Conformité

FREKCORE est aligné avec :
- ✅ **RGPD** (privacy by design, minimisation, chiffrement)
- ✅ **W3C DID Core 1.0 + VC Data Model 2.0**
- ✅ **EUDI Wallet Draft 13+**
- ✅ **RFC 7517 JWK**
- ✅ **RFC 8785 JCS**
- 🟡 **ISO 27001** (documentation prête, audit externe non fait)
- 🟡 **SOC 2 Type I** (documentation prête, audit externe non fait)

---

## 10. Ce document répond à

- *Qu'est-ce qui est protégé et comment ?* → §1 + §2 + §3
- *Que faire en cas d'incident ?* → §7
- *Quelles données sont stockées ?* → §5
- *Quelles limites connues ?* → §8
- *Conformité réglementaire ?* → §9
