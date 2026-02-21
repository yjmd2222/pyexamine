# Contributor Extraction Logic for Report-Generation Dataset

Scope:
- Source detectors: `master-thesis-materials/pyexamine/src/code_quality_analyzer/*_smell_detector.py`
- Output target: token-labeled excerpts with per-datapoint `smell`, `detected`, `ROLE0`, `ROLE1`, `ROLE2`
- Template reference: `master-thesis-materials/data/templates.json`

## 1) Dataset intent aligned to report generation
The analyzer pipeline is threshold-based:
1. Build aggregates/graphs/AST facts.
2. Compute smell-specific contributors (counts/ratios/paths/spans).
3. Compare against threshold(s).
4. If predicate true -> report row with evidence spans.

For learning report generation, datapoints must include:
- detected and undetected candidates
- all contributors used in threshold predicate
- evidence spans tied to contributor roles

## 2) Canonical datapoint schema (proposed)

```json
{
  "smell_name": "Deep Inheritance Tree (DIT)",
  "smell_slug": "deep-inheritance-tree",
  "category": "Structural",
  "detected": true,
  "entity_id": "habits.HabitAnnual",
  "base_file": "samples/habit_tracker_reminders/habits.py",
  "base_span": {"start": 24, "end": 27},
  "thresholds": {"DIT_THRESHOLD": 3},
  "contributors": {
    "role0": [{"file": ".../habits.py", "start": 1, "end": 7, "kind": "path_class", "value": "HabitBase"}],
    "role1": [{"file": ".../habits.py", "start": 9, "end": 12, "kind": "path_class", "value": "HabitDaily"}],
    "role2": []
  },
  "metrics": {"dit": 5, "path_len": 5},
  "predicate": "dit > DIT_THRESHOLD"
}
```

Notes:
- `entity_id` is the candidate key before thresholding (class/function/module/pair/project).
- `role0` = core contributor used directly in the main threshold condition.
- `role1` = first supporting contributor set (typically incoming/connected/context evidence).
- `role2` = second supporting contributor set (typically outgoing when both directions exist).
- For single-source smells, `role1/role2` may be empty.

## 3) Role semantics used consistently
- ROLE0 (core): evidence for the primary measured quantity (e.g., method spans for method-count smells, path class spans for DIT, repeated-call spans for API repetition).
- ROLE1 (support 1): secondary evidence that explains relation/context (usually incoming or connected file evidence).
- ROLE2 (support 2): tertiary evidence (usually outgoing direction where bidirectional dependency appears).

## 4) Detected extraction logic
Use report JSON normalized keys (`main.py` already normalizes):
- `instance_lines` -> default ROLE0
- `files[].instance_lines` -> ROLE1 unless smell says these are core path members (e.g., DIT/Cyclic/Redundant)
- `files[].incoming_instance_lines` -> ROLE1
- `outgoing_instance_lines` -> ROLE2
- `start_line_number/end_line_number` without evidence arrays -> ROLE0 as base span

## 5) Undetected extraction logic (critical)
Undetected datapoints do not exist in report JSON; they must be emitted from pre-threshold candidates.

Required extraction stage per detector:
1. Run same candidate loops as detector.
2. Compute same metrics used in `if` predicate.
3. Emit candidate regardless of predicate result.
4. Set `detected = predicate_result`.
5. Attach contributor spans for ROLE0/1/2 exactly as detector would for detected case.

Practical implementation point:
- Add per-smell `collect_<smell>()` helpers returning candidate objects with:
  - `entity_id`, `base_file`, `base_span`
  - `metrics`, `thresholds`, `predicate_result`
  - `role0_spans`, `role1_spans`, `role2_spans`
- `detect_<smell>()` becomes filter over collected candidates (`if predicate_result`).
- Dataset builder consumes all collected candidates (detected + undetected).

## 6) Smell-specific contributor map (46 smells)

Legend:
- Entity = candidate unit before threshold.
- Predicate = threshold condition.
- ROLE0/1/2 = contributor span groups for labeling.

### Code smells (21)
1. Long Method
- Entity: method/function node
- Predicate: effective_non_comment_lines > `LONG_METHOD_LINES`
- ROLE0: method/function span
- ROLE1: none
- ROLE2: none

2. Large Class
- Entity: class
- Predicate: non_trivial_method_count > `LARGE_CLASS_METHODS`
- ROLE0: class span + non-trivial method spans
- ROLE1: none
- ROLE2: none

