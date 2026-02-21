# PyExamine Detector Low-Level Component Map (46 detector methods)

Scope: `src/code_quality_analyzer/{architectural,structural,code}_smell_detector.py`

This note tracks low-level analysis components each detector uses:
- concrete in-memory maps/graphs
- AST node primitives traversed
- graph operations
- evidence fields emitted into report rows (`instance_lines`, `files`, `incoming_instance_lines`, `outgoing_instance_lines`, range anchors)

## Shared analysis structures

### Architectural detector (`architectural_smell_detector.py`)
- File/module graph and indices created in `analyze_file`:
  - `self.module_dependencies: nx.DiGraph` (module import edges)
  - `self.file_paths[module] -> file_path`
  - `self.module_functions[module] -> set(function_names)`
  - `self.function_lines[module][function] -> [(start,end)]`
  - `self.import_lines[module] -> [{name,start_line_number,end_line_number}]`
  - `self.api_usage[module] -> [api_attr_name,...]`
  - `self.api_call_lines[module] -> [{name,start_line_number,end_line_number}]`
  - `self.class_methods[class_key] -> set(method_names)`
  - `self.class_method_lines[class_key][method] -> [(start,end)]`
  - `self.class_lines[class_key] -> (start,end)`
  - `self.external_dependencies[module] -> set((kind,module_name))`

### Structural detector (`structural_smell_detector.py`)
- Class/module graph and indices from `analyze_file`/`analyze_class`/`analyze_method`:
  - `self.class_info[class_name]` keys used by detectors:
    - `methods`, `fields`, `method_calls`, `method_call_lines`, `base_classes`, `loc`, `start_line_number`, `end_line_number`
  - `self.module_info[module]['loc']`
  - `self.dependency_graph: nx.DiGraph`
  - `self.module_dependencies: nx.DiGraph`
  - `self.import_lines[module][target] -> [{start_line_number,end_line_number}]`
  - `self.file_paths[module] -> file_path`

### Code detector (`code_smell_detector.py`)
- Per-file `astroid` module from `astroid.parse(content)`.
- Core primitives:
  - class/function nodes: `nodes.ClassDef`, `nodes.FunctionDef`
  - statements/expressions: `nodes.If`, `nodes.Call`, `nodes.Attribute`, `nodes.Return`, etc.
  - `self.file_content` for line-based heuristics (comments, effective LOC)

## Architectural smells (8)

1. `detect_hub_like_dependency` (`architectural_smell_detector.py:406`)
- Core components:
  - graph degree from `self.module_dependencies.in_degree/out_degree`
  - imported edge line evidence from `self.import_lines[module]`
  - external edges from `self.external_dependencies[module]`
- Evidence fields built:
  - `outgoing_instance_lines` on base file
  - `files[].incoming_instance_lines` grouped by predecessor module

2. `detect_scattered_functionality` (`architectural_smell_detector.py:544`)
- Core components:
  - function index `self.module_functions`
  - function span map `self.function_lines`
- Evidence fields built:
  - per module/function in `files[].instance_lines`

3. `detect_redundant_abstractions` (`architectural_smell_detector.py:602`)
- Core components:
  - similarity on `self.module_functions` (overlapping function sets)
  - span retrieval from `self.function_lines`
- Evidence fields built:
  - multi-file `files[].instance_lines` (function spans)

4. `detect_god_objects` (`architectural_smell_detector.py:682`)
- Core components:
  - class public method sets in `self.class_methods`
  - method spans from `self.class_method_lines`
  - class span from `self.class_lines`
- Evidence fields built:
  - base class range (`start_line_number/end_line_number`)
  - method `instance_lines`

5. `detect_improper_api_usage` (`architectural_smell_detector.py:745`)
- Core components:
  - call frequency from `self.api_usage[module]`
  - call-site spans from `self.api_call_lines[module]`
- Evidence fields built:
  - base `file_path`
  - repetitive API call `instance_lines`

