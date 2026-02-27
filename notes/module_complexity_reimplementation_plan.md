# Module Complexity Reimplementation Plan

## 1. First Step: Re-examine the Reference Repo and the ChatGPT Summary

Before any reimplementation work, re-read these two sources together:

- Reference repo: `C:\Users\jinmo\Downloads\pyexamine_anchor_key_fixed_ready`
- Summary note: `C:\Users\jinmo\Downloads\module_complexity_anchor_key_fix_summary.md`

This step is mandatory because the reference repo shows the current ChatGPT implementation, and the summary explains its intent. The goal here is not to copy it directly. The goal is to understand how it currently works, then redesign it so it matches our implementation style more closely and avoids regression in the existing 46-smell path.

## 2. Copied Sample Source

The reference sample tree has been copied into the current repo here:

- `master-thesis-materials/pyexamine/samples_module_complexity/`

This copied tree is the local source set for reimplementation and later verification.

## 3. Fixed Design Decisions

These are now fixed requirements for the reimplementation.

### 3.1 Thresholds are not required

Module complexity here is not being treated like a threshold-triggered smell detector.

Reason:

- cohesion and coupling are being modeled as level/class assignments
- the task is to assign the level and attach evidence
- not to decide “above threshold => detected” in the same style as many 46 smells

So the reimplementation should use:

- classification logic
- evidence extraction
- positive/negative candidate coverage in the dataset

But it does not need a threshold-style decision rule.

### 3.2 Coupling uses only observed interacting pairs

For coupling, the candidate universe is:

- only observed interacting module pairs

Pair existence should come from actual analyzed interaction evidence.

Allowed sources for pair existence:

- AST-derived interactions
- import relationships
- call relationships
- access relationships
- graph relationships derived from the analyzed source

Do not use all possible module pairs.

### 3.3 Coupling uses only ROLE0 and ROLE1

Coupling should be modeled as a relationship between two modules.

Use:

- `ROLE0` = evidence from one module in the pair
- `ROLE1` = evidence from the other module in the pair
- `ROLE2` = empty

There is no need for `ROLE2` in the current coupling design.

### 3.4 Cohesion uses ROLE0 and ROLE1

Cohesion is internal to one module.

Use:

- `ROLE0` = the module/file anchor span
- `ROLE1` = the internal evidence lines that justify the assigned cohesion level
- `ROLE2` = empty

`ROLE1` is required, because the dataset should show not only the module being classified but also the supporting internal evidence.

### 3.5 Output structure should remain the same shape as the current excerpt pipeline

Even though module complexity will have its own implementation modules, the produced output should keep the same shape as the current excerpt/sidecar outputs.

This means:

- same excerpt JSONL row shape
- same sidecar JSONL row shape
- same `[ROLE0]` / `[ROLE1]` / `[ROLE2]` section markers
- same token/label format
- same downstream loader expectations

Structurally, it should stay very similar to the current 46-style dataset flow.

## 4. How ChatGPT's Current Implementation Is Done

### 4.1 Report generation

ChatGPT added a separate builder:

- `src/dataset_generator/build_module_complexity_report.py`

It is outside the 46 detector subsystem.

It currently:

1. Reads a manifest:
   - `samples/module_complexity/LABELS/module_complexity_labels.json`
2. Analyzes project source under `src/` using AST + lexical heuristics
3. Emits module-complexity report rows

This means module complexity report generation is currently:

- manifest-guided
- heuristic evidence extraction
- separate from the 46 detector flow

### 4.2 Report row shape in ChatGPT's implementation

Cohesion rows are file-rooted and compatible with the existing excerpt pipeline:

- `name`
- `file_path`
- `start_line_number`
- `end_line_number`
- `evidence_lines`

Coupling rows are anchor-file oriented in ChatGPT's implementation:

- `name`
- `file_path`
- `start_line_number`
- `end_line_number`
- `outgoing_evidence_lines`
- `files[*].incoming_evidence_lines`

This works mechanically with the existing template-driven excerpt generator, but it models coupling as anchor-file plus related files, not as a pair relationship.

### 4.3 Excerpt generation in ChatGPT's implementation

ChatGPT reused the existing excerpt generator:

