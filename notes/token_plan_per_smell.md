# Token Granularity Implementation Plan (Per Smell, One by One)

Policy baseline:
- Line mode remains SSOT and already fixed.
- Token mode must be span-constrained and entry-preserving.
- If a smell selector is not implemented for a role-entry, fallback to line for that entry; row effective granularity stays tracked.

Implementation status legend:
- `[Implemented]`: token selector exists in `token_label_selectors.py` (initial version).
- `[Not Implemented]`: no explicit token selector yet (falls back to line).

## 1. Long Method [Not Implemented]
- Roles: ROLE0(method span)
- Token plan: select control-flow/branch tokens (`if/for/while/try/except/match`) and call-heavy statements.
- Fallback: line for ROLE0 entry.

## 2. Large Class [Not Implemented]
- Roles: ROLE0(class span), ROLE1(optional method evidence)
- Token plan: class header + non-trivial method defs and field-heavy assignments.
- Fallback: per ROLE entry.

## 3. Primitive Obsession [Not Implemented]
- Roles: ROLE0(function span), ROLE1(signature evidence)
- Token plan: primitive type annotations/literals in signature (`int/str/float/bool/list/dict/tuple`, literal-heavy params).
- Fallback: per ROLE entry.

## 4. Long Parameter List [Not Implemented]
- Roles: ROLE0(function span), ROLE1(signature evidence)
- Token plan: parameter identifiers and separators in long signature region.
- Fallback: per ROLE entry.

## 5. Data Clumps [Not Implemented]
- Roles: ROLE0(multiple related signatures)
- Token plan: repeated parameter name/type tokens across grouped signatures.
- Fallback: per ROLE0 entry.

## 6. Switch Statements [Not Implemented]
- Roles: ROLE0(chain span)
- Token plan: branch keywords/conditions (`if/elif/else/match/case`) and compared discriminant tokens.
- Fallback: per ROLE0 entry.

## 7. Temporary Field [Not Implemented]
- Roles: ROLE0(class span), ROLE1(init-field lines)
- Token plan: `self.<field>` writes in `__init__`, low-usage field tokens.
- Fallback: per ROLE entry.

## 8. Alternative Classes with Different Interfaces [Not Implemented]
- Roles: ROLE0(class headers), ROLE1(public method defs)
- Token plan: class names + public method identifiers that differentiate interfaces.
- Fallback: per ROLE entry.

## 9. Potential Divergent Change [Not Implemented]
- Roles: ROLE0(class span), ROLE1(prefix-divergent method evidence)
- Token plan: method names/prefix tokens from evidence methods.
- Fallback: per ROLE entry.

## 10. Parallel Inheritance Hierarchies [Not Implemented]
- Roles: ROLE0(class chain entries)
- Token plan: class names and inheritance base tokens in hierarchy paths.
- Fallback: per ROLE0 entry.

## 11. Potential Shotgun Surgery [Not Implemented]
- Roles: ROLE0(call-site lines)
- Token plan: call expressions and callee identifiers at scattered call sites.
- Fallback: per ROLE0 entry.

## 12. Excessive Comments [Not Implemented]
- Roles: ROLE0(comment block spans)
- Token plan: comment text tokens only; code tokens stay `O`.
- Fallback: per ROLE0 entry.

## 13. Duplicate Code [Not Implemented]
- Roles: ROLE0(duplicate block spans)
- Token plan: duplicated statement/call sequences within each duplicate span.
- Fallback: per ROLE0 entry.

## 14. Data Class [Implemented]
- Roles: ROLE0(class span), ROLE1(getter/setter evidence)
- Token plan: getter/setter method names, `self.<field>`, trivial return/assignment patterns.
- Fallback: per ROLE entry.

## 15. Dead Code [Not Implemented]
- Roles: ROLE0(unused function/class span)
- Token plan: declaration token(s) and body statements in unused member span.
- Fallback: per ROLE0 entry.

## 16. Lazy Class [Not Implemented]
- Roles: ROLE0(class span)
- Token plan: minimal class header and sparse method/field tokens.
- Fallback: per ROLE0 entry.

## 17. Speculative Generality [Not Implemented]
- Roles: ROLE0(class span), ROLE1(abstract/pass/unused evidence)
- Token plan: `pass`, unused params, abstract method decorators/signatures.
- Fallback: per ROLE entry.

## 18. Feature Envy [Implemented]
- Roles: ROLE0(method span), ROLE1(external attribute evidence)
- Token plan: external receiver attribute/call tokens from detector-matched evidence lines (not generic dot-anything).
- Fallback: per ROLE entry.


## Status conclusion (Feature Envy)
Update after selector patch and regeneration: fallback is now `0`, so this smell is fully implemented in token mode.

## 19. Inappropriate Intimacy [Not Implemented]
- Roles: ROLE0(class headers), ROLE1(cross-class field-access evidence)
- Token plan: cross-object member access tokens (`other.<field>` style) in evidence spans.
- Fallback: per ROLE entry.

## 20. Message Chains [Implemented]
- Roles: ROLE0(chain evidence lines)
- Token plan: chained access segments (`a.b.c...`) and call-chain nodes only.
- Fallback: per ROLE0 entry.

