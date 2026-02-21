# Contributor Extraction Logic (Reanswered, Fixed-Design Aligned)

This is the re-answer to the previous question, aligned to the pasted "고정 설계 보고서".

Core commitments:
1. 46-head routing: smell type is fixed by head id; no type-query prediction.
2. Anchor generation is Role0-only (ANCHOR_SET).
3. Datapoints include detected + undetected candidates.
4. Each datapoint records smell type, detected flag, ROLE0/ROLE1/ROLE2 contributors.

## A) Global extraction protocol

Step 1: Build candidate objects per smell from detector internals (same loops as `detect_*`).
Step 2: Compute smell metrics and evaluate threshold predicate.
Step 3: Populate ROLE0/1/2 spans using smell recipe below.
Step 4: Set `detected = predicate_result`.
Step 5: Generate packed excerpts from ROLE spans.
Step 6: Label tokens per role query slots `(object, instance, role)`.
Step 7: Derive `anchor_lines` only from Role0 masks.
Step 8: Drop candidate instance if Role0 is empty.

## B) Hard contract: anchor from Role0 only

- `AnchorTokens[o] = OR_{i}(Mask[q(o,i,Role0)])`
- `anchor_lines = merge(sidecar_map(AnchorTokens[o]))`
- If Role0 has no positive tokens/spans for candidate `o`, candidate is removed.

No separate anchor predictor is allowed.

## C) Datapoint schema (aligned)

```json
{
  "smell_head": "deep-inheritance-tree",
  "what_smell": "deep-inheritance-tree",
  "detected": true,
  "entity_id": "habits.HabitAnnual",
  "base_file": "samples/habit_tracker_reminders/habits.py",
  "thresholds": {"DIT_THRESHOLD": 3},
  "metrics": {"dit": 5},
  "role0": [{"file": "...", "start": 24, "end": 27, "kind": "anchor"}],
  "role1": [],
  "role2": [{"file": "...", "start": 1, "end": 7, "kind": "path_class"}],
  "anchor_lines": [{"file": "...", "start": 24, "end": 27}]
}
```

## D) Smell recipes (ROLE0/1/2)

The mapping below follows your pasted fixed design.

### Code (21)
1. Long Method: R0=function/method span, R1=empty, R2=empty
2. Large Class: R0=class span, R1=non-trivial method spans, R2=empty
3. Primitive Obsession: R0=function span, R1=signature/typed-param spans, R2=empty
4. Long Parameter List: R0=function span, R1=parameter-list signature spans, R2=empty
5. Data Clumps: R0=clump function/method signature spans (multi-anchor), R1=empty, R2=empty
6. Switch Statements: R0=if/elif chain span, R1=empty, R2=empty
7. Temporary Field: R0=class span, R1=temp-field assignment lines, R2=empty
8. Alternative Classes with Different Interfaces: R0=class header spans (multi), R1=public method signature spans, R2=empty
9. Potential Divergent Change: R0=class header/span, R1=evidence method spans, R2=empty
10. Parallel Inheritance Hierarchies: R0=class header spans (multi), R1=empty, R2=empty
11. Potential Shotgun Surgery: R0=call-site spans (`lines`), R1=empty, R2=empty
12. Excessive Comments: R0=comment-block spans, R1=empty, R2=empty
13. Duplicate Code: R0=duplicate block spans (`lines`), R1=empty, R2=empty
14. Data Class: R0=class span, R1=evidence method spans, R2=empty
15. Dead Code: R0=unused function span, R1=empty, R2=empty
16. Lazy Class: R0=class span, R1=empty, R2=empty
17. Speculative Generality: R0=class span, R1=evidence method spans, R2=empty
18. Feature Envy: R0=function span, R1=external access evidence spans, R2=empty
19. Inappropriate Intimacy: R0=related class header spans (multi), R1=evidence access spans, R2=empty
20. Message Chains: R0=chain attribute line/span, R1=empty, R2=empty
21. Middle Man: R0=class span, R1=delegating method spans, R2=empty

### Structural (17)
22. NOM: R0=class span, R1=method header spans, R2=empty
23. WMPC: R0=class span, R1=complex method spans, R2=empty
24. SIZE2: R0=class span, R1=field lines + public method headers, R2=empty
25. WAC: R0=class span, R1=weighted-contributor method spans, R2=empty
26. LCOM: R0=class span, R1=field-usage evidence spans, R2=empty
27. RFC: R0=class span, R1=method_call_lines spans, R2=empty
28. High Number of Classes per Module: R0=module/file span, R1=class evidence spans, R2=empty
29. DIT: R0=current class span, R1=empty, R2=inheritance path class spans (`files[*]`)
30. LOC: R0=file range span, R1=code evidence spans, R2=empty
31. MPC: R0=class span, R1=call-site evidence spans, R2=empty
32. CBO: R0=class span, R1=coupling evidence spans, R2=empty
33. High Number of classes per Project: R0=project class spans (`files[*]`, multi-anchor), R1=empty, R2=empty
34. High Cyclomatic Complexity: R0=method span, R1=empty, R2=empty
35. High Fan-out: R0=file span, R1=outgoing import evidence spans, R2=empty
36. High Fan-in: R0=target module/file span, R1=empty, R2=incoming import spans (`files[*]`)
37. Long File: R0=file range span, R1=empty, R2=empty
38. Too Many Branches: R0=method span, R1=empty, R2=empty

### Architectural (8)
39. Hub-like Dependency: R0=hub module/file span, R1=outgoing evidence spans, R2=incoming evidence spans (`files[*]`)
40. Scattered Functionality: R0=distributed function spans (`files[*]`, multi-anchor), R1=empty, R2=empty
41. Potential Redundant Abstractions: R0=overlap function spans (`files[*]`, multi-anchor), R1=empty, R2=empty
42. God Object: R0=class span, R1=public method evidence spans, R2=empty
43. Potential Improper API Usage: R0=module/file span, R1=api-call evidence spans, R2=empty
44. Orphan Module: R0=module/file range span, R1=empty, R2=empty
45. Cyclic Dependency: R0=cycle module file/header spans (multi-anchor), R1=cycle-forming import evidence spans (`files[*]`), R2=empty
46. Unstable Dependency: R0=target module/file span, R1=outgoing evidence spans, R2=incoming evidence spans (`files[*]`)

## E) Detected + undetected generation rule

For every smell candidate:
- always emit datapoint with ROLE spans + metrics + thresholds.
- if predicate true: `detected=true` and include report-instance id link if available.
- if predicate false: `detected=false` and keep same role extraction fields.

## F) Immediate implications for current codebase

Current `build_dataset.py` is detected-only and single BIO channel.
To match this design, add a contributor extraction layer that outputs per-candidate ROLE0/1/2 spans first, then build role-aware token labels from that layer.
