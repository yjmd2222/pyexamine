# CoNLL Branch Completion Plan

## Purpose

This note captures the current branch direction and the remaining path to a complete end-to-end system.

Original repo purpose:
- generate project smell reports from source code

Current `conll` branch purpose:
- generate canonical CoNLL datasets from smell reports
- train token classifiers on those CoNLL datasets
- eventually run inference and regenerate report-like outputs from model predictions

This note is based on the current repo contents, with special care to avoid treating deprecated files as the active workflow.

## Current Active Workflow

The best current source of truth is:
- `runcommands.md`

Current active sequence:

1. Generate 46-smell reports into `creports/`
2. Generate module-complexity reports into `creports_module_complexity/`
3. Convert those reports into canonical CoNLL files under `cdatasets/<project>/role_section_excerpts.line.conll`
4. Generate a strict CoNLL dataset manifest at `training_inference/conll_dataset_paths.config.json`
5. Train using the CoNLL-native training path

Active code paths:
- `src/code_quality_analyzer/main.py`
- `src/dataset_generator/build_role_section_excerpts.py`
- `src/dataset_generator/build_module_complexity_report.py`
- `src/dataset_generator/build_module_complexity_excerpts.py`
- `training_inference/conll_data_utils.py`
- `training_inference/model_pipeline.py`
- `training_inference/train_loop.py`
- `training_inference/train_modernbert_routed_conll.ipynb`

## Important Current Reality

The branch is already CoNLL-first for dataset generation.

The active excerpt generators now:
- write CoNLL, not JSONL
- support line granularity only in the primary path
- do not emit active sidecar files

This means the real unresolved work is not basic dataset generation.

The major unfinished area is:
- post-inference reconstruction of source spans and report rows from predicted BIO labels

## Deprecated Or Misleading Paths

These should not drive the main plan unless deliberately revived.

### 1. Legacy JSONL + sidecar flow

Files:
- `training_inference/data_utils.py`
- `training_inference/dataset_paths.config.json`
- `training_inference/dataset_paths.config46AndComplexity.json`
- `src/dataset_generator/depr_build_role_section_excerpts_jsonl.py`
- `src/dataset_generator/depr_build_module_complexity_excerpts_jsonl.py`

Status:
- legacy training/inference path
- still useful as historical reference
- some deprecated helpers are still imported internally by the active CoNLL generators

Important:
- these files are not safe to delete blindly because some active code still reuses helper functions from deprecated modules

### 2. Old or stale inference notebook

File:
- `training_inference/infer_modernbert_routed_46heads.ipynb`

Problem:
- still uses the legacy JSONL dataset path config
- not aligned with the new CoNLL-native generation path

### 3. Stale `pyexamine` CLI wrappers

File:
- `src/pyexamine/__main__.py`

Problem:
- some subcommands point to module names that no longer exist as active non-deprecated entry points
- this file is not a trustworthy facade for the actual current workflow

### 4. Stale docs

Files:
- `training_inference/STRICT_DATASET_STRUCTURE.md`
- `notes/active_command_scope.md`

Problem:
- they still describe the strict JSONL flow more than the actual CoNLL-first workflow

## What Already Exists

### A. Report generation

Working pieces:
- 46-smell report generation via `code_quality_analyzer.main`
- module-complexity report generation via `build_module_complexity_report`

Outputs:
- `creports/*.json`
- `creports_module_complexity/*.module_complexity_report.json`

### B. CoNLL dataset generation

Working pieces:
- `build_role_section_excerpts.py`
- `build_module_complexity_excerpts.py`

Behavior:
- emits canonical line-level CoNLL blocks
- includes structural in-band markers such as `[ROLE0]`, `[FILE]`, `[SEP_EXCERPT]`
- includes `path=...#Lx-Ly` markers for source anchoring

### C. CoNLL dataset loading

Working pieces:
- `training_inference/conll_data_utils.py`
- `training_inference/generate_conll_dataset_paths_config.py`

Behavior:
- validates strict per-project CoNLL structure
- merges per-project CoNLL files into training examples
- creates train/val/test splits

### D. Training

Working pieces:
- `training_inference/model_pipeline.py`
- `training_inference/train_loop.py`
- `training_inference/train_modernbert_routed_conll.ipynb`

Behavior:
- shared encoder + smell-specific routed heads
- validation metrics and checkpoint saving already exist

### E. Raw inference

Working pieces:
- `training_inference/inference_utils.py`

Behavior:
- can emit predicted BIO labels for each example

Limitation:
- does not reconstruct source locations
- does not regenerate final report rows

## Biggest Missing Piece

The main missing chain is:

1. model predicts BIO labels over CoNLL tokens
2. predicted positive BIO spans must be mapped back to source files and source lines
3. traced source spans must be converted into report rows
4. regenerated reports must be benchmarked against gold `creports*`

This post-inference half is not finished as active code.

## Completion Plan

### Phase 1. Freeze the canonical workflow

Goal:
- establish one unambiguous supported path

Tasks:
- treat `runcommands.md` as the canonical generation sequence
- update stale docs so they no longer imply JSONL-sidecar is the main path
- decide whether `src/pyexamine/__main__.py` should be repaired or explicitly documented as non-canonical

Done when:
- a new reader can identify the supported pipeline without guessing

### Phase 2. Add generation validation

Goal:
- make report and CoNLL generation reliable and auditable

Tasks:
- add a smoke workflow that runs:
  - `creports` generation
  - `creports_module_complexity` generation
  - `cdatasets` generation
  - CoNLL config generation