3. Primitive Obsession
- Entity: method/function
- Predicate: primitive_count > `PRIMITIVE_OBSESSION_COUNT` AND primitive_ratio > `PRIMITIVE_RATIO_THRESHOLD`
- ROLE0: parameter declaration spans of primitive-typed args
- ROLE1: full function span (context)
- ROLE2: none

4. Long Parameter List
- Entity: method/function
- Predicate: parameter_count > adjusted(`LONG_PARAMETER_LIST`)
- ROLE0: parameter declaration spans
- ROLE1: function span
- ROLE2: none

5. Data Clumps
- Entity: repeated parameter combo across methods/functions
- Predicate: combo_occurrence >= `DATA_CLUMPS_THRESHOLD`
- ROLE0: all method/function spans containing the repeated combo
- ROLE1: combo parameter token spans within each method
- ROLE2: none

6. Switch Statements
- Entity: complex conditional block
- Predicate: branch/conditional complexity > `COMPLEX_CONDITIONAL`
- ROLE0: if/elif/except chain spans
- ROLE1: none
- ROLE2: none

7. Temporary Field
- Entity: class field usage profile
- Predicate: temporary-field score > `TEMPORARY_FIELD_THRESHOLD`
- ROLE0: class span + temporary field assignment/use spans
- ROLE1: none
- ROLE2: none

8. Alternative Classes with Different Interfaces
- Entity: class pair/group in same file
- Predicate: interface divergence score > `ALTERNATIVE_CLASSES_THRESHOLD`
- ROLE0: compared class spans
- ROLE1: differing method signature spans
- ROLE2: none

9. Potential Divergent Change
- Entity: class
- Predicate: grouped-change hotspots > `DIVERGENT_CHANGE_METHODS`
- ROLE0: evidence method spans matching divergent prefixes
- ROLE1: class span
- ROLE2: none

10. Parallel Inheritance Hierarchies
- Entity: class-pair chains
- Predicate: hierarchy similarity > `PARALLEL_INHERITANCE_SIMILARITY_THRESHOLD`
- ROLE0: paired class spans in parallel hierarchy
- ROLE1: inheritance relation anchors
- ROLE2: none

11. Potential Shotgun Surgery
- Entity: change target (method/call name)
- Predicate: call_count > `SHOTGUN_SURGERY_CALLS` AND contexts > `SHOTGUN_SURGERY_CONTEXTS`
- ROLE0: dispersed call-site spans
- ROLE1: context/container spans
- ROLE2: none

12. Excessive Comments
- Entity: file
- Predicate: comment_ratio > `EXCESSIVE_COMMENTS_RATIO` OR large_comment_blocks > `LARGE_COMMENT_BLOCKS`
- ROLE0: comment block spans
- ROLE1: file span
- ROLE2: none

13. Duplicate Code
- Entity: duplicated code block signature
- Predicate: duplicated_block_count >= `DUPLICATE_CODE_THRESHOLD` with min lines `DUPLICATE_CODE_MIN_LINES`
- ROLE0: duplicated block spans
- ROLE1: duplicate partner block spans
- ROLE2: none

14. Data Class
- Entity: class
- Predicate: behavior-to-data condition vs `DATA_CLASS_METHODS`
- ROLE0: field/member definition spans
- ROLE1: trivial/limited method spans
- ROLE2: none

15. Dead Code
- Entity: function
- Predicate: usage score < `DEAD_CODE_THRESHOLD`
- ROLE0: function span
- ROLE1: call/reference spans (often empty for dead code)
- ROLE2: none

16. Lazy Class
- Entity: class
- Predicate: class_loc < `LAZY_CLASS_LINES` AND effective_method_count < `LAZY_CLASS_METHODS`
- ROLE0: class span
- ROLE1: method spans (few/trivial)
- ROLE2: none

17. Speculative Generality
- Entity: class/abstraction
- Predicate: speculative score > `SPECULATIVE_GENERALITY_THRESHOLD` (plus unused parameter test `UNUSED_PARAMETERS_THRESHOLD`)
- ROLE0: abstract/placeholder member spans
- ROLE1: unused-parameter spans
- ROLE2: none

18. Feature Envy
- Entity: function/method
- Predicate: external_call_count > `FEATURE_ENVY_CALLS` AND external/local ratio > `FEATURE_ENVY_LOCAL_RATIO`
- ROLE0: external attribute-call spans (target object)
- ROLE1: local self-call spans
- ROLE2: none