6. `detect_orphan_modules` (`architectural_smell_detector.py:806`)
- Core components:
  - isolated modules where `in_degree + out_degree == 0` in `self.module_dependencies`
  - file length fallback from raw file read (for range anchor)
- Evidence fields built:
  - base module file range (`start_line_number=1`, `end_line_number=total_lines+1` when readable)
  - no line-span list arrays

7. `detect_cyclic_dependencies` (`architectural_smell_detector.py:858`)
- Core components:
  - cycle enumeration `nx.simple_cycles(self.module_dependencies)`
  - path-strength scoring using `nx.all_simple_paths`
  - per-cycle edge import spans from `self.import_lines[module]`
- Evidence fields built:
  - `files[].instance_lines` where each entry is the import span for one cycle hop

8. `detect_unstable_dependencies` (`architectural_smell_detector.py:938`)
- Core components:
  - instability score from `in_degree/out_degree` of `self.module_dependencies`
  - outgoing imports from `self.import_lines[node]`
  - incoming imports reconstructed by scanning predecessor `import_lines`
  - inclusion of `self.external_dependencies[node]`
- Evidence fields built:
  - `outgoing_instance_lines` on base module
  - `files[].incoming_instance_lines` per incoming module

## Structural smells (17)

1. `detect_nom` (`structural_smell_detector.py:402`)
- Components: `self.class_info[class]['methods']`
- AST primitives in filtering: decorators checked via `ast.Name('property')`
- Evidence fields: class range only

2. `detect_wmpc` (`structural_smell_detector.py:444`)
- Components:
  - methods from `self.class_info[class]['methods']`
  - per-method complexity from `self.calculate_cyclomatic_complexity(method)`
- AST primitives inside complexity calc: `ast.If`, `ast.For`, `ast.While`, `ast.ExceptHandler`, `ast.BoolOp`
- Evidence fields: class range only (complex methods listed in description)

3. `detect_size2` (`structural_smell_detector.py:506`)
- Components:
  - method count: `self.class_info[class]['methods']`
  - field count: `self.class_info[class]['fields']`
  - optional method-call check via `self.class_info[class]['method_calls']`
- Evidence fields: class range only

4. `detect_wac` (`structural_smell_detector.py:550`)
- Components:
  - fields: `self.class_info[class]['fields']`
  - usage scan over method AST (`ast.Attribute`, `ast.Name`)
- Evidence fields: class range only

5. `detect_lcom` (`structural_smell_detector.py:601`)
- Components:
  - method list `self.class_info[class]['methods']`
  - field-usage map from helper `_build_field_usage_map`
- Evidence fields: class range only

6. `detect_rfc` (`structural_smell_detector.py:695`)
- Components:
  - local methods: `self.class_info[class]['methods']`
  - distinct response set from `self.class_info[class]['method_calls']`
- Evidence fields: class range only

7. `detect_noc_per_module` (`structural_smell_detector.py:788`)
- Components:
  - classes grouped by module from `self.class_info`
  - complexity weighting via `calculate_cyclomatic_complexity`
- Evidence fields:
  - module base `file_path`
  - module class spans in `instance_lines`

8. `detect_dit` (`structural_smell_detector.py:884`)
- Components:
  - inheritance edges from `self.class_info[class]['base_classes']`
  - graph: `inheritance_graph = nx.DiGraph()`
  - root-path depth: `nx.shortest_path_length('object', class_name)`
  - class path sequence: `nx.shortest_path('object', class_name)`
  - per-path class spans from `self.class_info[path_class]['start_line_number'/'end_line_number']`
- Evidence fields:
  - base class `file_path` + `class_name`
  - inheritance path in `files[].instance_lines`

9. `detect_loc` (`structural_smell_detector.py:988`)
- Components:
  - per-module LOC from source content + line classification
  - `self.module_info[module]['loc']`, filtered code/doc/import/blank counts
- Evidence fields:
  - base module `file_path`
  - contiguous code `instance_lines`

