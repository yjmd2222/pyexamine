# Module Complexity Reimplementation Plan

## 1. First Step: Re-examine the Reference Repo and the ChatGPT Summary

Before reimplementation, re-read these two sources together:

- Reference repo: `C:\Users\jinmo\Downloads\pyexamine_anchor_key_fixed_ready`
- Summary note: `C:\Users\jinmo\Downloads\module_complexity_anchor_key_fix_summary.md`

This is necessary because the current reference already shows how ChatGPT integrated module complexity, but the goal here is not to copy that design blindly. The goal is to compare it against our existing 46-smell implementation style and then reimplement it so the structure and generation behavior stay very similar to 46.

## 2. Copied Sample Source

As requested, the reference sample tree has been copied into the current repo here:

- `master-thesis-materials/pyexamine/samples_module_complexity/`

This copied tree should be treated as the local source set for reimplementation and verification.

## 3. How ChatGPT's Current Implementation Is Done

### 3.1 Report generation

ChatGPT added a separate builder:

- `src/dataset_generator/build_module_complexity_report.py`

It is not implemented inside the 46 detector subsystem. It is a separate builder that:

1. Reads a manifest:
   - `samples/module_complexity/LABELS/module_complexity_labels.json`
2. Analyzes project source under `src/` using AST + lexical heuristics
3. Emits module-complexity report rows

This means module complexity report generation is currently:

- manifest-guided
- heuristic evidence extraction
- separate from the 46 threshold detector flow

### 3.2 Report row shape

ChatGPT made the row shape compatible with the existing excerpt pipeline.

Cohesion rows:

- `name`
- `file_path`
- `start_line_number`
- `end_line_number`
- `evidence_lines`

Coupling rows:

- `name`
- `file_path`
- `start_line_number`
- `end_line_number`
- `outgoing_evidence_lines`
- `files[*].incoming_evidence_lines`

This shape is close enough to the current 46-style template-driven excerpt generator.

### 3.3 Excerpt generation

ChatGPT reused the existing excerpt generator path:

- `src/dataset_generator/build_role_section_excerpts.py`

It did not make a separate excerpt generator. Instead it extended templates and fed the module-complexity report rows into the same excerpt pipeline.

### 3.4 The specific keying change ChatGPT made

In the anchor-key-fixed reference repo, ChatGPT changed `_candidate_key(...)` inside:

- `src/dataset_generator/build_role_section_excerpts.py`

It added a smell-specific exception:

- `Module Cohesion - *`
- `Module Coupling - *`

These are keyed as:

- `(smell_name, file_path)`

instead of using the normal file key shape that includes root `start_line_number/end_line_number`.

That was done to stop duplicate semantic candidates (`false` + `true`) when the module-complexity report uses cropped root spans.

## 4. What Must Be Corrected for Our Goal

Our goal is not just “make duplicates disappear.”

Our goal is:

- module complexity dataset added
- report and excerpt structure very similar to 46
- generation logic very similar to 46
- avoid regression in existing 46 flow

Based on that goal, the current ChatGPT implementation is not the correct final design.

### 4.1 The wrong part

The wrong part is the smell-specific keying exception inside:

- `build_role_section_excerpts.py`

Why it is wrong for our goal:

- the existing 46 pipeline does not introduce a smell-specific identity exception like this
- it changes core excerpt behavior for new smells inside the shared 46 generator
- even if 46 behavior is not directly broken, it increases regression risk by modifying shared identity logic in the main generator

### 4.2 The real root problem

The real problem is not that module complexity needs a special key.

The real problem is:

- ChatGPT used cropped root `start_line_number/end_line_number` in module-complexity report rows
- but the excerpt universe candidate for file-rooted smells is effectively based on the canonical file candidate shape
- so report identity and universe identity diverged

That mismatch creates the extra true/false split.

### 4.3 The correct fix direction

The correct fix is:

- keep the normal excerpt generator keying behavior unchanged
- keep the same general 46-style report/excerpt structure
- fix module-complexity report generation so the root identity is stable and canonical

For file-rooted module-complexity smells, the root row should use:

- `start_line_number = 1`
- `end_line_number = total_lines + 1`

or the exact same canonical root span that the file-level universe candidate uses.

Then:

- root `start/end` remains part of identity just like normal file-rooted smells
- evidence stays in `evidence_lines` / `outgoing_evidence_lines` / `incoming_evidence_lines`
- no smell-specific key exception is needed

## 5. Reimplementation Requirements

### 5.1 Do not modify `build_role_section_excerpts.py` for module-complexity-specific behavior

