## Token Granularity Status: 46 vs Module Complexity

### Verified current state

- For the current 46 per-project datasets under `master-thesis-materials/pyexamine/datasets`:
  - line and token `labels` arrays are **not** exactly the same
  - token entity count (`B-*` count) is **greater than or equal to** line for all checked projects
  - in practice, token entity count is much larger than line
  - this means the 46 pipeline currently has real token-level refinement

- For the current module-complexity per-project datasets under `master-thesis-materials/pyexamine/datasets_module_complexity`:
  - line and token `labels` arrays are **exactly the same**
  - token entity count equals line entity count for all checked projects
  - this means module-complexity token output currently differs only in metadata (`label_granularity` etc.), not in actual label behavior

### Practical conclusion

- Module-complexity token generation is currently only a structural output mode.
- True token-specific labeling for module complexity is **not implemented yet**.
- This is different from the existing 46 token behavior and should be treated as an implementation gap.

### Implication

- If module complexity is expected to match the 46 standard, module-complexity token labeling needs its own real token-level logic instead of reusing the same contributor spans unchanged.
