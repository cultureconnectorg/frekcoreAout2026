# FREKCORE — Completion Backlog

Every item traces to a specific finding in `reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`, `reports/FREKCORE_CONTRADICTIONS.md`, `docs/PERMISSION_MATRIX.md`, or a numbered Phase 1/2/3 report — no invented roadmap items.

## P0 — Required for correctness/security

1. **Fix or gate the unauthenticated mutating routes flagged in `docs/PERMISSION_MATRIX.md`'s FLAG section**, starting with `fingerprint/consent|observe|match` and `geo/consent|observe|notarize|encode` (highest remaining severity — anyone can flip another FREK-ID's consent flags or submit observations against it). **Correction**: `POST /api/v1/notary/notarize` and `/anchor/*` were previously (mis)named here as the top item — re-reading `backend/notary/routes.py` found they already carry real `Depends(require_permission("emit"))` enforcement, live-verified by `test_anchor_sweep_requires_auth` passing in every integration run. See `docs/PERMISSION_MATRIX.md`'s correction note.
2. **Resolve the dual-identity-system split** (`reports/FREKCORE_CONTRADICTIONS.md` C1) — at minimum, decide and document which system is authoritative before any external CVLN system (Wallet, KORA, Academy) is granted write access via the interfaces in `docs/interfaces/`.
3. **Bump the 21 packages with known CVEs** identified in `reports/17_SECURITY_FINAL.md`, prioritized by the reachability/severity notes there — cannot be done blind; needs the integration suite genuinely green first (see P1 #1).

## P1 — Required for FREKCORE v1

1. **Get the 335-test integration suite to a fully known, green state against a real MongoDB** (not the `mongomock` substitute used this phase — see `reports/16_INTEGRATION_TEST_BASELINE.md` for exactly what blocked a real MongoDB here: Docker registry pulls return `403 Forbidden` from this sandbox's network policy). This is the single highest-leverage next step — almost everything else in this backlog benefits from being verifiable against it.
2. **Add the missing `identity_engine` lifecycle endpoints** (revoke, update, merge, archive, search) — named MISSING since Phase 1, still MISSING after Phase 3's re-audit (`reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md` Identity section).
3. **Wire `backend/permissions/` (Phase 2 model) into at least the P0 #1 routes** once P1 #1 makes it possible to regression-test the change.
4. **DONE (this pass)**: `sync_router`, `heritage_router`, `investor_router`, `pdf_batch_router` are now individually audited (`docs/PERMISSION_MATRIX.md`) — all confirmed real-protected except `investor_router` (2 GET-only, low-severity, genuinely public dashboard reads) and `heritage`'s `/claim` + `/lineage/{frek_id}` (intentionally public by design). Remaining: the 33 `frek`/`frek_router_advanced` legacy routes — still genuinely unaudited beyond a module-level pass, held on Contradiction C4's founder decision rather than a pure labeling question.
5. **Decide the fate of `backend/frek/` (FREK v2, legacy, unversioned, 33 unauthenticated routes)** — `reports/FREKCORE_CONTRADICTIONS.md` C4, founder decision required.
6. **Reconcile the two object-type taxonomies** (`.fk`'s `object_type` enum vs. FREK Registry's `frek.*` namespaces) — `reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`, FREK Registry section.
7. **Build the Registry instance store** (`POST/GET /api/v1/registry/objects/{namespace}`) — named since Phase 1's `08_NEXT_INTEGRATION.md`, still not built; blocks every "PROPOSED, NOT IMPLEMENTED" resolver in `docs/interfaces/*.md`.
8. **Add remaining event producers** once their underlying capability exists — `identity.revoked`/`identity.updated` depend on item #2 above; `object.created` needs a careful read of `backend/fk/routes.py` (not touched yet, larger file, higher blast radius); `certificate.issued` needs the Academy Certificate Engine to exist at all (Bloc 5, still MISSING).

## P2 — Required for ecosystem interoperability

1. **Complete exhaustive documentation reconciliation** — `reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`'s own scope note: this phase covered every named domain but not every historical document line-by-line.
2. **Reconcile FAP (`frek_v3/`) with `backend/proof_engine/`** — currently two separate, non-integrated proof concepts (`reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`, FAP section). Do not merge blind; needs a design decision on whether hardware attestation (FAP) ever becomes a `ProofState` in the software-side engine.
3. **Add Issuer/Holder/Verifier as `permissions.Role` values** (or an explicit mapping layer) — `reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`, Credentials section: the DID/VC/EUDI protocol roles and the Phase 2/3 Permission Engine's role vocabulary were never connected.
4. **Separate business/provenance/security-audit events formally** — currently conflated in `backend/audit/` (Phase 1); `backend/audit_trail/` (Phase 2/3) is the correctly-scoped security-audit-only mechanism but the older module wasn't refactored to match.
5. **OpenID4VP** (presentation, as opposed to the existing OID4VCI issuance) — currently entirely MISSING; only pursue if a real EUDI/wallet-presentation use case is confirmed (avoid inventing scope per this and prior phases' own rule).
6. **Extend the Python/TypeScript SDKs** beyond the Registry API, once each additional API family has the same kind of live-tested evidence the Registry API has (`reports/18_RUNTIME_VALIDATION.md` Priority 10) — Identity Engine's public read endpoints are the natural next candidate.

## P3 — Future / optional / research

1. **Trust anchors / trust lists** for VC verification — no current use case identified; MISSING is not necessarily wrong yet.
2. **Key rotation/revocation tooling** for the Ed25519 signing key — real gap, but no incident has forced it yet; still worth scheduling deliberately rather than reactively.
3. **A queryable cultural-provenance graph** (Produced By, Certified By, Published By, Licensed To, Sampled From — beyond the existing informal `based_on`) — named in Phase 1's original Bloc 1 spec, never built; large enough to be its own project.
4. **S3/Cloudinary `StorageProvider` implementations** — explicitly deferred twice now (Phase 2, Phase 3) for the same reason: no real, evidenced need beyond the existing Emergent Object Storage integration.
5. **eIDAS/EUDI conformance testing** against a real reference wallet or conformance suite — the code exists (`backend/eudi/`); proving compliance is a distinct, larger effort this repository has never claimed to have done (and this backlog explicitly does not recommend claiming it without that testing).

## Explicitly out of scope for this backlog (not silently dropped, addressed separately)

Two large mission briefs were received mid-session during Phase 3 and are **not** reflected in the P0–P3 items above because they were not executed this session — see the final report to the user for why (each is an independently multi-week-scale engagement: a full adversarial Red/Blue/Purple Team security assessment with an isolated attack lab, and a full UI/UX/design-system/accessibility/motion/3D overhaul of `frontend/`, which no Phase 1–3 work has touched). Both remain live requests; they need their own dedicated sessions rather than a partial, evidence-thin pass folded into this backlog.
