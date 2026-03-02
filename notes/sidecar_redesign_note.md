# Sidecar Redesign Note

## Your New Proposition (understanding)

The new proposition is to stop storing a large per-token sidecar map.

Instead:
- each excerpt block should carry enough structural information so its source origin is known
- the sidecar should scale with the number of excerpt blocks / excerpt sections, not with the number of tokens
- the sidecar can therefore be much smaller than the current token-level `token_map` design

The intended idea is:
- if each excerpt block has a deterministic source anchor and deterministic packed position,
- then token-to-source reconstruction can be derived later from the excerpt text itself,
- without storing a full source-metadata object for every token

This means the sidecar becomes:
- excerpt-level provenance
- not token-level provenance

## What this implies

To make this work correctly, the excerpt generator must guarantee:

1. Exact source-text preservation inside excerpt blocks
- No rewriting of code text.
- No normalization that changes characters.
- The excerpt body must remain an exact slice of the source file.

2. Deterministic excerpt boundaries
- Each `[FILE]` block / excerpt section must have a stable boundary in the packed text.
- The packed layout must be deterministic so offsets can be reconstructed later.

3. Source span anchoring per excerpt block
- Each excerpt block must record enough source metadata to reconstruct where the excerpt starts and ends in the original file.

4. Token offsets must remain derivable from the packed text
- If token-level sidecar is removed, the later tracer must be able to tokenize the packed excerpt text consistently and map token offsets back into the anchored source excerpt span.

## Where modifications are needed

### A. 46-smell excerpt generation

File:
- `master-thesis-materials/pyexamine/src/dataset_generator/build_role_section_excerpts.py`

Current behavior:
- builds verbose per-token `token_map`
- stores source metadata on many token entries

Needed redesign:
- stop emitting full per-token provenance as the primary sidecar payload
- emit excerpt-level records instead, for each rendered excerpt block / role section block
- preserve enough metadata to reconstruct source origin later

Likely modification points:
- the function that currently builds `text, tokens, labels, token_map, ...`
- the logic that writes sidecar rows
- any helper that computes char/token offsets for the current `token_map`

### B. Module-complexity excerpt generation

File:
- `master-thesis-materials/pyexamine/src/dataset_generator/build_module_complexity_excerpts.py`

Current behavior:
- reuses the same shared text/token/sidecar builder used by the 46 pipeline
- therefore inherits the same verbose token-level sidecar behavior

Needed redesign:
- once the shared excerpt-sidecar contract changes, this file must either:
  - adopt the same new excerpt-level sidecar structure, or
  - be explicitly adapted to emit the new smaller sidecar format

Because module complexity reuses the shared builder, this file may need only light updates if the shared sidecar contract is changed centrally.

### C. Training/inference sidecar tracing

Files:
- `master-thesis-materials/pyexamine/training_inference/inference_utils.py`
- future tracing helper(s) to be added under `master-thesis-materials/pyexamine/training_inference/`

Current behavior:
- no sidecar tracing implemented yet
- current plan assumed token-level `token_map`

Needed redesign:
- tracing logic must be designed against the new excerpt-level sidecar structure
- the tracer will need to reconstruct token-to-source by combining:
  - packed excerpt text
  - excerpt-level sidecar anchors
  - deterministic tokenization / offset logic

This is the point where the sidecar redesign directly affects the future tracing implementation.

## Main consequence

If this redesign is adopted:
- sidecar size can become much smaller
- but reconstruction logic moves from "read token_map directly" to "derive token mapping from excerpt-level anchors + text"

So this is a valid redesign, but it changes the excerpt/sidecar contract and the future tracing implementation together.