19. Inappropriate Intimacy
- Entity: class pair
- Predicate: shared_member_count > `INAPPROPRIATE_INTIMACY_SHARED` AND overlap_ratio > `INAPPROPRIATE_INTIMACY_METHOD_RATIO`
- ROLE0: overlap/access spans from class A to class B members
- ROLE1: class A span
- ROLE2: class B span

20. Message Chains
- Entity: chained attribute expression
- Predicate: chain_length > `MESSAGE_CHAIN_LENGTH`
- ROLE0: chain expression/link spans
- ROLE1: enclosing function/class context span
- ROLE2: none

21. Middle Man
- Entity: class
- Predicate: delegation_ratio > `MIDDLE_MAN_RATIO` AND delegate_target_count <= `MIDDLE_MAN_MAX_DELEGATE_TARGETS`
- ROLE0: delegating method spans
- ROLE1: primary delegate target access spans
- ROLE2: class span

### Architectural smells (8)
22. Hub-like Dependency
- Entity: module node
- Predicate: dependency concentration + balance constraints using
  - `HUB_LIKE_DEPENDENCY_THRESHOLD`, `MIN_HUB_CONNECTIONS`, `HUB_MIN_PROJECT_MODULES`, `HUB_BALANCE_RATIO_MIN/MAX`
- ROLE0: outgoing import spans from hub module (`outgoing_instance_lines`)
- ROLE1: incoming import spans from other modules (`files[].incoming_instance_lines`)
- ROLE2: none

23. Scattered Functionality
- Entity: function name across modules
- Predicate: occurrence_count >= `MIN_SCATTERED_OCCURRENCES` with naming filters
- ROLE0: base function occurrence spans in anchor module
- ROLE1: other-module occurrences (`files[].instance_lines`)
- ROLE2: none

24. Potential Redundant Abstractions
- Entity: module pair/group
- Predicate: function-set similarity > `REDUNDANT_SIMILARITY_THRESHOLD` and min-function guards (`REDUNDANT_MIN_FUNCTIONS`)
- ROLE0: overlapping function spans in first module
- ROLE1: overlapping function spans in second module (`files`)
- ROLE2: none

25. God Object
- Entity: class
- Predicate: public_function_count > `GOD_OBJECT_FUNCTIONS` and >= `MIN_GOD_OBJECT_FUNCTIONS`
- ROLE0: class public method spans (`instance_lines`)
- ROLE1: class span
- ROLE2: none

26. Potential Improper API Usage
- Entity: module
- Predicate: repetitive_call_ratio > `API_REPETITION_THRESHOLD` with guards `MIN_API_CALLS`, `API_REPETITION_MIN_COUNT`
- ROLE0: repetitive API call-site spans (`instance_lines`)
- ROLE1: module span/file context
- ROLE2: none

27. Orphan Module
- Entity: module
- Predicate: in_degree + out_degree == 0 (with exclusions and min project size)
- ROLE0: module/file full range
- ROLE1: none
- ROLE2: none

28. Cyclic Dependency
- Entity: cycle path/group
- Predicate: cycle size between `MIN_CYCLE_SIZE` and `MAX_CYCLE_SIZE`, not excluded; severity uses `CYCLE_HIGH_MIN_SIZE/STRONGTH`
- ROLE0: cycle edge import spans (`files[].instance_lines`)
- ROLE1: module sequence/path context
- ROLE2: none

29. Unstable Dependency
- Entity: module
- Predicate: instability = out/(in+out) > `UNSTABLE_DEPENDENCY_THRESHOLD` with `MIN_DEPENDENCIES`
- ROLE0: outgoing import spans (`outgoing_instance_lines`)
- ROLE1: incoming spans from predecessor files (`files[].incoming_instance_lines`)
- ROLE2: none

### Structural smells (17)
30. High Number of Methods (NOM)
- Entity: class
- Predicate: regular_method_count > `NOM_THRESHOLD`
- ROLE0: method definition spans
- ROLE1: class span
- ROLE2: none

31. High Weighted Methods per Class (WMPC)
- Entity: class
- Predicate: WMPC1 > `WMPC1_THRESHOLD` OR WMPC2 > `WMPC2_THRESHOLD`
- ROLE0: complex method spans contributing to WMPC
- ROLE1: class span
- ROLE2: none

32. Large Class (SIZE2)
- Entity: class
- Predicate: significant_members > `SIZE2_THRESHOLD`
- ROLE0: member spans (methods + fields)
- ROLE1: class span
- ROLE2: none

33. High Weight of a Class (WAC)
- Entity: class
- Predicate: weighted_attribute_count > `WAC_THRESHOLD`
- ROLE0: significant field/attribute spans
- ROLE1: method spans using those fields
- ROLE2: none