This is mandatory.

Reason:

- the existing 46 path must remain isolated
- module complexity must not rely on smell-specific branching in the shared excerpt generator

The excerpt generator may be reused as-is, but module-complexity-specific logic must not be embedded there.

### 5.2 Make a separate module for module complexity

This is also mandatory.

Create a dedicated Python module for module-complexity integration, instead of writing logic inside:

- `src/dataset_generator/build_role_section_excerpts.py`

The separate module should own:

- module complexity report building
- any report normalization needed to align identity with the current excerpt generator
- any report merge step needed before excerpt generation

## 6. Proposed Module Layout

Create dedicated files under `src/dataset_generator/`:

1. `build_module_complexity_report.py`
- build raw module-complexity rows from labels + source analysis

2. `normalize_module_complexity_report.py`
- rewrite module-complexity root identity fields to canonical file-root spans
- keep cropped ranges only in evidence arrays
- this is the key file that fixes the current keying mismatch without touching the shared generator

3. `merge_reports.py`
- combine standard report rows + module-complexity rows when needed
- plain list concat, no identity logic inside the shared excerpt generator

This keeps module complexity isolated and avoids modifying the existing 46 excerpt core.

## 7. Detailed Reimplementation Plan

### Step 1. Rebuild the module-complexity builder locally

Use the copied local sample tree:

- `master-thesis-materials/pyexamine/samples_module_complexity/`

Port or rewrite:

- `build_module_complexity_report.py`

Initial goal:

- reproduce ChatGPT's current report row shapes
- do not yet change the AST/lexical heuristics unless necessary

### Step 2. Change root identity generation in the builder/normalizer

Do not use cropped anchor ranges as root identity.

For each module-complexity row:

- root `start_line_number/end_line_number` must be canonical file-level span
- cropped ranges remain only in evidence fields

Concretely:

Cohesion:

- root span: full file
- evidence: `evidence_lines`

Coupling:

- root span: full anchor file
- evidence:
  - `outgoing_evidence_lines`
  - `files[*].incoming_evidence_lines`

This preserves 46-like identity behavior.

### Step 3. Keep templates structurally aligned with 46-style excerpt generation

The module-complexity templates can stay in the same format already used by ChatGPT:

Cohesion:

- `ROLE0 = start_line_number/end_line_number`
- `ROLE1 = evidence_lines[*]`
- `ROLE2 = []`

Coupling:

- `ROLE0 = start_line_number/end_line_number`
- `ROLE1 = outgoing_evidence_lines[*]`
- `ROLE2 = files[*].incoming_evidence_lines[*]`

This is already compatible with the current excerpt generator and does not need smell-specific excerpt logic.

### Step 4. Leave `build_role_section_excerpts.py` unchanged for module-specific behavior

Reimplementation must verify that:

- no `_candidate_key(...)` special-case for module complexity is added
- no module-complexity branch is added in role span collection
- no module-complexity branch is added in dedupe/coverage logic

The shared generator should remain generic.

### Step 5. Add a local module-complexity report pipeline

The intended pipeline should be:

1. Generate standard 46 report (existing path)
2. Generate module-complexity report (new separate module)
3. Normalize module-complexity root identity if needed (new separate module)
4. Merge reports (new separate module)
5. Run existing excerpt generator on the merged report

That keeps the excerpt path identical in style to the current 46 pipeline.

### Step 6. Verify against the current 46-like expectations

Verification should check:

1. For module-complexity smells, no duplicate semantic candidate rows
2. For the same file-level candidate, exactly one truth value
3. Report row structure matches the existing template-driven excerpt expectations
4. Excerpt generator works without any module-specific branch in `build_role_section_excerpts.py`
5. Existing 46 behavior remains unchanged because the shared generator was not modified for module complexity

## 8. Additional Corrections to Watch

### 8.1 Coupling taxonomy mismatch

ChatGPT's labels file includes `message`, but the builder only implements:

- `data`
- `stamp`
- `control`
- `external`
- `common`
- `content`

So `message` is currently inconsistent and must be resolved by either:

- implementing it, or
- removing it from labels/specs

### 8.2 Keep sidecar/output structure unchanged

The output dataset structure should remain compatible with the existing excerpt + sidecar convention.

Do not invent a separate output format for module complexity.

## 9. Final Implementation Rule

Module complexity should be added as:

- a separate report-producing module
- with report rows normalized so they fit the current 46-style excerpt generator

It should not be added by patching special behavior into the shared excerpt generator core.

That is the safest design and the one least likely to cause regression in the current 46 implementation.
