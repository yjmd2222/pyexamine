# Updated Labeling Policy and Implementation Plan

## Context
This updates the BIO labeling plan after clarifying that ROLE0 is not always a single strand.
ROLE0 can be multi-strand when templates/report define multiple disjoint exact spans.

## Source of Truth
- Exact ROLE spans from `templates_with_roles.json` + `code_quality_report.json` are the SSOT.
- Dataset labeling must follow these spans, not ad-hoc token heuristics.

## Role-Based Labeling Policy

### ROLE0
- ROLE0 is span-authoritative line BIO.
- Label the full exact ROLE0 span(s) as positive (`B-ROLE0/I-ROLE0`).
- Do **not** apply token-selector thinning inside ROLE0 spans.
- If ROLE0 has multiple disjoint spans, produce multiple ROLE0 strands (BIO restarts per span).

### ROLE1 / ROLE2
- ROLE1/ROLE2 may use token-level sparsification via smell-specific selectors.
- Selector outputs must stay within exact ROLE1/ROLE2 spans.
- If selector returns empty for a role instance, fallback to line-span BIO for that role instance.

## Non-Role Behavior
- Context padding outside exact spans is `O`.
- Structural markers are `-100`:
  - `[ROLE0]`, `[ROLE1]`, `[ROLE2]`, `[FILE]`, `path=...`, `[SEP_EXCERPT]`.

## Implementation Plan
1. Re-check per-smell role span contracts from templates/report.
2. In token mode, bypass selectors for ROLE0 and enforce span-BIO for ROLE0.
3. Keep selector logic for ROLE1/ROLE2 with fallback to line BIO.
4. Ensure BIO boundaries follow span segmentation (including disjoint spans).
5. Validate per smell (`is_detected=true/false` samples) and containment checks.
6. Re-run per-project line/token comparison after changes.

## Validation Criteria
- ROLE0 matches exact report/template spans, including multi-strand cases.
- ROLE1/ROLE2 positives remain inside exact role spans.
- No positives in padded context.
- Report detected entries are fully represented in JSONL detected rows.
