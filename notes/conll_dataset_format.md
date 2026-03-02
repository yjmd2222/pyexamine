# Canonical CoNLL Dataset Format

This note documents the current canonical CoNLL artifact written into `cdatasets/`.

## Scope

- The canonical dataset artifact is the `.conll` file.
- It is intended to be human-readable and tokenizer-agnostic.
- The active CoNLL generators no longer emit a sidecar artifact.

## Sample Structure

- One sample is one contiguous block.
- One blank line separates samples.
- Each sample starts with metadata comment lines, followed by body rows.

Example:

```text
# id = 0
# smell_name = "Alternative Classes with Different Interfaces"
# is_detected = true
# label_granularity = "line"
# requested_label_granularity = "line"
# effective_label_granularity = "line"
# granularity_fallbacks = []
[ROLE0]	-100
[FILE]	-100
path=campus_event_planning/models.py#L51-L188	-100
class	B-ROLE0
EntryType1	I-ROLE0
:	I-ROLE0
[SEP_EXCERPT]	-100

```

## Body Columns

Body rows use exactly two columns:

1. `token`
2. `label`

The delimiter is a tab.

There is no `token_index` column in the canonical CoNLL output.

## Metadata Comment Headers

Current sample-level metadata is written as comment lines beginning with `#`.

Common headers:

- `id`
- `smell_name`
- `is_detected`
- `label_granularity`
- `requested_label_granularity`
- `effective_label_granularity`
- `granularity_fallbacks`

These headers are row metadata for the whole sample, not normal CoNLL columns.

## Structural Vocabulary

The canonical CoNLL stream keeps structural markers in-band. These markers are part of the vocabulary and appear in the `token` column.

Structural tokens:

- `[ROLE0]`
- `[ROLE1]`
- `[ROLE2]`
- `[FILE]`
- `[SEP_EXCERPT]`

Path marker:

- `path=<relative_path>#L<start>-L<end>`

Example:

- `path=campus_event_planning/models.py#L51-L188`

Meaning:

- `<relative_path>` is the project-relative file path shown in the packed excerpt.
- `L<start>` is the first source line included in that excerpt.
- `L<end>` is the last source line included in that excerpt.

The path marker is treated as a structural row and receives label `-100`.

## Label Vocabulary

Current label values in the `label` column are:

- `-100`
- `O`
- `B-ROLE0`
- `I-ROLE0`
- `B-ROLE1`
- `I-ROLE1`
- `B-ROLE2`
- `I-ROLE2`

Meaning:

- `-100` means the row should be ignored by loss computation. This is used for structural rows.
- `O` means the token is in the excerpt context but not inside an exact positive evidence line.
- `B-ROLE*` marks the first positive token on a positive source line for that role.
- `I-ROLE*` marks subsequent positive tokens on the same positive source line for that role.

The current implementation is line-granularity-first:

- positive labeling is derived from whether the token's source line is inside an exact evidence span
- context lines may appear in the excerpt, but they are labeled `O`

## Tokens That Do Not Appear In Canonical CoNLL

The canonical CoNLL stream does not emit the older synthetic whitespace/control pseudo-tokens:

- `[NL]`
- `[INDENT:...]`
- `[DEDENT]`

Those are intentionally excluded from the canonical artifact.

## Practical Parsing Rules

When reading the `.conll` file:

- read comment lines as sample metadata
- read `token<TAB>label` rows as the canonical sequence
- treat a blank line as the end of the sample
- reconstruct role/file state from structural tokens as they appear

This means downstream readers can recover section boundaries without adding extra columns such as `section` or `file_id`.
