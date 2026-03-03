# Repo Boundary And `training_inference` Location

## Current Nested Structure

Current workspace structure:

- outer root: `encoder-bio`
- inside: `master-thesis-materials`
- inside: `pyexamine`

Current active work:
- `pyexamine` is the submodule currently being used for CoNLL dataset cleanup
- `pyexamine` also contains training scripts

Environment note:
- `.venv` exists at the outer root and is mainly used in WSL
- Windows work mostly uses conda

The environment location does not force any code move.
Keeping `.venv` at the outer root is normal and does not imply that `training_inference` is misplaced.

## Short Answer

The current location of `training_inference/` is acceptable.

It should stay inside `pyexamine` for now unless the intended long-term meaning of `pyexamine` is narrowed to only a reusable analyzer library.

## Core Issue

The main problem is not folder placement.

The real issue is unclear product boundary:
- what should `pyexamine` own?
- what should live outside it?

Right now, `pyexamine` already contains multiple layers:

1. rule-based analysis and report generation
2. dataset generation
3. training and inference work

That can be a valid design, but only if `pyexamine` is understood as the full end-to-end project rather than only a narrow analyzer package.

## Two Valid Interpretations Of `pyexamine`

### Option 1. `pyexamine` is the full end-to-end workflow project

In this interpretation, `pyexamine` owns:
- rule-based smell analysis
- report generation
- dataset generation
- model training
- model inference
- tracing / report reconstruction / benchmarking

If this is the intended direction, then keeping `training_inference/` inside `pyexamine` is coherent.

Why:
- it depends directly on `pyexamine` dataset contracts
- it depends directly on `pyexamine` smell taxonomy and report schema
- the planned unfinished work is tightly coupled to the CoNLL format generated here

Under this interpretation, the internal repo shape is conceptually:

- `src/code_quality_analyzer/`: rule-based analysis/report generation
- `src/dataset_generator/`: dataset and CoNLL generation
- `training_inference/`: ML training, inference, and later benchmarking/report reconstruction
- `notes/`: design notes and planning

This is a reasonable structure for a research or thesis-oriented workflow repo.

### Option 2. `pyexamine` is only the analyzer/package

In this interpretation, `pyexamine` should own only:
- rule-based code smell analysis
- report generation
- possibly dataset generation as a direct export layer

If this is the intended direction, then `training_inference/` should eventually move out of `pyexamine` and become a sibling project under `master-thesis-materials`.

Example conceptual structure:

- `pyexamine/`: analyzer + dataset generation
- another sibling project such as:
  - `smell_modeling/`
  - `report_learning/`
  - `smell_ml/`

Why:
- training/inference is a separate product concern
- it is not the same kind of reusable library functionality as the analyzer
- this separation makes `pyexamine` cleaner as a library/package boundary

## Recommendation

For the current stage, the better choice is:

- keep `training_inference/` inside `pyexamine`

Reasoning:

1. The active branch work is tightly coupled to `pyexamine` internals
- CoNLL files are generated here
- smell names and report schemas are defined here
- future tracing and report reconstruction will depend directly on the exact CoNLL contract

2. Moving it now would create churn without reducing complexity
- the main complexity is still unfinished functionality
- moving directories now mostly adds refactor cost and path churn

3. The missing work is strongly tied to this repo
- post-inference tracing
- report regeneration
- report-level benchmarking

Those are not generic training utilities yet.
They are project-specific extensions of the `pyexamine` pipeline.

## Practical Decision Rule

Use this rule when deciding whether something belongs inside `pyexamine`.

Keep it inside `pyexamine` if it depends on:
- `pyexamine` dataset schema
- `pyexamine` report schema
- `pyexamine` smell taxonomy
- `pyexamine` CoNLL contract

Move it to a sibling project only if it could reasonably be reused independently from these contracts.

By that rule, the current `training_inference/` directory still belongs inside `pyexamine`.

## What To Change First

The first cleanup should be conceptual, not physical.

Do not start by moving directories.

Instead:
- define what `pyexamine` is supposed to own
- document that ownership clearly
- then adjust structure later only if the ownership definition demands it

## Suggested Long-Term Framing

For now, the most useful framing is:

`pyexamine` is not just a report generator.

It is the full smell analysis and learned report-generation pipeline.

That framing makes the current placement of `training_inference/` make sense.

## Future Revisit Trigger

Revisit this decision later if one of these becomes true:

1. training/inference becomes reusable across multiple unrelated projects
2. the ML pipeline starts supporting inputs not generated by `pyexamine`
3. `pyexamine` needs to be maintained as a clean standalone library/package
4. you want a stricter packaging boundary for release or distribution

If none of those are true yet, keeping `training_inference/` in `pyexamine` is the more practical choice.
