# Sample Excerpt and Sidecar (Redesign)

## Purpose

This note shows a concrete example of:
- the excerpt row shape
- the smaller excerpt-level sidecar shape

The point is to illustrate the redesign where sidecar scales with excerpt blocks, not with every token.

## Sample Excerpt Row

```json
{
  "id": 131,
  "smell_name": "Feature Envy",
  "is_detected": true,
  "label_granularity": "token",
  "text": "[ROLE0]\n[FILE]\npath=log_analyzer/duplicates.py\n\ndef _template(entry, flag, tag, weight, source):\n    result = []\n    result.append(str(entry).strip())\n    result.append(str(flag).strip())\n    result.append(str(tag).strip())\n    result.append(str(weight).strip())\n    result.append(str(source).strip())\n    result.append(\"ok\")\n    return \":\".join(result)\n\n\ndef normalize_a(entry, flag, tag, weight, source):\n[SEP_EXCERPT]\n\n[ROLE1]\n[FILE]\npath=log_analyzer/duplicates.py\n\ndef _template(entry, flag, tag, weight, source):\n    result = []\n    result.append(str(entry).strip())\n    result.append(str(flag).strip())\n    result.append(str(tag).strip())\n    result.append(str(weight).strip())\n    result.append(str(source).strip())\n    result.append(\"ok\")\n    return \":\".join(result)\n[SEP_EXCERPT]\n\n[ROLE2]\n\n\n",
  "tokens": [
    "[ROLE0]",
    "[FILE]",
    "path=log_analyzer/duplicates.py",
    "def",
    "_template(entry,",
    "flag,",
    "tag,",
    "weight,",
    "source):",
    "result",
    "=",
    "[]",
    "result.append(str(entry).strip())",
    "result.append(str(flag).strip())",
    "result.append(str(tag).strip())",
    "result.append(str(weight).strip())",
    "result.append(str(source).strip())",
    "result.append(\"ok\")",
    "return",
    "\":\".join(result)",
    "def",
    "normalize_a(entry,",
    "flag,",
    "tag,",
    "weight,",
    "source):",
    "[SEP_EXCERPT]",
    "[ROLE1]",
    "[FILE]",
    "path=log_analyzer/duplicates.py",
    "def",
    "_template(entry,",
    "flag,",
    "tag,",
    "weight,",
    "source):",
    "result",
    "=",
    "[]",
    "result.append(str(entry).strip())",
    "result.append(str(flag).strip())",
    "result.append(str(tag).strip())",
    "result.append(str(weight).strip())",
    "result.append(str(source).strip())",
    "result.append(\"ok\")",
    "return",
    "\":\".join(result)",
    "[SEP_EXCERPT]",
    "[ROLE2]"
  ],
  "labels": [
    -100,
    -100,
    -100,
    "O",
    "O",
    "O",
    "O",
    "O",
    "O",
    "O",
    "O",
    "O",
    "B-ROLE0",
    "I-ROLE0",
    "I-ROLE0",
    "I-ROLE0",
    "I-ROLE0",
    "I-ROLE0",
    "O",
    "B-ROLE0",
    "O",
    "O",
    "O",
    "O",
    "O",
    "O",
    -100,
    -100,
    -100,
    -100,
    "O",
    "O",
    "O",
    "O",
    "O",
    "O",
    "O",
    "O",
    "O",
    "B-ROLE1",
    "I-ROLE1",
    "I-ROLE1",
    "I-ROLE1",
    "I-ROLE1",
    "I-ROLE1",
    "O",
    "O",
    -100,
    -100
  ]
}
```

## Sample Smaller Sidecar Row

This is the redesigned sidecar idea.

Instead of one `token_map` entry per token, store excerpt-level blocks with enough source anchors to reconstruct later.

```json
{
  "id": 131,
  "smell_name": "Feature Envy",
  "label_granularity": "token",
  "excerpt_blocks": [
    {
      "role": "ROLE0",
      "block_index": 0,
      "packed_char_start": 0,
      "packed_char_end": 404,
      "file_path": "log_analyzer/duplicates.py",
      "source_start_line": 2,
      "source_start_col": 0,
      "source_end_line": 13,
      "source_end_col": 0,
      "source_span_start_line": 2,
      "source_span_end_line": 13
    },
    {
      "role": "ROLE1",
      "block_index": 0,
      "packed_char_start": 420,
      "packed_char_end": 770,
      "file_path": "log_analyzer/duplicates.py",
      "source_start_line": 2,
      "source_start_col": 0,
      "source_end_line": 11,
      "source_end_col": 0,
      "source_span_start_line": 2,
      "source_span_end_line": 11
    }
  ]
}
```

## What this sample means

- `excerpt_blocks` is the proposed replacement for a huge per-token `token_map`.
- Each block records:
  - which role section it belongs to
  - where that block sits in the packed excerpt text
  - where that block came from in the source file
- Later tracing would reconstruct token-to-source by:
  - tokenizing the packed excerpt text
  - locating which excerpt block each token belongs to
  - mapping token offsets back into that block's anchored source span

## Important constraint

This smaller sidecar only works correctly if the excerpt text inside each block is preserved exactly from source, so reconstruction remains deterministic.
