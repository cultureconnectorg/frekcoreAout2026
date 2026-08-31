# 20 — Event Producers (Phase 3, Priority 6)

## What the Event Registry catalog (`backend/registry/events/event_registry.json`) currently claims

| event_type | `implemented` | `status` | producer |
|---|---|---|---|
| `identity.created` | `true` | — | `identity_engine` |
| `identity.updated` | `false` | — | — |
| `identity.merged` | `false` | — | — |
| `identity.revoked` | `false` | — | — |
| `object.created` | `false` | — | — |
| `object.verified` | `false` | — | `backend/fk/routes.py POST /fk/verify` returns synchronously, no persisted/broadcast event |
| `proof.generated` | `true` | `PARTIAL` | `notary` |
| `certificate.issued` | `false` | — | — |
| `wallet.linked` | `false` | — | — |
| `artist.verified` | `false` | — | — |

## What this session verified against actual code (`grep -rn "\.publish(" backend --include="*.py"`, excluding tests)

**Exactly one real Event Bus producer exists in the entire codebase**: `backend/identity_engine/routes.py:128`, `_event_bus.publish(_build_identity_created_event(identity))`, firing `identity.created`. This is unchanged from Phase 2 and re-confirmed this phase by direct grep, not by trusting the catalog.

**`proof.generated`'s `implemented: true` needs a careful reading, not a correction.** Its own `evidence` field is honest and internally consistent once read in full: `backend/notary/service.py`'s `notarize_event()` does create a real, persisted, hash-chained block (`notary_blocks`) — that underlying *capability* is genuinely implemented, which is what `implemented: true` is asserting. What is **not** implemented is publishing that block creation as an `InProcessEventBus` event a subscriber could react to (no `.publish("proof.generated", ...)` call exists anywhere — confirmed by the same grep above). The registry's own `status: PARTIAL` already flags exactly this gap. Left as-is: editing `implemented` to `false` would contradict the entry's own evidence trail (the notarization *capability* is real), and editing `status`/`evidence` risks losing the nuance a shorter edit can't preserve. Recorded here instead, per the mission's "reconcile documentation against code" instruction, so the ambiguity is explicit rather than silently carried forward.

## Priority 6's instruction: "add producers only where real capability exists"

Checked each candidate the mission named:

- **`identity.updated` / `identity.revoked`**: no underlying capability exists — `identity_engine` (the WebAuthn/Passkey system, `frek_persons` collection) has no update/revoke/merge/archive endpoint at all (confirmed Phase 1, re-confirmed Phase 2, re-confirmed this phase — `reports/FREKCORE_CONTRADICTIONS.md` C1). `frek_v1` (the *other* identity system, `frek_identities` collection) **does** have `POST /{frek_id}/revoke` and `/renew` (`backend/frek_v1/identity.py:134,200`) — but wiring an event producer there would be adding a producer for the wrong identity system's revoke/renew semantics under an event name (`identity.revoked`) the registry's own vocabulary defines in `identity_engine` terms (see C1's full writeup). Not added this phase — would require the founder decision C1 asks for first, otherwise the producer's payload shape is a guess.
- **`object.created`**: real capability exists (`backend/fk/routes.py` creates `.fk` objects), but this phase did not touch `backend/fk/routes.py` at all — it is a larger, higher-blast-radius file not otherwise in scope this phase, and adding a publish call there without the same level of read-and-verify diligence applied to `identity_engine/routes.py` in Phase 2 would violate this mission's "no blind changes" rule. Left `false`, tracked as `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #9 (implicit in item #9's `object.created` note).
- **`certificate.issued`**: no capability exists at all — the Academy Certificate Engine (Bloc 5) is MISSING, confirmed by this phase's requirements-matrix pass (`reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`). Nothing to wire a producer to.

## Net result this phase

**No new event producer was added.** The honest, evidence-backed producer list for the Freeze Assessment's required output is:

```
identity.created  — REAL, live-verified, subscribed by Audit Trail (reports/19_PERMISSION_ENFORCEMENT.md)
```
Every other named event type in the mission's list (`identity.updated`, `identity.revoked`, `object.created`, `certificate.issued`) remains `implemented: false`, each for a specific, evidenced reason above — not silently skipped.
