# Role Section Label Semantics (BIO/O)

Updated generator behavior in `src/dataset_generator/build_role_section_excerpts.py`:

- Structural tokens remain `-100`:
  - `[ROLE0]`, `[ROLE1]`, `[ROLE2]`, `[FILE]`, `path=...`, `[SEP_EXCERPT]`
- Code tokens are now labeled with BIO/O based on exact contributor spans (non-padded):
  - `B-ROLE0` / `I-ROLE0`
  - `B-ROLE1` / `I-ROLE1`
  - `B-ROLE2` / `I-ROLE2`
  - `O` for non-contributor code tokens (including context padding lines)

Important:
- Context lines from `--context-lines` are included in text but labeled `O` unless they overlap exact contributor spans.
- ROLE fallback excerpts may still render text, but if no exact role evidence exists, those tokens remain `O`.
