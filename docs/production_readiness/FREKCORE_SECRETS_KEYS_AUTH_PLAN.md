# FREKCORE Secrets, Key Management & Production Auth Plan

**Status: PLANNING ARTIFACT.** Documents current, verified reality plus a
concrete plan for the two real gaps found (Ed25519 rotation/revocation,
delegation-runtime wiring). No code changed by this document.

## 1. Secrets management

**Current state (EXISTS, verified)**: every secret this codebase needs is
read via `os.environ[...]` — `SECRET_KEY`, `FREK_EMAIL_SALT`,
`FREK_CLIENT_KILTIKONET_SECRET`, `FREK_CLIENT_CVLBRAIN_SECRET`,
`FREKCORE_SECRET_KILTIKONET`, staff PINs, `MONGO_URL`/`MONGO_URI`. None have
a hardcoded fallback value that would work in production (`.env.example`
ships only placeholder text, e.g. `replace-with-a-strong-random-secret`).
`.env` itself is untracked (confirmed: absent from `git ls-files`).
`docker-compose.yml` uses the `${VAR:?message}` syntax for the required ones
— compose refuses to start at all if they're unset, a correct fail-closed
default.

**Where secrets should live in production** (FOUNDER-OPERATED choice of
mechanism, repo-side requirement is only "never in git, never in code"):

- Simplest: a `.env` file on the host, `chmod 600`, owned by the service
  user, referenced by `EnvironmentFile=` (systemd path) or Compose's
  `env_file:` — this is what `backup_frekcore.sh` already assumes exists at
  `/app/backend/.env`.
- More robust (optional, not required to launch): a secrets manager
  (e.g. `pass`, HashiCorp Vault, or the OS keyring) injecting env vars at
  process start instead of a plaintext file at rest — worth doing once the
  service is handling real user data, not a blocker before that.
- **Never**: committing `.env`, printing secret values in logs (confirmed
  this codebase doesn't — `server.py` logs startup steps by name, never by
  value), or embedding a secret in a URL query string that would land in
  access logs.

**GitHub Actions secrets**: `MONGO_URI` is now confirmed working as a
repository secret (this session, `real-mongo-validation` job). The same
pattern (repository secret, referenced as `${{ secrets.NAME }}`, injected as
an env var, never echoed) is the template for any future CI-side secret
(e.g. a future deploy key, once CI gains a deploy step — see the
architecture doc §6 / roadmap doc §4).

## 2. Ed25519 key lifecycle — storage (EXISTS), rotation & revocation (MISSING)

**Storage — real, verified**: `backend/passport/keys.py` — a single Ed25519
private key, generated on first boot if `FREK_PASSPORT_KEY_PATH` doesn't
exist, written with `chmod 0600`. `KEY_ID` (`frek-passport-v1` by default)
is the only versioning concept that exists today. `/health/deep` already
reports this key's SHA-256 fingerprint and confirms its file permissions are
not group/other-readable (`mode_secure`) — genuine, existing verification,
not proposed.

**The real gap**: this is a **single, static key with no rotation and no
revocation path**. If it is ever compromised, or simply due for scheduled
rotation, there is today no way to:
1. Introduce a new key while old signatures (already anchored in the
   FREK-Chain, already shipped to holders as `.fk` proof material) remain
   verifiable against the *old* public key.
2. Mark the old key as revoked so a verifier checking a *new* claim signed
   with a leaked old key rejects it, while still trusting *historical*
   claims genuinely signed before the compromise (a real distinction —
   revocation must be forward-looking, not retroactively invalidate
   everything the key ever signed, or every past proof becomes worthless on
   every future rotation).

**Plan (not implemented; sized for a future, explicitly-authorized state,
most likely Production Readiness)**:

- Extend `KEY_ID` from a single string constant into a small, persisted
  **key registry** (a new Mongo collection, e.g. `passport_keys`: `key_id`,
  `public_key_pem`, `created_at`, `status` [`active`/`retired`/`revoked`],
  `revoked_at`, `revocation_reason`) — reusing this codebase's existing
  "small, typed, Mongo-persisted registry" pattern (`registry/`,
  `permissions/`), not a new architecture.