- `src/dataset_generator/build_role_section_excerpts.py`

It extended templates and pushed module-complexity report rows through the same shared pipeline.

### 4.4 The specific keying change ChatGPT made

In the anchor-key-fixed reference repo, ChatGPT changed `_candidate_key(...)` inside:

- `src/dataset_generator/build_role_section_excerpts.py`

It added a smell-specific exception so:

- `Module Cohesion - *`
- `Module Coupling - *`

are keyed as:

- `(smell_name, file_path)`

instead of using the normal key shape that includes root `start_line_number/end_line_number`.

That fix was added to stop duplicate true/false splits when the module-complexity report used cropped root spans.

## 5. What Must Be Corrected for Our Goal

Our goal is:

- module complexity dataset added
- report and excerpt structure still close to the existing system
- generation logic close in spirit to the 46 pipeline
- no regression risk in the shared 46 excerpt generator

Based on that goal, the current ChatGPT implementation is not the correct final design.

### 5.1 Wrong part: module-specific logic inside the shared excerpt generator

The wrong part is the smell-specific keying exception inside:

- `build_role_section_excerpts.py`

Why it is wrong for our goal:

- it changes shared generator behavior for a new feature
- it increases regression risk for the existing 46 path
- it solves a module-complexity problem by patching the shared core instead of isolating module-complexity behavior

### 5.2 Wrong part: coupling modeled as anchor-file instead of relationship pair

Coupling is between modules.

So the anchor-file + outgoing + incoming model is only a convenience shortcut.
It is not the preferred semantic model for this project.

For our reimplementation, coupling should be modeled as an observed module pair.

### 5.3 Root cause of the duplicate split

The duplicate true/false split happened because:

- ChatGPT used cropped root `start_line_number/end_line_number` in module-complexity report rows
- but the universe candidate identity in the shared file-centric generator did not line up with that root identity

That mismatch caused one semantic candidate to split into:

- one false row
- one true row

## 6. Corrected Reimplementation Direction

### 6.1 Keep module complexity isolated from the shared 46 excerpt core

Do not add module-complexity-specific behavior inside:

- `src/dataset_generator/build_role_section_excerpts.py`

This is mandatory.

The existing 46 excerpt generator should remain unchanged for module-complexity-specific concerns.

### 6.2 Use separate module-complexity files

This is mandatory.

Create separate module-complexity-specific files under `src/dataset_generator/`.

The module-complexity integration must live in separate `.py` files, not inside the shared generator.

### 6.3 Use pair-based coupling candidates without committing to directedness

For coupling, use canonical observed module pairs.

Do not commit to directedness unless absolutely required.

Use a canonical pair identity such as:

- sorted `(module_a, module_b)`

This avoids reversed duplicate pairs while keeping coupling as a true relationship.

### 6.4 Keep cohesion as file-based candidates

For cohesion, the candidate remains file/module based.

That is natural because cohesion is an internal property of one module.

## 7. Proposed Module Layout

Create separate module-complexity files under `src/dataset_generator/`:

1. `build_module_complexity_report.py`
- build raw module-complexity report rows from labels + source analysis

2. `build_module_complexity_excerpts.py`
- build excerpt JSONL + sidecar JSONL for module-complexity rows only
- handle cohesion file-universe synthesis
- handle coupling pair-universe synthesis
- emit the same output structure as the existing excerpt pipeline
- keep all module-complexity-specific candidate logic out of `build_role_section_excerpts.py`

3. `merge_reports.py`
- combine standard 46 report rows + module-complexity report rows when needed
- plain list concat only

This keeps module complexity isolated and avoids modifying the shared 46 excerpt core.

## 8. Detailed Reimplementation Plan

### Step 1. Rebuild the module-complexity builder locally

Use the copied local sample tree:

- `master-thesis-materials/pyexamine/samples_module_complexity/`

Port or rewrite:

- `build_module_complexity_report.py`

Initial goal:

- reproduce the current report-building heuristics from the reference implementation
- keep the analysis/evidence logic reusable
- do not carry over the shared-generator key hack

### Step 2. Define report row shapes for the corrected design

#### Cohesion report rows

Keep cohesion file-rooted.

