# Severity Assignment Audit (Report Generation)

Scope:
- `master-thesis-materials/pyexamine/src/code_quality_analyzer/code_smell_detector.py`
- `master-thesis-materials/pyexamine/src/code_quality_analyzer/structural_smell_detector.py`
- `master-thesis-materials/pyexamine/src/code_quality_analyzer/architectural_smell_detector.py`

## Classification Rule Used
- `NON-FALLBACK severity`: severity is computed from runtime metric magnitude (typically threshold-relative), not fixed.
- `FALLBACK severity`: severity is fixed literal (`low`/`medium`/`high`) per smell implementation, or defaulted by recorder (`severity or payload.severity or "medium"`).

Recorder-level fallback behavior (all 3 detectors):
- `resolved_severity = severity or getattr(payload, "severity", "medium")`
- If a detector call omits severity and payload has none, final severity becomes `medium`.

## NON-FALLBACK Severity (computed)

### Structural smells (all 17 are computed)
1. `High Number of Methods (NOM)` (`detect_nom`)
- Formula: `High` if `nom > NOM_THRESHOLD * 1.5`, else `Medium`.

2. `Weighted Methods per Class (WMPC)` (`detect_wmpc`)
- Formula: `High` if `WMPC1` or `WMPC2` exceeds `1.5x` threshold, else `Medium`.

3. `Class Size 2 (SIZE2)` (`detect_size2`)
- Formula: `High` if `size2 > SIZE2_THRESHOLD * 1.5`, else `Medium`.

4. `Weighted Attributes per Class (WAC)` (`detect_wac`)
- Formula: `High` if `wac > WAC_THRESHOLD * 1.5`, else `Medium`.

5. `Lack of Cohesion of Methods (LCOM)` (`detect_lcom`)
- Formula: `High` if `lcom > LCOM_THRESHOLD * 1.5`, else `Medium`.

6. `Response For Class (RFC)` (`detect_rfc`)
- Formula: `High` if `rfc > RFC_THRESHOLD * 1.5`, else `Medium`.

7. `High Number of classes per Module` (`detect_noc_per_module`)
- Formula: `High` if `count > adjusted_threshold * 1.5`, else `Medium`.

8. `Deep Inheritance Tree` (`detect_dit`)
- Formula (detected case): `High` if `dit > DIT_THRESHOLD * 1.5`, else `Medium`.
- Also has non-detected template rows with `Low` in one branch.

9. `High Lines of Code (LOC)` (`detect_loc`)
- Formula: `High` if `effective_loc > adjusted_threshold * 1.5`, else `Medium`.

10. `Message Passing Coupling (MPC)` (`detect_mpc`)
- Formula: `High` if `weighted_mpc > MPC_THRESHOLD * 1.5`, else `Medium`.

11. `Coupling Between Objects (CBO)` (`detect_cbo`)
- Uses `_calculate_cbo_severity(weighted_cbo, threshold)`:
  - `High` if `weighted_cbo > 2.0 * threshold`
  - `Medium` if `weighted_cbo > 1.5 * threshold`
  - `Low` otherwise

12. `High Number of classes per Project` (`detect_noc_per_project`)
- Formula: `High` if `weighted_noc > adjusted_threshold * 1.5`, else `Medium`.

13. `High Cyclomatic Complexity` (`detect_cyclomatic_complexity`)
- Formula: `High` if complexity `> threshold * 1.5`, else `Medium`.

14. `High Fan-out` (`detect_fanout`)
- Formula: `High` if significant deps `> threshold * 1.5`, else `Medium`.

15. `High Fan-in` (`detect_fanin`)
- Formula: `High` if fanin `> threshold * 1.5`, else `Medium`.

16. `Long File` (`detect_file_length`)
- Formula: `High` if meaningful lines `> threshold * 1.5`, else `Medium`.

17. `Too Many Branches` (`detect_branches`)
- Formula: `High` if branch count `> threshold * 1.5`, else `Medium`.

### Architectural smells (computed)
18. `Hub-like Dependency` (`detect_hub_like_dependency`)
- Formula: `high` if `total_connections > MIN_HUB_CONNECTIONS * 2`, else `medium`.

19. `Cyclic Dependency` (`detect_cyclic_dependencies`)
- Formula: `high` if both hold:
  - `len(cycle) >= CYCLE_HIGH_MIN_SIZE`
  - `strength >= CYCLE_HIGH_MIN_STRENGTH`
- Else `medium`.

## FALLBACK Severity (fixed literal / default behavior)

### Code smells (all 21 use fixed severity literals)
- `Long Method` -> `medium`
- `Large Class` -> `medium`
- `Primitive Obsession` -> `medium`
- `Long Parameter List` -> `medium`
- `Data Clumps` -> `medium`
- `Switch Statements` -> `medium`
- `Temporary Field` -> `low`
- `Alternative Classes with Different Interfaces` -> `medium`
- `Potential Divergent Change` -> `medium`
- `Parallel Inheritance Hierarchies` -> `high`
- `Potential Shotgun Surgery` -> `high`
- `Excessive Comments` -> `low`
- `Duplicate Code` -> `high`
- `Data Class` -> `medium`
- `Dead Code` -> `low`
- `Lazy Class` -> `low`
- `Speculative Generality` -> `medium`
- `Feature Envy` -> `medium`
- `Inappropriate Intimacy` -> `medium`
- `Message Chains` -> `medium`
- `Middle Man` -> `medium`

### Architectural smells (fixed severity literals)
- `Scattered Functionality` -> `medium`
- `Potential Redundant Abstractions` -> `medium`
- `God Object` -> `medium`
- `Potential Improper API Usage` -> `medium`
- `Orphan Module` -> `medium`
- `Unstable Dependency` -> `medium`

## Practical takeaway
- Your statement is accurate: severity in pyexamine is mostly fallback/fixed for code smells and most architectural smells.
- Severity is genuinely magnitude-aware mainly in structural smells, plus `Hub-like Dependency` and `Cyclic Dependency`.

## Future Training Target

Severity should later be treated as a prediction target for both the existing 46 smells and module complexity.

Current status:

- 	raining_inference does not predict severity
- severity is only report metadata today

Planned direction:

- severity should be detected/predicted later
- this is future work and not part of the current implementation pass

