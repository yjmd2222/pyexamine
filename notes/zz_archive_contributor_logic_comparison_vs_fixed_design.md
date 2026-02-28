# Comparison: My Contributor Logic vs "고정 설계 보고서"

Date: 2026-02-21
Compared artifacts:
- My note: `notes/contributor_extraction_logic.md`
- User-provided fixed design text (type-query removed, Role0-driven anchors)

## 1) Head/query architecture

Fixed design:
- No type query `type(tau)`.
- 46-head routing already fixes smell type.
- Query slots are only `(object, instance, role)`.

My previous note:
- Did not explicitly enforce query-level removal of type query.
- Focused on extraction schema and detector-side contributors.

Result:
- Partial mismatch. Fixed design is stricter and should be treated as canonical.

## 2) Anchor contract

Fixed design:
- `anchor_lines` must come only from Role0 (ANCHOR_SET).
- If Role0 mask is empty, object/slot is dropped.
- Anchor cannot be independently predicted.

My previous note:
- Role0 described as core contributor, but not stated as hard anchor-only source.
- Some smells placed core evidence in Role0 instead of placing anchor entity in Role0.

Result:
- Mismatch. Must adopt Role0-only anchor contract.

## 3) ROLE1/ROLE2 direction conventions

Fixed design examples:
- Hub-like, Unstable: Role1=outgoing, Role2=incoming(list_by_file)
- DIT, Fan-in: Role2 used for connected/list_by_file context

My previous note:
- For Hub-like/Unstable I had Role0=outgoing and Role1=incoming.
- For DIT I had Role0=path spans, Role1/2 optional split.

Result:
- Mismatch in direction/role placement for several connected smells.

## 4) Smell recipe granularity

Fixed design:
- Role assignment is recipe-first and inference-friendly.
- Role0 is generally anchor header/range; Role1/2 are evidence/context.

My previous note:
- More metric-first (threshold contributor centric).
- Some smells used evidence-heavy Role0 where fixed design expects class/file anchor in Role0.

Result:
- Different emphasis. Fixed design should drive final labeling recipes.

## 5) Detected/undetected stance

Fixed design text:
- Describes pointer/role extraction pipeline and deterministic postprocessing.
- Does not forbid undetected inclusion.

My previous note:
- Explicitly requires detected + undetected candidates and pre-threshold candidate emission.

Result:
- Compatible. Keep this requirement.

## 6) Concrete mismatches to fix (high impact)

1. Remove any dependency on type query in extraction design.
2. Enforce Role0-only anchor creation globally.
3. Re-map role directions for connected smells:
- Hub-like Dependency: Role0=file anchor, Role1=outgoing, Role2=incoming(list_by_file)
- Unstable Dependency: Role0=file anchor, Role1=outgoing, Role2=incoming(list_by_file)
- Deep Inheritance Tree: Role0=current class anchor, Role2=path list_by_file
- High Fan-in: Role0=target module anchor, Role2=incoming list_by_file
4. Recenter many class/file smells so Role0 is class/file anchor span.

## 7) What remains valid from my previous note

1. Candidate-first extraction for undetected + detected datapoints.
2. Threshold/metrics capture per datapoint.
3. Detector-internal provenance for contributors.
4. Need for explicit per-smell recipes and machine-readable contracts.

## 8) Final decision for this repo

Canonical logic to use going forward:
- Use the fixed design role contract as primary (`Role0=ANCHOR_SET` source for `anchor_lines`).
- Keep my candidate-first undetected extraction layer underneath.
- Build smell-specific recipe table according to fixed design role mapping.
