# 0002 — Founder Decision Package: `identity_engine` merge / renew / recovery

Status: **AWAITING FOUNDER DECISION**. Nothing in this document is implemented. Per `docs/decisions/0001-founder-decisions-2026-08-31.md` §28, work that would "merge incompatible identity semantics" or otherwise redefine FREK-ID identity behavior stops here for a founder decision — this package exists to make that decision informed, not to make it.

Scope: the three `identity_engine` lifecycle capabilities left open after `revoke`/`update`/`archive`/`search` were closed (`reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #2, `docs/architecture/FREK_ID_RECONCILIATION.md`). Evidence below was re-verified directly against the code and the historical `frek_v3/docs/` corpus while writing this package (2026-08-31), not carried over from memory.

---

## 1. MERGE

### Current code reality
No merge logic exists anywhere in the codebase. `grep -rn "merge" backend/identity_engine/` returns no match (confirmed three separate times across this project's phases — Phase 1's `02_GAP_ANALYSIS.md`, Phase 3's re-confirmation, this pass). `identity_engine`'s `frek_persons` documents have no field that references "another identity of the same person" — the closest adjacent mechanism is `linked_objects` (`POST /identity/link-object`), which attaches an *object* (a `.fk` or a moment) to an identity, never another *identity* to an identity.

### Historical FREK documentation evidence
None found. `grep -rniE "\bmerge\b" frek_v3/docs/*.md` returns no real hits (the apparent matches are all substring collisions with "Emergent.sh", the integration partner's name). Identity merge is not a documented original-FREK concept — it does not appear in `FREK_Architecture_Integree_v0.2.md`, `FREK_V3_Reconciliation_Architecture_v0.2.md`, or any other spec in that corpus.

### Equivalent in `frek_v1` / `backend/frek/`?
No. `frek_v1` has revoke and renew but no merge (`reports/FREKCORE_CONTRADICTIONS.md` C1, re-verified). `backend/frek/` ("FREK v2") mints a *work* identity (a creative-work fingerprint), not a person identity — merging two audio-work certifications is not the same question and has no bearing here.

### Exact semantic ambiguity
"Merge" is ambiguous between two structurally different operations, and the founder needs to specify which (or both) is wanted:

1. **Same-system merge** — a person accidentally created two separate `identity_engine` identities (e.g. registered a second time after losing their first Passkey, before any recovery mechanism existed — see §3) and wants them combined into one surviving `frek_id`.
2. **Cross-system merge** — reconciling a `frek_v1`-minted event-badge identity with an `identity_engine` person identity into a single record. This is the Contradiction-C1-shaped question (`reports/FREKCORE_CONTRADICTIONS.md`), already partially answered by the founder as "reconcile, do not replace" (§5 of decision 0001) — but "reconcile" was never specified as "merge into one collection" versus "keep separate, cross-reference via `linked_objects`" (already built, see `docs/architecture/FREK_ID_RECONCILIATION.md`'s "second consumer" section for a live example: the fingerprint/geo per-holder-auth work uses exactly this cross-reference, not a merge).

### Implementation options

**Option A — Same-system merge only, alias-and-preserve.** Two `identity_engine` `frek_id`s, both provably owned by the requester (dual session proof, see Security below), combine into one surviving record: credentials, `linked_objects`, and `linked_sessions` union into the survivor; the retired `frek_id` becomes a permanent redirect stub (`GET /{old_id}` returns `{"merged_into": "<new_id>"}` rather than 404 or deletion) — no identity is ever deleted, matching decision 0001 §5's "no identity deletion" constraint. Cross-system merge (frek_v1 ↔ identity_engine) is explicitly out of scope for this option.

**Option B — No true merge; formalize the existing cross-system LINK instead.** Do not build same-system merge at all. Document `POST /identity/link-object` as the intentional, permanent answer to "how do two identity-shaped records relate to one person" — a `frek_v1` UUID and an `identity_engine` `frek_id` stay two distinct, independently-resolvable records, cross-referenced via `linked_objects`, never unified. This closes the cross-system half of the ambiguity above by declaring it answered (link, not merge) and leaves the same-system case (duplicate `identity_engine` registrations) to Option C below or to §3 (recovery) making duplicate registration unnecessary in the first place.

**Option C — Full unification (retire one record into the other's collection).** The higher-risk option: physically move a `frek_v1` identity's data into an `identity_engine` `frek_persons` document (or vice versa), collapsing two collections' worth of semantics into one. Raises real questions decision 0001 doesn't answer: which system's `frek_id` format wins, what happens to `frek_v1`'s OAuth2-client attribution once the record leaves that system's authority model, and whether "retiring" a record without deleting it (per the "no identity deletion" rule) is even representable across two structurally different collections.

### Compatibility impact
Any option must never invalidate a previously-issued `frek_id` string — QR codes, DIDs (`did:frek:{frek_id}`), and external systems (KORA, Wallet, Academy per `docs/interfaces/`) may already hold a reference to it. Option A's redirect-stub design satisfies this directly. Option B has zero compatibility impact (no existing behavior changes). Option C is the only one that risks breaking an external resolver expecting a `frek_id` to always resolve within its originating system.

### Migration impact
Option A: none required until a merge is actually invoked (opt-in, per-pair). Option B: none — it is a documentation decision, not a code change. Option C: potentially large — every existing cross-referenced record (`linked_objects` entries, notarized events citing either `frek_id`) would need a resolution strategy for "which side does this citation now point to."

### Security implications
Merge (same-system or cross-system) is a high-value identity-takeover target: if the authority check for "these two identities belong to the same person" is anything weaker than proof of control over *both* frek_ids, an attacker who controls one identity could annex a victim's separate identity's `linked_objects`/credentials into their own. Option A's design (dual session proof — the requester must present a valid `X-FREK-Session` for the surviving identity *and* prove control of the identity being retired, e.g. via its own session or a Passkey ceremony) is the minimum bar; an admin-only override (matching this module's existing `_holder_or_admin` pattern) would need to be logged with an explicit justification, since it's the one path that bypasses dual-proof. Option B has no new security surface (no new capability). Option C inherits Option A's risk plus the added surface of two different authority models (OAuth2-client vs. holder-session) needing to agree on one outcome.

### Recommended option
**Option B**, as the default: the cross-system question (C1) is already answered by the existing `linked_objects` mechanism, live-proven in the fingerprint/geo per-holder-auth work — formalizing it as the permanent answer avoids inventing new identity-unification machinery for a case that already has a working, lower-risk solution. If same-system duplicate-registration merge (Option A) is still wanted after §3 (recovery) closes the main reason someone would end up with two `identity_engine` identities in the first place, it can be scoped as its own, later, narrower decision.

---

## 2. RENEW

### Current code reality
`identity_engine`'s `FREKIdentity` model (`backend/identity_engine/models.py`) has no `expires_at` or any expiry-related field at all — `frek_id, identity_type, display_name, created_at, status, credentials, linked_objects, linked_sessions, permissions, metadata`. There is no route named or shaped like renewal anywhere in `backend/identity_engine/routes.py`.

### Historical FREK documentation evidence
No mention of `identity_engine`-side renewal in any historical document. The renewal *concept* exists only in `frek_v1`'s own design and code.

### Equivalent in `frek_v1` / `backend/frek/`?
Yes, in `frek_v1` — real, live, well-specified: `POST /{frek_id}/renew` (`backend/frek_v1/identity.py:256-311`) extends the identity's `expires_at` field (validated to be in the future), records `renewed_at`, refuses on an already-revoked identity, and notarizes a `"renewal"` block with `previous_expires_at`/`new_expires_at`/`reason`. This is meaningful there because `frek_v1` identities are explicitly **time-bound event badges** with a real expiry concept baked into the data model from the start. `backend/frek/` has no renewal concept — its lifecycle (GENESIS→WORKSHOP→...) tracks a creative work's maturity stages, not a credential's time-to-live.

### Exact semantic ambiguity
`frek_v1`'s renew is only coherent *because* `frek_v1` identities expire. `identity_engine` identities are explicitly positioned (`docs/interfaces/*.md`, this module's own docstrings) as long-lived personal identities with no expiry. "Renew" for `identity_engine` is therefore ambiguous between three different things, only one of which is a literal port of `frek_v1`'s meaning:

1. **A category error** — the concept simply does not apply; `identity_engine` identities do not expire, so there is nothing to renew.
2. **A new identity-level expiry system**, ported from `frek_v1` — this would mean *adding* an expiry concept to `identity_engine` that does not exist today, a real data-model change, not an adaptation of an existing field.
3. **Session-token refresh** — extending the `X-FREK-Session` token's TTL (`SESSION_TTL_DAYS`, currently fixed, no refresh mechanism exists) before it lapses. This is a real, narrow, and completely different capability that happens to share the English word "renew" with `frek_v1`'s concept but is not the same thing at all — conflating them under one name would repeat exactly the terminology-collision pattern already found and fixed once this session (the `/revoke` path collision, `docs/architecture/FREK_ID_RECONCILIATION.md`).

### Implementation options

**Option A — Do not implement.** Document `identity_engine` identities as non-expiring by design; `renew` stays a `frek_v1`-only concept. Zero code change.

**Option B — Session-token refresh, under a distinct name.** Add a narrow capability (e.g. `POST /identity/session/refresh`) that extends the current session's TTL given a still-valid `X-FREK-Session`, deliberately not named "renew" to avoid the terminology collision. Solves real UX friction (forced re-authentication) without touching identity-level semantics at all.

**Option C — Add identity-level expiry, mirroring `frek_v1`.** Add `expires_at` to `FREKIdentity`, build `POST /{frek_id}/renew` analogous to `frek_v1`'s. The largest option: requires a default-TTL policy decision, a decision on what happens to an identity that lapses (soft-lock like `archived`? hard-lock like `revoked`? something new?), and touches every existing consumer of `identity_engine` that currently assumes these identities never expire.

### Compatibility impact
Options A and B: none — nothing existing changes. Option C: potentially breaking — any code (this codebase's or an external CVLN system's, per `docs/interfaces/*.md`) that treats an `identity_engine` `frek_id` as permanently resolvable would need to handle a new "expired" state it has never had to handle before.

### Migration impact
Options A/B: none. Option C: every pre-existing `frek_persons` document needs an `expires_at` value assigned retroactively — there is no principled default (the identity was created with no expiry in mind) — this is a real, unavoidable migration decision, not just a schema addition.

### Security implications
Option B is net-neutral-to-positive: shorter-lived sessions with an explicit refresh path are generally *more* secure than either very-long-lived sessions or a forced-permanent one. Option C introduces a new failure mode with real user-facing security-adjacent consequences: a mis-set default TTL would silently lock legitimate users out of their own identity (indistinguishable in effect from the exact denial-of-service the P0 pass spent effort preventing elsewhere this session), and the "what happens when it lapses" question directly overlaps revoke/archive's already-decided semantics without an obvious answer for how it's different.

### Recommended option
**Option A** as the base position (the concept genuinely does not apply to a long-lived personal identity), with **Option B** as an optional, separately-scoped, distinctly-named addition only if session-refresh UX friction is an evidenced real problem — not assumed here. Option C is not recommended without a much more specific founder brief on what "an `identity_engine` identity expiring" is even supposed to mean for a system explicitly positioned as long-lived.

---

## 3. RECOVERY

### Current code reality
There is no recovery flow in either identity system. More specifically, and more urgently than the other two items: `identity_engine`'s **only** authentication mechanism is WebAuthn/Passkey, and `register_begin`'s ownership check (`backend/identity_engine/routes.py`, the P1 security fix found while building revoke) has **no admin-key override at all** — unlike every other gated route in this module (`revoke`, `update`, `archive`, `search`, `export`), which all accept `X-Admin-Key` as a fallback when the holder can't self-serve. Verified directly in the current code:

```python
if identity.get("credentials") and (
    not x_frek_session or service.verify_session_token(x_frek_session) != frek_id
):
    raise HTTPException(403, "Session du titulaire requise pour ajouter une Passkey")
```

This means: **today, a holder who loses every registered Passkey (device lost, stolen, wiped, or simply replaced without transferring credentials) has no way — not even via support/admin intervention — to add a new Passkey to their existing identity.** Their identity's data (`linked_objects`, history) remains intact and publicly readable via `GET /{frek_id}`, but the identity becomes permanently unable to authenticate as itself again. This is a genuine, unmitigated lockout gap that exists in production code right now, not a hypothetical.

### Historical FREK documentation evidence
None. The only "recovery" hit anywhere in `frek_v3/docs/` (`CE_QUI_MANQUE.md` line 146, "Comment gère-t-on le rollback autorisé (recovery)?") was read in full context before citing it here and is **not** about identity/account recovery — it is an open question about FAP hardware firmware OTA rollback recovery, a completely unrelated concept from an unrelated (hardware) part of the FREK ecosystem. Identity-level account recovery is not a documented original-FREK concept.

### Equivalent in `frek_v1` / `backend/frek/`?
No — and not coincidentally. `frek_v1` has no holder-session concept at all (§ "Second finding" of `docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`; confirmed again in `docs/architecture/FREK_ID_RECONCILIATION.md`): every `frek_v1` operation is OAuth2-client-scoped, meaning the *client* (e.g. CC2026's own backend) always has standing authority over its own identities — there is no scenario where "the holder locked themselves out" is even a coherent failure mode for `frek_v1`, because the holder was never the one authenticating in the first place. `backend/frek/` mints work-identities, not person identities — "the artist forgot their Passkey" is not a concept that applies there either. This confirms `identity_engine` is the *first and only* FREKCORE system where holder-self-lockout is even possible, which is exactly why no prior system had to solve it.

### Exact semantic ambiguity
Without any secondary factor already collected at registration (no email, no phone, no recovery codes — `InitIdentityRequest`/`FREKIdentity` collect none of these today), "self-service recovery" is not a small route addition — it requires deciding what secondary proof would even exist to recover *with*. The ambiguity is between:

1. **Admin-mediated recovery** — an operator, after some out-of-band verification (support ticket, live conversation, whatever process the founder/ops team defines outside this codebase), authorizes the locked-out holder to register a fresh Passkey.
2. **Self-service recovery via a new secondary factor** — the system would need to start collecting something it doesn't collect today (recovery codes issued at registration time, an email/phone verification loop) specifically to enable this later. This is new capability scope, not a route.
3. **No recovery at all, mitigated by upstream UX** — encourage/require registering 2+ Passkeys at initial onboarding so single-device loss is never total loss. This doesn't help anyone already single-credentialed under the current flow, and isn't enforceable from the backend alone.

### Implementation options

**Option A — Admin-mediated override on `register_begin`/`register_complete`.** Add the same `_holder_or_admin`-shaped check already used everywhere else in this module: when `x_frek_session` doesn't verify, accept `X-Admin-Key` as an alternative authorization to add a new Passkey to an already-credentialed identity. Smallest possible change (one `elif` clause, matching an existing, already-reviewed pattern) and closes the *only* route in this module that currently has zero override path for a holder who can't self-serve.

**Option B — Self-service recovery codes.** At `POST /init` (or at first credential registration), generate and return a set of one-time recovery codes the holder is responsible for storing themselves; a new `POST /identity/{frek_id}/recover` endpoint accepts one such code (once, then invalidates it) as an alternative to a session token for `register_begin`. Industry-standard shape, but real new scope: code generation, storage (hashed, like credentials), a UX for the holder to actually retain them, and a migration question for every identity that already has credentials today (see Migration impact below).

**Option C — Defer entirely; rely on Option A as the only mitigation.** Treat Option A as sufficient for now (it already closes the "zero mitigation" gap completely, just via a human-in-the-loop rather than self-service) and explicitly postpone self-service recovery (Option B) to a later, separately-scoped decision once real usage data shows whether admin-mediated recovery's operational load is actually a problem.

### Compatibility impact
Option A: none — purely additive, the existing anonymous-bootstrap and holder-session paths through `register_begin`/`register_complete` are untouched. Option B: none to existing routes, but introduces a new artifact (recovery codes) holders must be told about, ideally at registration time going forward — no retroactive compatibility break, just nothing retroactive either (see Migration).

### Migration impact
Option A: none. Option B: real and unavoidable — every `identity_engine` identity that already has a registered credential today has zero recovery codes on file (the field doesn't exist yet), and there is no way to retroactively deliver codes to a holder the system has no verified contact channel for. Any Option B design needs an explicit answer for "what about identities credentialed before this shipped" (most likely: no accommodation for them, only future registrations get codes — a real, visible gap the founder should sign off on knowingly, not by omission).

### Security implications
Option A reintroduces, deliberately and in a controlled way, exactly the identity-takeover vector the P1 security fix (found while building revoke) just closed — an attacker who compromises the shared `X-Admin-Key` could add a Passkey to *any* credentialed identity, not just their own. This is not a new risk category for this codebase (the identical trust assumption already covers `revoke`/`update`/`archive`/`search`/`export`), but it is worth the founder explicitly confirming the admin key's operational security (rotation, access scoping) is adequate before this closes a sixth route with it. Option B's new attack surface is recovery-code theft/interception at whatever delivery channel is chosen — real, but well-understood and mitigable (single-use, hashed at rest, short validity window). Option C carries no new risk beyond Option A's (it doesn't add anything Option A didn't already add).

### Recommended option
**Option A**, as the immediate fix — it is the smallest possible change, uses a pattern already reviewed and accepted five times over in this same module, and closes a real, currently-unmitigated lockout with no admin escape hatch at all. **Option B** is worth pursuing afterward as a genuinely better long-term answer (self-service, no support burden, no admin-key-compromise blast radius on this route) but is real new scope deserving its own dedicated design pass, not a rushed addition here.

---

## Summary table

| Item | Recommended option | Why | Requires founder sign-off on |
|---|---|---|---|
| Merge | B — formalize existing cross-system link, no true merge | The C1 cross-system question already has a working, lower-risk answer (`linked_objects`); same-system merge isn't urgent once recovery (below) reduces why duplicates happen | Whether "reconcile" (decision 0001 §5) is satisfied by link-not-merge, or whether true merge is still wanted |
| Renew | A — do not implement (base); B — session refresh, distinctly named (optional) | The concept doesn't apply to a non-expiring identity; conflating it with `frek_v1`'s expiring-badge renewal repeats a terminology collision already found once this session | Whether `identity_engine` identities should ever expire at all (a much bigger question than "add a renew route") |
| Recovery | A — admin-mediated override on register_begin/register_complete | Closes a real, currently-unmitigated lockout gap today, using an already-reviewed pattern; smallest safe change | Confirming the admin key's operational security is adequate to extend to a sixth route |

**Nothing above is implemented.** This document is the input to a founder decision, not a substitute for one.