- Verification call sites (wherever a signature is checked against "the"
  public key today) look the signer's `key_id` up in this registry instead
  of assuming a single global key — every signed artifact already carries
  enough context to know which key signed it (event/block metadata), so
  this is additive, not a breaking change to the signed payload shape.
- Rotation procedure: generate a new key under a new `key_id`, insert it as
  `active`, mark the previous key `retired` (not `revoked` — a retired key
  still verifies old signatures, it's simply no longer used for *new*
  signing). Revocation procedure: mark a key `revoked` with a reason and
  timestamp; verification of anything signed by it *after* `revoked_at`
  fails, verification of anything signed *before* `revoked_at` still
  succeeds (the registry's `revoked_at` timestamp, checked against the
  signed artifact's own timestamp, is exactly the mechanism — reusing this
  codebase's RFC3339-UTC-everywhere convention).
- This explicitly reuses the Permission Engine's own `status`/timestamp
  vocabulary conventions (`ServiceIdentity.revoked_at`,
  `DelegationGrant.revoked_at` from STATE_7/8) rather than inventing a new
  one — `NO_PARALLEL_AUTHORITY_ENGINE`-style discipline applied to key
  management too.

## 3. Production auth/authz — what's real today, what's still unwired

| Layer | Status | Detail |
|---|---|---|
| `identity_engine` (WebAuthn holder sessions) | LIVE, enforced on routes | Real second-factor-capable identity, session tokens issued via `identity_service.issue_session_token`, checked via `X-FREK-Session` throughout D1-D5. |
| `frek_v1/auth.py` (client-credential OAuth2) | LIVE, enforced on routes | Issuer/service bearer tokens (`create_access_token`), checked via `Authorization: Bearer` on registry writes and elsewhere. |
| Admin key (`X-Admin-Key`, `SECRET_KEY`) | LIVE, enforced on routes | Single shared admin secret across every admin-gated route. **Note for production**: this is a single shared secret, not per-admin — if more than one human needs admin access, this doesn't distinguish who did what (the audit trail records the *action*, not *which* admin key-holder). Sized as a Production-Readiness item, not a blocker: today's single-operator reality (the founder) makes this acceptable for launch. |
| `permissions/` (Role/Scope/Action/`decide()`) | Built, tested, **not wired** | Confirmed unchanged status through STATE_7/8: zero live callers. This is the intended future authorization layer (subject -> role -> scope -> resource -> action -> decision) but nothing in `server.py` calls `decide()` today. |
| `permissions.delegation` (`delegation_authority_chain_valid()`) | Built, tested, **not wired** | STATE_8 closed this to UNIT_VERIFIED — proves the logic is correct in isolation, not that any route actually consults it. |

**Wiring plan (not implemented; a real, scoped piece of Production Readiness
work, not a redesign)**:

1. Pick ONE real route with a genuine multi-actor delegation need (the
   mission's own STATE_7 example — "the Agent Factory may invoke FREKCORE
   only within these delegated scopes" — is a good, concrete first case,
   once CVLN wiring is authorized; until then, a same-system example like
   "an admin delegates a specific holder temporary write access to one
   object" is a self-contained first target that needs no ecosystem wiring
   at all).
2. Add a dependency-injection style check at that route: resolve the
   caller's `Subject`/`DelegationGrant` from a persisted collection (new,
   small — same registry pattern as §2 above), call
   `delegation_authority_chain_valid()`, and 403 on `allowed=False`.
3. This is additive to that one route; every other route keeps its current
   auth mechanism unchanged. `NO_PARALLEL_AUTHORITY_ENGINE=TRUE` is
   preserved because this reuses the existing `decide()`/`delegation_permits()`
   functions verbatim — the wiring work is entirely "call the existing pure
   function from a route," not new authorization logic.
4. Full regression + a new integration test proving the wired route
   actually 403s an out-of-scope delegate (not just the pure-function unit
   tests that already exist) closes this item.