- validate:
  - expected files exist
  - no empty report files
  - no empty CoNLL files
  - each CoNLL file is parseable as sample blocks

Done when:
- generation failures are caught before training starts

### Phase 3. Lock training to the CoNLL-native path

Goal:
- make CoNLL training the clear supported training path

Tasks:
- treat `train_modernbert_routed_conll.ipynb` as canonical
- add one scriptable non-notebook training entry point using:
  - `create_conll_dataset_build`
  - `create_tokenizer`
  - `PretokenizedSmellDataset`
  - `TokenClassificationCollator`
  - `train_model`
- define a stable output structure for:
  - checkpoints
  - split manifests
  - metrics
  - training metadata

Done when:
- training can be repeated without depending on manual notebook edits

### Phase 4. Build a CoNLL-native inference path

Goal:
- inference should use the same CoNLL dataset contract as training

Tasks:
- replace or supersede `infer_modernbert_routed_46heads.ipynb`
- create a CoNLL-native inference notebook or script
- load datasets via `create_conll_dataset_build(...)` or a split-specific variant
- ensure inference outputs carry enough identity to trace back to original dataset samples

Recommended output fields:
- global example id
- source dataset path
- source local sample id
- smell name
- predicted labels
- optional probabilities

Done when:
- inference no longer depends on the old JSONL config path

### Phase 5. Implement CoNLL prediction tracing

Goal:
- map predicted BIO labels back to source spans without sidecars

Why this is possible:
- the canonical CoNLL format embeds structure in-band
- the active dataset format includes:
  - role markers
  - file markers
  - path-and-line anchors

Tasks:
- build a parser that reads predicted token sequence together with the original CoNLL token sequence
- track current:
  - role section
  - file block
  - anchored file path
  - anchored excerpt line window
- extract predicted positive spans for `ROLE0`, `ROLE1`, `ROLE2`
- map those spans to source line spans
- merge adjacent source spans by role and file

Important constraint:
- this should not rely on the old sidecar design

Done when:
- a prediction record can be converted into grouped source spans per role

### Phase 6. Regenerate report rows from traced spans

Goal:
- convert traced predictions into report-like JSON rows

Tasks:
- define a deterministic conversion from traced spans to final report schema
- match the existing report shape used in:
  - `creports/*.json`
  - `creports_module_complexity/*.module_complexity_report.json`
- decide how to set fields not directly predicted by the model, especially:
  - severity
  - optional descriptions

Important note:
- the model currently predicts token labels, not severity
- severity likely needs either:
  - deterministic fallback logic, or
  - a deliberately fixed placeholder policy

Done when:
- model outputs can be transformed into JSON report artifacts comparable to gold reports

### Phase 7. Build benchmarking

Goal:
- measure whether regenerated reports are useful

There are two distinct benchmark layers.

#### A. Token-level benchmark

Use the existing training metrics:
- token accuracy
- micro F1
- non-`O` micro F1
- seqeval BIO metrics

This already mostly exists in:
- `training_inference/metrics_utils.py`
- `training_inference/train_loop.py`

#### B. Report-level benchmark

This appears to be missing as active code.

Tasks:
- compare regenerated reports against gold `creports*`
- measure:
  - smell-row presence match
  - file match
  - line overlap / span overlap
  - role-level span agreement

Done when:
- it is possible to say whether the model reproduces useful report structure, not just token labels

### Phase 8. Add regression tests for the new path

Goal:
- protect the active CoNLL pipeline

Current state:
- existing tests are mostly detector-focused
- there is no visible active test suite for the new end-to-end CoNLL inference pipeline

Needed tests:
- CoNLL parsing tests
- CoNLL tracing tests
- report regeneration tests
- report-level benchmarking tests

Done when:
- refactors in generation or inference do not silently break the end-to-end path

### Phase 9. Cleanup and explicit deprecation boundaries

Goal:
- reduce confusion for future work

Tasks:
- mark which notebooks are canonical
- mark which notebooks are historical only
- clearly label JSONL-sidecar configs as legacy if they remain in the repo
- avoid deleting deprecated helper files until active imports are removed

Done when:
- the repo has one obvious path and legacy files are visibly legacy

## Definition of Completion

This branch can be considered complete when all of the following are true:

1. A documented command chain generates:
   - `creports`
   - `creports_module_complexity`
   - `cdatasets`
   - `training_inference/conll_dataset_paths.config.json`

2. A canonical training path runs on CoNLL and produces:
   - checkpoints
   - metrics
   - reproducible split metadata

3. A canonical inference path runs on CoNLL and produces raw prediction outputs

4. A tracing layer converts predictions into source spans without relying on sidecars

5. A regeneration layer converts traced predictions into report JSON outputs

6. A benchmark layer compares regenerated reports against gold reports

7. Stale JSONL-sidecar instructions no longer compete with the CoNLL-first workflow

## Recommended Implementation Order

The most practical order is:

1. Freeze docs and canonical workflow
2. Add generation validation
3. Make training scriptable outside the notebook
4. Replace the stale inference notebook with a CoNLL-native one
5. Implement CoNLL prediction tracing
6. Implement report regeneration
7. Implement report-level benchmarking
8. Add regression tests
9. Final cleanup

## Main Thought / Key Insight

The hidden complexity is not the training loop.

Training infrastructure already exists in a mostly reusable form.

The real unfinished engineering work is the post-inference path:

- prediction tracing
- report reconstruction
- report-level benchmarking

That is the part that converts this branch from "dataset + model experiment" into a complete report-generation pipeline.
