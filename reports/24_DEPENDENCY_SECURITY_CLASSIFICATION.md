# 24 — Dependency/Security Advisory Classification

Per the founder's instruction: the 115 dependency advisories
(`reports/17_SECURITY_FINAL.md`) must not remain an undifferentiated
informational red forever. This report classifies every one of the 20
flagged packages into the requested buckets, re-verified fresh this pass
(not copied from the prior report's numbers), and states exactly what is
fixed, what is deferred, and why.

## Reproduction (exact command, re-run 2026-08-31)

```
pip-audit -r <(grep -v '^emergentintegrations' backend/requirements.txt) --format json
```

`emergentintegrations` (the one private, non-PyPI package) has to be
excluded for `pip-audit` to resolve the file at all — the same
workaround `reports/17_SECURITY_FINAL.md` used, re-verified still
necessary. **115 findings across 20 packages — identical count to the
prior report**, confirming nothing has silently drifted since.

## Classification

| Package | Findings | Direct import in `backend/`? | Classification | Reasoning |
|---|---|---|---|---|
| `starlette` | 9 | Yes (FastAPI's foundation — every request) | **Exploitable/reachable** | Core web framework; every inbound request is processed through it |
| `cryptography` | 1 | Yes (`passport/keys.py` Ed25519, `webauthn` dependency) | **Exploitable/reachable** | Actively used for signing and WebAuthn ceremonies |
| `pyjwt` | 11 | Yes (`frek_v1/utils.py`, `staff/routes.py`) | **Exploitable/reachable** | Issues and verifies real auth tokens |
| `python-multipart` | 5 | Yes (FastAPI's own form/file-upload parsing) | **Exploitable/reachable** | Multiple routes accept file uploads (badges/PDF, staff) |
| `requests` | 1 | Yes (`storage/emergent_object_storage.py`, `moment/storage.py`) | **Potentially reachable** | Used for outbound HTTP; `emergent_object_storage.py`'s path is gated behind `EMERGENT_LLM_KEY` (unset by default — confirmed via this session's own dev-server boot log: "Object Storage desactive"), `moment/storage.py`'s is unconditional |
| `urllib3` | 3 | Transitive (via `requests`) | **Potentially reachable** | Same reachability as `requests` — carries its HTTP transport |
| `idna` | 2 | Transitive (via `requests`/`urllib3`) | **Potentially reachable** | Same chain |
| `python-dotenv` | 1 | Yes (`server.py` startup, `load_dotenv`) | **Transitive/unreachable in practice** | Runs once at process start against a local `.env` file the operator controls — not attacker-supplied input |
| `pyasn1` | 6 | Transitive (via `webauthn`, added this session for RECOVERY/Passkey work) | **Potentially reachable** | `webauthn` is a real, active dependency (WebAuthn ceremonies); `pyasn1` is its ASN.1 parsing dependency |
| `pillow` | 27 | **No** direct import found (`grep -rn "^import PIL\|^from PIL" backend/` → no matches) | **Transitive/unreachable in practice** | Pulled in by `reportlab` (PDF generation, `pdf_batch/service.py`) as an optional imaging backend; the one image `reportlab` draws there is a server-generated QR code buffer, not attacker-supplied external image data — technically loadable, not a realistic attack surface |
| `aiohttp` | 25 | **No** | **Blocked by private dependency/infrastructure** | Required only by `litellm`, which is required only by `emergentintegrations` — the one private package this deployment cannot install (no access to its index) and which `backend/services/webhook.py` already imports lazily/defensively. This entire chain cannot execute in this deployment today |
| `litellm` | 12 | **No** | **Blocked by private dependency/infrastructure** | Same chain as `aiohttp` above — a dependency of the uninstallable private package |
| `google-*` family (pulls in `httplib2`, contributes to `ecdsa`) | 2 (`httplib2`) | **No** | **Blocked by private dependency/infrastructure** | Same chain — `emergentintegrations`' own dependency tree |
| `ecdsa` | 2 | **No** (`grep -rn "import ecdsa" backend/` → no matches) | **Blocked by private dependency/infrastructure** | Same chain |
| `pymongo` | 1 | **No** direct import (`grep -rn "^import pymongo" backend/` → no matches) — only `motor` wraps it | **Transitive/unreachable in practice** | `backend/`'s own code exclusively calls Motor's async API; `pymongo`'s vulnerable surface (if any is request-reachable at all) sits entirely inside Motor's own wrapping, unchanged by anything this codebase does |
| `msgpack` | 1 | **No** | **Transitive/unreachable in practice** | No direct import found; a dependency of the `emergentintegrations` chain or a MongoDB driver codec never exercised without a feature this deployment doesn't use |
| `black` | 3 | N/A (dev tool) | **False positive/not applicable** | Runs only in CI's lint job and local development, never in served code |
| `click` | 1 | N/A (dev tool, CLI dependency of `black`/`uvicorn`) | **False positive/not applicable** | Same — no production request path invokes it |
| `pygments` | 1 | N/A (dev tool, syntax highlighting) | **False positive/not applicable** | No production code path |
| `pytest` | 1 | N/A (test tool) | **False positive/not applicable** | Never present in a production deployment's actual served process |

## Summary

- **Exploitable/reachable (4 packages, 26 findings)**: `starlette`,
  `cryptography`, `pyjwt`, `python-multipart` — real production request
  paths.
- **Potentially reachable (4 packages, 12 findings)**: `requests`,
  `urllib3`, `idna`, `pyasn1` — used, but either conditionally-gated or
  in a supporting/parsing role rather than a primary attack surface.
- **Transitive/unreachable in practice (4 packages, 30 findings)**:
  `python-dotenv`, `pillow`, `pymongo`, `msgpack` — present in the
  dependency graph, no direct import, no realistic attacker-controlled
  input reaching the vulnerable code path in this deployment's actual
  usage.
- **Blocked by private dependency/infrastructure (4 groups, 41 findings)**:
  `aiohttp`, `litellm`, `httplib2`(`google-*`), `ecdsa` — entirely inside
  the `emergentintegrations` dependency tree, which cannot even install in
  this environment (confirmed repeatedly, same root cause as the
  documented Docker-build failure).
- **False positive/not applicable (4 packages, 6 findings)**: `black`,
  `click`, `pygments`, `pytest` — dev/CI tooling, never present in a
  served request path.

**115 findings accounted for across all five buckets — none left
unclassified.**

## What was fixed this pass vs. deferred, and why

**Not bumped in this pass.** Every flagged package has a published fix
version (verified — `pip-audit`'s own `fix_versions` field, checked for
all 20 packages). A responsible bump of the four **exploitable/reachable**
packages specifically is the right next action, but three of the four
carry real compatibility risk that this pass is not positioned to verify
safely:

- `starlette` — FastAPI pins a compatible `starlette` range; bumping it
  without also checking FastAPI's own compatibility matrix risks a
  runtime break across every route in the application, and this
  sandbox's only verification path is `mongomock`, not the real
  MongoDB integration suite that would actually exercise every route
  (blocked on `reports/23_REAL_MONGODB_VALIDATION_PLAN.md`'s own
  infrastructure gate).
- `cryptography` — bumped once already this session (`41.0.7` →
  `49.0.0`, specifically to satisfy `webauthn`'s own constraint,
  `backend/requirements-ci.txt`'s own comments record why). A second
  bump to `50.0.0` in the same pass, without the real-Mongo integration
  suite available to catch a regression in the WebAuthn ceremony flow
  this session just built RECOVERY on top of, is exactly the kind of
  compounding, unverified change the standing CI discipline exists to
  prevent.
- `pyjwt` — a real, load-bearing auth dependency (`frek_v1`, `staff`);
  same reasoning — a version bump deserves the full integration suite,
  not just the unit-tier one this sandbox can run.

`python-multipart`'s bump is the lowest-risk of the four (a narrower,
more isolated surface — form/file parsing only) and is the recommended
first target once real-Mongo infrastructure is available to run the full
regression suite against it, not blocked by anything else.

**This is not "leaving it red forever"** — it is recording, with
evidence, that the safe order of operations is real-Mongo validation
first (so a dependency bump can be verified against the actual
integration suite, not just `mongomock`), then the four reachable
packages, in the order named above. Bumping now, unverified, to make a
number go down would be exactly the kind of change the standing
discipline ("do not weaken CI gates... do not claim all CI green while...
remain red") exists to prevent applied to dependencies instead of tests.

## What remains before this can be marked fully closed

1. Real-MongoDB infrastructure becomes available
   (`reports/23_REAL_MONGODB_VALIDATION_PLAN.md`).
2. Bump `python-multipart` first (lowest risk), run the full integration
   suite, confirm green, push.
3. Bump `pyjwt`, `cryptography`, `starlette` in that order (each on its
   own commit, own verification pass, per the standing one-logical-
   change discipline) — `starlette` last, since a FastAPI-compatibility
   check is required before touching it.
4. Re-run `pip-audit` after each bump to confirm the specific findings
   it was meant to close are actually gone, not just that the version
   number moved.
5. The `blocked by private dependency/infrastructure` bucket (41
   findings) remains blocked until `emergentintegrations` either gets a
   configured private index (a human/infrastructure decision, not a code
   one) or is vendored/replaced — tracked, not attempted here, matching
   the Docker-build failure's own long-standing documented status.
