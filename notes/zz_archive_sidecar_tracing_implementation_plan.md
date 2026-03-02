**Purpose**

Implement sidecar tracing so inference outputs can be mapped back to original source code.

What this should do:

- take model predictions from excerpt rows
- use the matching sidecar row (`id`-joined)
- convert predicted token labels back into source locations
- recover:
  - file path
  - line range
  - column range if available
  - grouped spans per `ROLE0` / `ROLE1` / `ROLE2`

This is needed because the model predicts over packed excerpt tokens, not over raw source files directly.

**Current Excerpt Connection**

Current pipeline already gives the pieces, but they are not connected yet in `training_inference`.

What exists now:

1. Excerpt row
- in `role_section_excerpts.*.jsonl`
- includes:
  - `id`
  - `smell_name`
  - `tokens`
  - `labels`
  - `text`

2. Sidecar row
- in `role_section_excerpts.*.sidecar.jsonl`
- same `id`
- includes:
  - `token_map`
- `token_map` already carries source mapping metadata for non-structural tokens:
  - `file_path`
  - `source_line_start`
  - `source_col_start`
  - `source_line_end`
  - `source_col_end`
  - source span line info

3. Inference output
- produced by `training_inference/inference_utils.py`
- includes:
  - `id`
  - `pred_labels`
- but does not read sidecar yet

So the connection is:

- `inference record.id` -> `sidecar row.id`
- `pred_labels[token_idx]` -> `sidecar.token_map[token_idx]`

That join exists conceptually, but the code is not implemented.

**Resulting Output**

The new output should be a traced inference record, not just label strings.

Minimum useful traced output per record:

- `id`
- `smell_name`
- `pred_labels`
- `traced_roles`

Where `traced_roles` looks like:

```json
{
  "ROLE0": [
    {
      "file_path": "samples/foo/bar.py",
      "start_line": 10,
      "start_col": 4,
      "end_line": 12,
      "end_col": 18
    }
  ],
  "ROLE1": [],
  "ROLE2": []
}
```

Optional but useful additions:

- merged snippet text for each traced span
- token index ranges that produced the span
- separated raw token hits before merge

**Implementation Plan**

1. Define the trace contract
- Input:
  - inference JSONL row
  - sidecar JSONL row with same `id`
- Output:
  - role-grouped source spans derived from predicted labels

2. Build sidecar loader/index
- Add a helper to load sidecar JSONL into:
  - `id -> sidecar_row`
- Validate:
  - unique IDs
  - token_map present

3. Add predicted-label span extraction
- Parse `pred_labels`
- Extract contiguous BIO spans by role:
  - `B-ROLE0/I-ROLE0`
  - `B-ROLE1/I-ROLE1`
  - `B-ROLE2/I-ROLE2`
- Ignore:
  - `O`
  - structural `-100` positions if ever present in inference-aligned arrays

4. Map predicted token spans through `token_map`
- For each predicted token index:
  - read sidecar `token_map[token_idx]`
- Skip structural tokens:
  - `is_structural = true`
- Keep only mapped source-bearing tokens

5. Merge mapped tokens into source spans
- Merge adjacent predicted tokens when they belong to:
  - same role
  - same file
  - same source line / contiguous source region
- Preserve disjoint regions as separate spans

6. Return role-grouped traced spans
- Emit `ROLE0`, `ROLE1`, `ROLE2` lists
- Empty roles should be `[]`

7. Add an inference utility function
- Example shape:
  - `trace_predictions_with_sidecar(pred_records, sidecar_path) -> traced_records`
- Keep this outside notebook logic, in shared `.py`

8. Add save helper
- Save traced outputs as JSONL
- Do not overwrite raw inference output by default
- Use a separate file, e.g.:
  - `inference_test.traced.jsonl`

9. Add validation checks
- Verify:
  - prediction length matches sidecar `token_map` length
  - `id` exists in sidecar index
- Fail clearly on mismatch

10. Keep first version minimal
- First version should trace:
  - predicted labels only
  - to merged source spans
- Do not add snippet reconstruction or full report regeneration in the same step

**Important constraints**

- This should use existing sidecar `token_map` as source of truth.
- It should not attempt to re-tokenize source files.
- It should work for both:
  - 46 dataset
  - module complexity dataset
because both use the same excerpt/sidecar row structure.
