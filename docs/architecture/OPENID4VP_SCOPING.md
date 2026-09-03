# OpenID4VP Scoping

Per the founder's instruction: continue the OpenID4VP interoperability
work while preserving the boundary — *OpenID4VP is interoperability
around FREK-ID; it does not define FREK-ID* — and implement only what is
justified by an actual interoperability need, clearly classifying
anything deliberately deferred.

## Current state (re-verified this pass)

`backend/eudi/routes.py` implements **issuance only**: `POST
/credential-offer/{frek_id}`, `POST /token`, `POST /credential`, `POST
/credential/verify-sdjwt` — the OID4VCI half of the EUDI/OpenID4VC
family. `grep -rn "OpenID4VP\|openid4vp\|vp_token\|presentation_definition" backend/`
finds no matches anywhere — confirmed, consistent with every prior phase's
finding (`reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`'s own "MISSING"
entry, `docs/architecture/FREK_ID_CANONICAL_MODEL.md` §5). This pass adds
no code — it scopes what building it would actually require, and records
why that build is not started yet.

## What OpenID4VP would add, and where it sits relative to FREK-ID

OID4VCI (existing) answers *"issue me a credential about this FREK-ID."*
OpenID4VP answers the complementary question: *"a Verifier asks a
Holder's wallet to present one or more already-issued credentials, and
the Holder's wallet returns a signed Verifiable Presentation."*
FREKCORE's own role in that exchange is unchanged from its issuance role:
it can act as **Verifier** (asking to see a credential someone else
holds) or as the platform whose **already-issued VCs** get presented
elsewhere — either way, OpenID4VP consumes FREK-ID/VC/DID exactly as they
already exist (`did/vc.py`, `identity_engine`), it does not add, replace,
or reinterpret any of them. Concretely, the minimal building blocks would
be:

1. A `presentation_definition` (DIF Presentation Exchange) describing
   what claims a Verifier wants — a static JSON artifact per use case,
   not a new identity concept.
2. A `POST /identity/{frek_id}/present` (or an EUDI-namespaced
   equivalent) that verifies an incoming VP against that definition and
   the existing `did/vc.py` verification logic — reusing the verifier
   already built for OID4VCI's `verify-sdjwt`, not a new crypto path.
3. A response/callback shape (`direct_post` or `direct_post.jwt`) — pure
   OAuth2/OIDC transport plumbing, no FREK-ID semantics involved at all.

None of this touches `identity_engine`'s identity model, `.fk`'s
provenance model, or the Proof Engine/FREK-Chain — exactly the boundary
the founder's instruction names. Building it would be additive to
`backend/eudi/`, the same way OID4VCI itself was additive to `did/vc.py`.

## Why this pass does not build it

Every other scope decision this session made the same way (the SDK's own
documented "do not invent capacites" rule, the Permission Engine's
`ProtocolRole` mapping choosing documentation over new enum values, the
Agent Factory interface doc's own "PROPOSED, NOT IMPLEMENTED") rests on
the same test: **is there evidence of an actual consumer needing this
now?** For OpenID4VP, checked against every interoperability-facing
document this session has access to:

- `docs/interfaces/CVLN_WALLET.md` — describes identity/signature/wallet-
  linkage attestation only; does not mention presenting credentials to a
  third-party Verifier.
- `docs/interfaces/AGENT_FACTORY.md` — describes FREK-ID issuance for
  agents; no presentation-flow requirement named.
- `reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`'s own Credentials
  section — names OpenID4VP as `MISSING`, cites no waiting consumer.
- No EUDI/eIDAS conformance testing has been done against a real
  reference wallet (`reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`'s
  own explicit rule: "do NOT claim EUDI/eIDAS compatibility unless
  technically proven") — building a presentation flow with no reference
  wallet to test it against would produce exactly the kind of
  unverifiable, un-provable capability this mission's own rules
  repeatedly warn against claiming.

Building OID4VP now, with no named consumer and no way to conformance-
test it, would be scope invention — the same mistake this pass avoided
elsewhere (e.g., not adding `Issuer`/`Holder`/`Verifier` as enforceable
`Role` values with no route needing them).

## Classification

**DEFERRED, scoped and ready to pick up** — not `MISSING` in the sense of
"nobody has thought about it": the building blocks above are the actual
next steps, reusing existing verification code, once either (a) a real
consuming system (Wallet, an external Verifier partner) names a concrete
presentation-exchange requirement, or (b) the EUDI conformance-testing
gap closes enough that a presentation flow could be proven, not just
built. Tracked here so the next pass that picks this up does not have to
re-derive the boundary or re-discover that OID4VCI's existing verifier
code is the reusable foundation.