10. `detect_mpc` (`structural_smell_detector.py:1101`)
- Components:
  - method-call totals from `self.class_info[class]['method_calls']`
  - call-site spans from `self.class_info[class]['method_call_lines']`
- Evidence fields:
  - class range
  - call-site `instance_lines`

11. `detect_cbo` (`structural_smell_detector.py:1198`)
- Components:
  - base links `self.class_info[class]['base_classes']`
  - method AST calls (`ast.Call`, `ast.Attribute`) to infer external coupling
  - exclusion helpers `_is_excluded_dependency`, `_get_base_object`
- Evidence fields:
  - class range
  - coupling-related `instance_lines`

12. `detect_noc_per_project` (`structural_smell_detector.py:1375`)
- Components:
  - weighted project class count from `self.class_info`
  - threshold adjustment by `_adjust_noc_threshold` using project LOC
- Evidence fields:
  - project-wide `files[].instance_lines` by module/class

13. `detect_cyclomatic_complexity` (`structural_smell_detector.py:1559`)
- Components:
  - per method AST walk via `calculate_cyclomatic_complexity`
- Evidence fields:
  - method range only

14. `detect_fanout` (`structural_smell_detector.py:1633`)
- Components:
  - outgoing dependencies from `self.dependency_graph.successors(module)`
  - import-site spans from `self.import_lines[module][successor]`
- Evidence fields:
  - base module file
  - outgoing import `instance_lines`

15. `detect_fanin` (`structural_smell_detector.py:1689`)
- Components:
  - incoming degree from `self.dependency_graph.in_degree(module)`
  - incoming import spans by scanning `self.import_lines[src][target]`
- Evidence fields:
  - base module file
  - connected source modules in `files[].instance_lines`

16. `detect_file_length` (`structural_smell_detector.py:1746`)
- Components:
  - raw file content scan for meaningful lines (non-blank/non-comment/non-docstring)
- Evidence fields:
  - file-level contiguous `instance_lines`

17. `detect_branches` (`structural_smell_detector.py:1825`)
- Components:
  - branch metrics from `_analyze_branches(method)`
  - `_analyze_branches` counts `ast.If`, `ast.For`, `ast.While`, `ast.Try`, nested depth
- Evidence fields:
  - method range only

## Code smells (21, astroid)

1. `detect_long_methods` (`code_smell_detector.py:224`)
- Components: `nodes.FunctionDef` spans + `self.file_content` effective-line counting
- Node primitives: decorators (`nodes.Name`, `nodes.Call`), class/function context
- Evidence fields: method/function range

2. `detect_large_classes` (`code_smell_detector.py:279`)
- Components: per-class `nodes.FunctionDef` filtering (ignore magic/simple getter-setter)
- Node primitives: `nodes.ClassDef`, `nodes.Return`, `nodes.Assign`
- Evidence fields: class range

3. `detect_primitive_obsession` (`code_smell_detector.py:337`)
- Components: function arg annotations via astroid arg nodes
- Node primitives: `nodes.AssignName`, `nodes.Name`
- Evidence fields: method/function range

4. `detect_long_parameter_lists` (`code_smell_detector.py:393`)
- Components: arg vector length, vararg/kwarg presence
- Node primitives: class/function nodes
- Evidence fields: method/function range

5. `detect_data_clumps` (`code_smell_detector.py:448`)
- Components: repeated parameter-set signatures across functions/methods
- Node primitives: `nodes.FunctionDef`, `nodes.AssignName`, `nodes.Name`
- Evidence fields: base `file_path` + `instance_lines` per repeated parameter block

6. `detect_switch_statements` (`code_smell_detector.py:518`)
- Components: complex conditional patterns
- Node primitives: `nodes.If`, `nodes.Compare`, `nodes.Call`, `nodes.ExceptHandler`, `nodes.Expr`
- Evidence fields: statement range