## 21. Middle Man [Not Implemented]
- Roles: ROLE0(class span), ROLE1(delegating method evidence)
- Token plan: delegating calls forwarding to collaborator object.
- Fallback: per ROLE entry.

## 22. High Number of Methods (NOM) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(method headers)
- Token plan: method-def identifiers and class header token.
- Fallback: per ROLE entry.

## 23. High Weighted Methods per Class (WMPC) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(complex method evidence)
- Token plan: complexity-driving constructs in listed methods.
- Fallback: per ROLE entry.

## 24. Large Class (SIZE2) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(field + public method evidence)
- Token plan: field identifiers + public method names from evidence spans.
- Fallback: per ROLE entry.

## 25. High Weight of a Class (WAC) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(weight-contributing methods)
- Token plan: tokens in weighted methods and class header.
- Fallback: per ROLE entry.

## 26. High Lack of Cohesion of Methods (LCOM) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(field-access evidence)
- Token plan: field access tokens and method-field linkage tokens.
- Fallback: per ROLE entry.

## 27. High Response for a Class (RFC) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(external call-site evidence)
- Token plan: call expressions that contribute to RFC.
- Fallback: per ROLE entry.

## 28. High Number of Classes per Module [Not Implemented]
- Roles: ROLE0(module/file span), ROLE1(class evidence)
- Token plan: class definition tokens in module evidence.
- Fallback: per ROLE entry.

## 29. Deep Inheritance Tree (DIT) [Implemented]
- Roles: ROLE0(target class span), ROLE2(inheritance path entries)
- Token plan: class header/base tokens per path entry.
- Fallback: per ROLE entry.

## 30. High Lines of Code (LOC) [Not Implemented]
- Roles: ROLE0(file evidence spans)
- Token plan: no extra thinning; keep line evidence tokens (or conservative statement tokens).
- Fallback: per ROLE0 entry.

## 31. High Message Passing Coupling (MPC) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(call evidence)
- Token plan: method call tokens contributing to MPC.
- Fallback: per ROLE entry.

## 32. High Coupling Between Object Classes (CBO) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(coupling evidence)
- Token plan: import/ref/call tokens that form external couplings.
- Fallback: per ROLE entry.

## 33. High Number of classes per Project [Not Implemented]
- Roles: ROLE0(project class entries)
- Token plan: class definition identifiers across project entries.
- Fallback: per ROLE0 entry.

## 34. High Cyclomatic Complexity [Not Implemented]
- Roles: ROLE0(method span)
- Token plan: branch/control tokens driving complexity metric.
- Fallback: per ROLE0 entry.

## 35. High Fan-out [Implemented]
- Roles: ROLE0(file span), ROLE1(outgoing dependency evidence)
- Token plan: import/from/module target tokens for outgoing deps.
- Fallback: per ROLE entry.

## 36. High Fan-in [Implemented]
- Roles: ROLE0(target module span), ROLE2(incoming evidence by file)
- Token plan: import statements in incoming files referencing target module.
- Fallback: per ROLE entry.

## 37. Long File [Not Implemented]
- Roles: ROLE0(file span)
- Token plan: conservative (line-equivalent) or statement heads only.
- Fallback: per ROLE0 entry.

## 38. Too Many Branches [Not Implemented]
- Roles: ROLE0(method span)
- Token plan: branch tokens and condition expressions.
- Fallback: per ROLE0 entry.

## 39. Hub-like Dependency [Implemented]
- Roles: ROLE0(hub module span), ROLE1(outgoing), ROLE2(incoming)
- Token plan: dependency edge tokens from import/call evidence.
- Fallback: per ROLE entry.

## 40. Scattered Functionality [Implemented]
- Roles: ROLE0(function anchors across files)
- Token plan: function definition identifiers tied to scattered concern.
- Fallback: per ROLE0 entry.

## 41. Potential Redundant Abstractions [Not Implemented]
- Roles: ROLE0(overlap function entries across files)
- Token plan: overlapping function name/signature tokens.
- Fallback: per ROLE0 entry.

## 42. God Object [Not Implemented]
- Roles: ROLE0(class span), ROLE1(public-method evidence)
- Token plan: public method def identifiers and high-responsibility call tokens.
- Fallback: per ROLE entry.

## 43. Potential Improper API Usage [Not Implemented]
- Roles: ROLE0(module span), ROLE1(API call evidence)
- Token plan: API call target tokens and misuse-site arguments.
- Fallback: per ROLE entry.

## 44. Orphan Module [Not Implemented]
- Roles: ROLE0(module span)
- Token plan: conservative line-equivalent; sparse token rule not prioritized.
- Fallback: per ROLE0 entry.

## 45. Cyclic Dependency [Implemented]
- Roles: ROLE0(cycle module anchors), ROLE1(cycle-forming evidence)
- Token plan: cycle edge import tokens per participating file.
- Fallback: per ROLE entry.

## 46. Unstable Dependency [Implemented]
- Roles: ROLE0(target module span), ROLE1(outgoing), ROLE2(incoming)
- Token plan: dependency edge tokens used for instability relation.
- Fallback: per ROLE entry.

## Execution order (recommended)
1. Implement selectors smell-by-smell in numerical order above.
2. After each smell, run one detected + one undetected semantic check.
3. Keep fallback metadata (`requested/effective/granularity_fallbacks`) to track not-yet-implemented coverage.