34. High Lack of Cohesion of Methods (LCOM)
- Entity: class
- Predicate: lcom_value > `LCOM_THRESHOLD`
- ROLE0: non-cohesive method pair spans
- ROLE1: field-usage spans (cohesion context)
- ROLE2: none

35. High Response for a Class (RFC)
- Entity: class
- Predicate: rfc_value > `RFC_THRESHOLD`
- ROLE0: class method spans (response set seed)
- ROLE1: method-call spans expanding response set
- ROLE2: none

36. High Number of Classes per Module
- Entity: module
- Predicate: adjusted_class_count > dynamic threshold from `NOC_MODULE_THRESHOLD` and multipliers
- ROLE0: class spans in module (`instance_lines`)
- ROLE1: none
- ROLE2: none

37. Deep Inheritance Tree (DIT)
- Entity: class
- Predicate: shortest_path_length(object -> class) > `DIT_THRESHOLD` (after base filtering with `FRAMEWORK_BASES`)
- ROLE0: inheritance path class spans (`files[].instance_lines`)
- ROLE1: base class span in path (if distinguished)
- ROLE2: leaf class span (target class)
- Within-smell sharing note: multiple DIT rows can share same base file and nearly identical path spans (e.g., Monthly vs Annual), differing by tail node.

38. High Lines of Code (LOC)
- Entity: module/file
- Predicate: adjusted_loc > `LOC_THRESHOLD` with doc/test modifiers
- ROLE0: code line spans counted toward LOC (`instance_lines`)
- ROLE1: none
- ROLE2: none

39. High Message Passing Coupling (MPC)
- Entity: class
- Predicate: mpc_value > `MPC_THRESHOLD` (weighted by `MPC_EXTERNAL_WEIGHT`)
- ROLE0: external call-site spans (`instance_lines`)
- ROLE1: class span
- ROLE2: none

40. High Coupling Between Object Classes (CBO)
- Entity: class
- Predicate: coupling_score > `CBO_THRESHOLD` (weights: `CBO_DIRECT_WEIGHT`, `CBO_INDIRECT_WEIGHT`)
- ROLE0: direct coupling call/base spans (`instance_lines`)
- ROLE1: indirect coupling spans
- ROLE2: class span

41. High Number of classes per Project
- Entity: project
- Predicate: weighted_project_class_count > adjusted project threshold
- ROLE0: all counted class spans grouped by file (`files[].instance_lines`)
- ROLE1: module grouping context
- ROLE2: none

42. High Cyclomatic Complexity
- Entity: method
- Predicate: cyclomatic_complexity > `CYCLOMATIC_COMPLEXITY_THRESHOLD`
- ROLE0: method span
- ROLE1: branch/decision node spans in method
- ROLE2: none

43. High Fan-out
- Entity: module
- Predicate: significant_outgoing_dependency_count > `MAX_FANOUT`
- ROLE0: outgoing import spans (`instance_lines`)
- ROLE1: none
- ROLE2: none

44. High Fan-in
- Entity: module
- Predicate: incoming_dependency_count > `MAX_FANIN`
- ROLE0: incoming import spans in source files (`files[].instance_lines`)
- ROLE1: base module context span
- ROLE2: none

45. Long File
- Entity: file
- Predicate: meaningful_line_count > `MAX_FILE_LENGTH`
- ROLE0: meaningful line spans (`instance_lines`)
- ROLE1: none
- ROLE2: none

46. Too Many Branches
- Entity: method
- Predicate: branch_count > `MAX_BRANCHES` OR max_nesting > `MAX_NESTING_DEPTH`
- ROLE0: method span
- ROLE1: branch construct spans
- ROLE2: none

## 7) Notes on current builder vs required dataset
Current `build_dataset.py` labels only detected report spans and uses BIO(+WITHIN/CALLFROM) without explicit ROLE0/1/2 separation.
For your goal, contributor extraction must be smell-aware and candidate-aware (detected + undetected), with explicit role channels per datapoint.

## 8) Minimal extraction algorithm per smell (uniform)
For each smell S:
1. Build candidate entities from detector internals (same loops as `detect_S`).
2. Compute `metrics_S` and evaluate `predicate_S`.
3. Materialize contributor spans into ROLE0/ROLE1/ROLE2.
4. Emit datapoint with `detected = predicate_S`.
5. Token-label excerpt(s) per role channel.

This keeps dataset semantics identical to report-generation semantics while adding undetected supervision.