7. `detect_temporary_fields` (`code_smell_detector.py:568`)
- Components: class attribute assignment/use frequency
- Node primitives: `nodes.Attribute`, `nodes.Assign`, `nodes.Call`, `nodes.FunctionDef`
- Evidence fields: class range

8. `detect_alternative_classes` (`code_smell_detector.py:641`)
- Components: class interface comparison (method signatures/attributes)
- Node primitives: `nodes.ClassDef`, `nodes.Attribute`, `nodes.Call`
- Evidence fields: multi-class spans in file (`files`-style class segments)

9. `detect_divergent_change` (`code_smell_detector.py:723`)
- Components: method-name prefix clustering + class method groups
- Node primitives: `nodes.ClassDef`, `nodes.Call`, `nodes.Attribute`
- Evidence fields: class range + hotspot `instance_lines`

10. `detect_parallel_inheritance` (`code_smell_detector.py:813`)
- Components: class naming/inheritance parallelism patterns
- Node primitives: `nodes.ClassDef`, `nodes.Name`
- Evidence fields: paired class spans

11. `detect_shotgun_surgery` (`code_smell_detector.py:903`)
- Components: call-site dispersion contexts for same call target
- Node primitives: `nodes.FunctionDef`, `nodes.ClassDef`, `nodes.Name`
- Evidence fields: file `instance_lines` of dispersed call contexts

12. `detect_comments` (`code_smell_detector.py:954`)
- Components: comment ratio/block-size from raw `self.file_content`
- Node primitives: none (line scanner)
- Evidence fields: comment `instance_lines`

13. `detect_duplicate_code` (`code_smell_detector.py:1013`)
- Components: normalized statement/block signatures + repeated line windows
- Node primitives: `nodes.FunctionDef`, `nodes.Assign`, `nodes.Return`
- Evidence fields: duplicated block `instance_lines`

14. `detect_data_class` (`code_smell_detector.py:1072`)
- Components: class member mix (fields vs behavior)
- Node primitives: `nodes.ClassDef`, `nodes.Name`
- Evidence fields: class range + member evidence `instance_lines`

15. `detect_dead_code` (`code_smell_detector.py:1147`)
- Components: function usage heuristics and visibility/decorator checks
- Node primitives: `nodes.FunctionDef`, `nodes.Name`, `nodes.Attribute`
- Evidence fields: function range

16. `detect_lazy_class` (`code_smell_detector.py:1231`)
- Components: class LOC/method-count thresholds
- Node primitives: `nodes.ClassDef`, `nodes.Return`, `nodes.Assign`
- Evidence fields: class range

17. `detect_speculative_generality` (`code_smell_detector.py:1276`)
- Components: unused-parameter and abstract/placeholder behavior checks
- Node primitives: `nodes.ClassDef`, `nodes.Pass`, `nodes.Name`
- Evidence fields: class range + instance lines for speculative members

18. `detect_feature_envy` (`code_smell_detector.py:1355`)
- Components: external attribute-call counts vs local `self` calls
- Node primitives: `nodes.Attribute`, `nodes.FunctionDef`, `nodes.Call`, `nodes.Name`
- Evidence fields: function range + external-call `instance_lines`

19. `detect_inappropriate_intimacy` (`code_smell_detector.py:1459`)
- Components: cross-class field/method overlap and attribute access
- Node primitives: `nodes.ClassDef`, `nodes.AssignAttr`, `nodes.Attribute`
- Evidence fields: class range + merged overlap/access `instance_lines`

20. `detect_message_chains` (`code_smell_detector.py:1594`)
- Components: chained `nodes.Attribute` traversal depth + chain context
- Evidence fields: chain expression range (line spans collapsed from chain links)

21. `detect_middle_man` (`code_smell_detector.py:1683`)
- Components: delegating-return method ratio and delegation target concentration
- Node primitives: `nodes.Return`, `nodes.Call`, `nodes.Attribute`, `nodes.ClassDef`
- Evidence fields: class range + delegated-method `instance_lines`
