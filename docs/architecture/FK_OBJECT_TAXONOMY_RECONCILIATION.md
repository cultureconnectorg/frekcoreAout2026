# `.fk` Object-Type Taxonomy <-> FREK Registry Namespaces — Reconciliation

`reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`'s FREK Registry section flagged this as **PARTIAL**: "`frek.artist/track/album/work/certificate/organization/wallet/event` (Registry, new) vs. `.fk`'s `object_type` enum ... — these are two different taxonomies that were not reconciled into one." This document is that reconciliation. Per the founder directive: **no historical FREK semantics change** — `.fk`'s `OBJECT_TYPES` (`backend/fk/models.py`) is untouched, every existing `.fk` object and route behaves exactly as before.

## The finding: it was already half-reconciled by design, just never written down or checked

`backend/registry/schemas/v1/frek.work.schema.json` already exists (Phase 1) with this docstring: *"Oeuvre culturelle generique (superset de track/album/artwork/document) — miroir registry de backend/fk/models.py OBJECT_TYPES."* Its `work_type` enum is not merely "similar to" `.fk`'s `OBJECT_TYPES` — it is the **identical value set**: `song, album, event, heritage, photo, captation, document, artwork, other`. Nobody had verified this claim stayed true, or built anything that uses it. This pass does both:

- `backend/registry/fk_taxonomy.py` (new) — the mapping, as tested code, not just narrative.
- `backend/tests/test_registry_fk_taxonomy.py` (new) — `test_frek_work_type_enum_is_an_exact_mirror_of_fk_object_types` reads both `fk/models.py`'s `OBJECT_TYPES` and `frek.work.schema.json`'s `work_type` enum straight off disk and asserts they're the same set. If either file is ever edited without the other, this test fails immediately — the reconciliation stays a checked fact, not a report claim that silently rots.

## The mapping

| `.fk` `object_type` | Generic Registry mirror | Specific Registry namespace | Notes |
|---|---|---|---|
| `song` | `frek.work` (`work_type: "song"`) | **`frek.track`** | Naming mismatch is real and intentional, not an oversight: `.fk` calls this a "song" (its own historical term, preserved), the Registry's KORA-facing catalog namespace calls it a "track" (the music-industry/DSP term KORA's own domain uses, see `docs/interfaces/KORA.md`). Neither is renamed to match the other. |
| `album` | `frek.work` (`work_type: "album"`) | **`frek.album`** | Same term in both — no mismatch. |
| `event` | `frek.work` (`work_type: "event"`) | **`frek.event`** | Same term in both. `frek.event`'s own docstring explicitly disambiguates from the unrelated Event *Bus* (Bloc 7) — a third, different meaning of "event" this codebase carries. |
| `heritage` | `frek.work` (`work_type: "heritage"`) | *(none)* | No domain-specific Registry namespace exists for heritage objects. `backend/heritage/routes.py` (versioning/lineage) is a separate, unrelated module — this reconciliation does not touch it. |
| `photo` | `frek.work` (`work_type: "photo"`) | *(none)* | |
| `captation` | `frek.work` (`work_type: "captation"`) | *(none)* | French for "recording/capture" (e.g. a live performance capture) — this term is `.fk`'s own and is preserved, not translated or normalized. |
| `document` | `frek.work` (`work_type: "document"`) | *(none)* | |
| `artwork` | `frek.work` (`work_type: "artwork"`) | *(none)* | |
| `other` | `frek.work` (`work_type: "other"`) | *(none)* | |

**Reading the table**: every one of `.fk`'s 9 `object_type` values has at least one valid Registry home (`frek.work`, always); 3 of the 9 (`song`, `album`, `event`) additionally have a more specific namespace for consumers that only care about that particular shape (KORA for track/album, an event listing for event). This is not a strict 1:1 taxonomy merge — it is a documented, verified *n:m* mapping that keeps both vocabularies intact.

## What this pass does NOT do (deliberately, staying inside "reconcile, don't redesign")

- **Does not auto-create a Registry object when a `.fk` is created.** `fk_taxonomy.build_frek_work_mirror()` only *shapes* a payload — it is not called from `backend/fk/routes.py`, and `POST /api/v1/fk/create`'s behavior is completely unchanged by this pass. Wiring an automatic mirror would be a real behavior/write-amplification change (every `.fk` creation would also write a `registry_objects` row) that nothing in this session's scope asked for and that has open questions of its own (should it be synchronous or best-effort? does a mirror ever get updated if the `.fk` changes? who owns fixing drift between the two?) — left as a clearly-scoped, smaller future item, not decided here.
- **Does not rename or alias either taxonomy's terms.** `song`/`track`, `captation`, `heritage` etc. all keep their existing meaning in their existing system — per the founder directive's explicit instruction that FREK terminology is preserved, not normalized to generic vocabulary.
- **Does not add `fk_object_ref` to the schemas that lack it.** `frek.track` and `frek.work` both already have an `fk_object_ref` field (pointing back at the `.fk` container); `frek.album`, `frek.event`, and the other namespaces do not. This is a real, minor asymmetry, noted here for whoever picks up the "auto-mirror" follow-up above, but adding fields to schemas already in production use is a real (if low-risk, additive) change this document does not make unilaterally.

## Evidence

- `backend/registry/fk_taxonomy.py` — the mapping.
- `backend/tests/test_registry_fk_taxonomy.py` — 24 tests, all passing: the enum-equivalence proof, every `object_type`'s namespace list, every named namespace's real existence in the schema catalog, and `build_frek_work_mirror()`'s output validating against the real `frek.work` JSON Schema (not just asserted by eye).