Required fields:

- `name`
- `file_path`
- `start_line_number`
- `end_line_number`
- `evidence_lines`

Role mapping:

- `ROLE0` = root module span
- `ROLE1` = evidence lines
- `ROLE2` = empty

#### Coupling report rows

Model coupling as an observed module pair.

Required fields should be pair-oriented, not anchor-only.

Recommended shape:

- `name`
- `files`
  - first module entry with evidence lines
  - second module entry with evidence lines

Conceptually:

- `files[0]` = module A + evidence
- `files[1]` = module B + evidence

Role mapping:

- `ROLE0` = module A evidence
- `ROLE1` = module B evidence
- `ROLE2` = empty

This keeps coupling aligned with the pair concept while keeping the downstream output shape the same.

### Step 3. Do not use the shared excerpt generator for module-complexity candidate synthesis

Because coupling is pair-based, the existing shared generator is not the right place to synthesize the module-complexity universe.

Reason:

- the existing shared generator is file/class/method centered
- pair-universe generation for coupling is a module-complexity-specific concern
- pushing that into the shared generator would create exactly the regression risk we want to avoid

So:

- `build_role_section_excerpts.py` stays unchanged for module-complexity-specific logic
- `build_module_complexity_excerpts.py` becomes responsible for module-complexity candidate synthesis

### Step 4. Keep the output structure the same as the current excerpt/sidecar outputs

Even though module-complexity excerpt generation is moved to a separate module, the output format should remain the same shape:

- excerpt JSONL row:
  - `id`
  - `smell_name`
  - `is_detected`
  - `label_granularity`
  - `text`
  - `tokens`
  - `labels`

- sidecar JSONL row:
  - `id`
  - `smell_name`
  - `is_detected`
  - `label_granularity`
  - `token_map`

The point is to keep downstream training/inference compatibility unchanged.

### Step 5. Candidate synthesis rules

#### Cohesion

Universe:

- one candidate per module/file per cohesion level

Detected truth:

- report row present for that file + level

Undetected truth:

- all other file + cohesion-level combinations not present in the report

#### Coupling

Universe:

- one candidate per observed interacting canonical module pair per coupling level

Detected truth:

- report row present for that pair + level

Undetected truth:

- all other coupling-level assignments for that same observed pair not present in the report

Use canonical pair ordering to avoid reversed duplicates.

### Step 6. Preserve training compatibility in the existing shape

If we keep:

- same excerpt JSONL shape
- same sidecar shape
- same `smell_name`-driven routing style
- same BIO/O labeling style

then the training pipeline should remain structurally compatible.

Main thing to verify:

- pair-based coupling rows will contain two files in one example
- text packing, sidecar mapping, and source trace-back must correctly support both role sections

This is compatible in principle because the current role-section format already supports multi-file sections.

### Step 7. Verification requirements

Verification should check:

1. The shared `build_role_section_excerpts.py` has no module-complexity-specific branches added
2. Module-complexity excerpt generation works through its own separate module
3. Cohesion rows use `ROLE0` + `ROLE1`, with `ROLE2` empty
4. Coupling rows use `ROLE0` + `ROLE1`, with `ROLE2` empty
5. No duplicate semantic candidates exist for module-complexity rows
6. Canonical pair ordering prevents reversed duplicate coupling pairs
7. Existing 46 behavior remains unchanged

## 9. Additional Corrections to Watch

### 9.1 Coupling taxonomy mismatch

The reference labels file includes `message`, but the builder only implements:

- `data`
- `stamp`
- `control`
- `external`
- `common`
- `content`

So `message` is currently inconsistent and must be resolved by either:

- implementing it, or
- removing it from labels/specs

### 9.2 Keep sidecar/output structure unchanged

Do not invent a different dataset output format for module complexity.

Only the candidate synthesis module should differ. The output row shape should remain compatible with the current excerpt + sidecar convention.

## 10. Final Implementation Rule

Module complexity should be added as:

- a separate report-producing module
- a separate module-complexity excerpt-producing module
- with no module-complexity-specific logic embedded into the shared `build_role_section_excerpts.py`

This is the safest design and the one least likely to cause regression in the current 46 implementation.
