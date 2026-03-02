1. Verify loader head discovery is already data-driven
- Confirm `training_inference` builds the smell-to-head map from dataset `smell_name` values, not a hardcoded 46 list.
- This determines whether code changes are needed in the core loader or only in notebook assumptions.

2. Remove 46-only assumptions from training code
- Find and remove any:
  - `== 46` assertions
  - `46h` naming conventions
  - comments or config text that assume 46 fixed heads
- Replace with dynamic logic based on the loaded smell map size.

3. Regenerate and freeze the combined config
- Use the combined dataset root (`datasets`)
- Use the combined config file (the one that includes both 46 and module complexity)
- Treat that config as the single source for the 60-head training run.

4. Confirm the actual head set before training
- Load the combined config
- Enumerate unique `smell_name` values
- Save/export the exact ordered mapping:
  - `smell_name -> head_id`
- This prevents accidental drift if datasets change later.

5. Update model construction to use the discovered count
- Ensure `SharedEncoderSmellHeads` (or equivalent model builder) receives:
  - `num_smells = len(smell_to_head)`
- For this run, that should resolve to `60`.

6. Check checkpoint compatibility rules
- A 46-head checkpoint cannot be reused as-is for a 60-head routed output unless you explicitly remap/expand heads.
- Decide one of:
  - fresh training from base encoder
  - partial load of shared encoder weights only, with new head layers initialized fresh
- Do not silently load a 46-head full checkpoint into a 60-head model.

7. Persist the 60-head label schema with the run
- Save alongside training outputs:
  - `smell_to_head`
  - `head_to_smell`
- This is required so inference uses the exact same routing schema later.

8. Update inference to require schema match
- Inference code should validate that:
  - the loaded checkpoint¡¯s head mapping
  - matches the runtime dataset / expected smell map
- Fail fast if a 46-head mapping is used against a 60-head model or vice versa.

9. Keep severity out of scope for this extension
- Extending to 60 heads is only about:
  - adding 14 new routed smell labels
- Do not mix in severity prediction in the same step.

10. Validate the combined dataset before training
- Confirm:
  - combined config loads all 27 datasets
  - 60 unique smells are present
  - no missing excerpt/sidecar paths
  - module-complexity entries are included in the smell map

11. Update documentation
- Update training notes / notebook comments to say:
  - current run uses 60 heads
  - head count is data-driven
  - combined config file is the source of truth

12. Run a dry initialization check
- Build dataset
- build smell map
- construct model
- print:
  - head count
  - first few and last few smell names
- This catches any mismatch before actual training starts
