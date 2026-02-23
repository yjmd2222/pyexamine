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
- Implementation selector detail: define a smell-specific selector for Long Method using the existing token plan target (select control-flow/branch tokens (`if/for/while/try/except/match`) and call-heavy statements.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(method span)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Long Method; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (line for ROLE0 entry.) only when selector is truly missing.

## 2. Large Class [Not Implemented]
- Roles: ROLE0(class span), ROLE1(optional method evidence)
- Token plan: class header + non-trivial method defs and field-heavy assignments.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for Large Class using the existing token plan target (class header + non-trivial method defs and field-heavy assignments.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(optional method evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Large Class; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 3. Primitive Obsession [Not Implemented]
- Roles: ROLE0(function span), ROLE1(signature evidence)
- Token plan: primitive type annotations/literals in signature (`int/str/float/bool/list/dict/tuple`, literal-heavy params).
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for Primitive Obsession using the existing token plan target (primitive type annotations/literals in signature (`int/str/float/bool/list/dict/tuple`, literal-heavy params).) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(function span), ROLE1(signature evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Primitive Obsession; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 4. Long Parameter List [Not Implemented]
- Roles: ROLE0(function span), ROLE1(signature evidence)
- Token plan: parameter identifiers and separators in long signature region.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for Long Parameter List using the existing token plan target (parameter identifiers and separators in long signature region.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(function span), ROLE1(signature evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Long Parameter List; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 5. Data Clumps [Not Implemented]
- Roles: ROLE0(multiple related signatures)
- Token plan: repeated parameter name/type tokens across grouped signatures.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for Data Clumps using the existing token plan target (repeated parameter name/type tokens across grouped signatures.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(multiple related signatures)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Data Clumps; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 6. Switch Statements [Not Implemented]
- Roles: ROLE0(chain span)
- Token plan: branch keywords/conditions (`if/elif/else/match/case`) and compared discriminant tokens.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for Switch Statements using the existing token plan target (branch keywords/conditions (`if/elif/else/match/case`) and compared discriminant tokens.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(chain span)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Switch Statements; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 7. Temporary Field [Not Implemented]
- Roles: ROLE0(class span), ROLE1(init-field lines)
- Token plan: `self.<field>` writes in `__init__`, low-usage field tokens.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for Temporary Field using the existing token plan target (`self.<field>` writes in `__init__`, low-usage field tokens.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(init-field lines)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Temporary Field; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 8. Alternative Classes with Different Interfaces [Not Implemented]
- Roles: ROLE0(class headers), ROLE1(public method defs)
- Token plan: class names + public method identifiers that differentiate interfaces.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for Alternative Classes with Different Interfaces using the existing token plan target (class names + public method identifiers that differentiate interfaces.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class headers), ROLE1(public method defs)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Alternative Classes with Different Interfaces; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 9. Potential Divergent Change [Not Implemented]
- Roles: ROLE0(class span), ROLE1(prefix-divergent method evidence)
- Token plan: method names/prefix tokens from evidence methods.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for Potential Divergent Change using the existing token plan target (method names/prefix tokens from evidence methods.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(prefix-divergent method evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Potential Divergent Change; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 10. Parallel Inheritance Hierarchies [Not Implemented]
- Roles: ROLE0(class chain entries)
- Token plan: class names and inheritance base tokens in hierarchy paths.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for Parallel Inheritance Hierarchies using the existing token plan target (class names and inheritance base tokens in hierarchy paths.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class chain entries)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Parallel Inheritance Hierarchies; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 11. Potential Shotgun Surgery [Not Implemented]
- Roles: ROLE0(call-site lines)
- Token plan: call expressions and callee identifiers at scattered call sites.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for Potential Shotgun Surgery using the existing token plan target (call expressions and callee identifiers at scattered call sites.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(call-site lines)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Potential Shotgun Surgery; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 12. Excessive Comments [Not Implemented]
- Roles: ROLE0(comment block spans)
- Token plan: comment text tokens only; code tokens stay `O`.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for Excessive Comments using the existing token plan target (comment text tokens only; code tokens stay `O`.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(comment block spans)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Excessive Comments; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 13. Duplicate Code [Not Implemented]
- Roles: ROLE0(duplicate block spans)
- Token plan: duplicated statement/call sequences within each duplicate span.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for Duplicate Code using the existing token plan target (duplicated statement/call sequences within each duplicate span.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(duplicate block spans)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Duplicate Code; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 14. Data Class [Implemented]
- Roles: ROLE0(class span), ROLE1(getter/setter evidence)
- Token plan: getter/setter method names, `self.<field>`, trivial return/assignment patterns.
- Fallback: per ROLE entry.

## 15. Dead Code [Not Implemented]
- Roles: ROLE0(unused function/class span)
- Token plan: declaration token(s) and body statements in unused member span.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for Dead Code using the existing token plan target (declaration token(s) and body statements in unused member span.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(unused function/class span)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Dead Code; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 16. Lazy Class [Not Implemented]
- Roles: ROLE0(class span)
- Token plan: minimal class header and sparse method/field tokens.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for Lazy Class using the existing token plan target (minimal class header and sparse method/field tokens.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Lazy Class; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 17. Speculative Generality [Not Implemented]
- Roles: ROLE0(class span), ROLE1(abstract/pass/unused evidence)
- Token plan: `pass`, unused params, abstract method decorators/signatures.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for Speculative Generality using the existing token plan target (`pass`, unused params, abstract method decorators/signatures.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(abstract/pass/unused evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Speculative Generality; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

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
- Implementation selector detail: define a smell-specific selector for Inappropriate Intimacy using the existing token plan target (cross-object member access tokens (`other.<field>` style) in evidence spans.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class headers), ROLE1(cross-class field-access evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Inappropriate Intimacy; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 20. Message Chains [Implemented]
- Roles: ROLE0(chain evidence lines)
- Token plan: chained access segments (`a.b.c...`) and call-chain nodes only.
- Fallback: per ROLE0 entry.

## 21. Middle Man [Not Implemented]
- Roles: ROLE0(class span), ROLE1(delegating method evidence)
- Token plan: delegating calls forwarding to collaborator object.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for Middle Man using the existing token plan target (delegating calls forwarding to collaborator object.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(delegating method evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Middle Man; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 22. High Number of Methods (NOM) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(method headers)
- Token plan: method-def identifiers and class header token.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for High Number of Methods (NOM) using the existing token plan target (method-def identifiers and class header token.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(method headers)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Number of Methods (NOM); assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 23. High Weighted Methods per Class (WMPC) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(complex method evidence)
- Token plan: complexity-driving constructs in listed methods.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for High Weighted Methods per Class (WMPC) using the existing token plan target (complexity-driving constructs in listed methods.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(complex method evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Weighted Methods per Class (WMPC); assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 24. Large Class (SIZE2) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(field + public method evidence)
- Token plan: field identifiers + public method names from evidence spans.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for Large Class (SIZE2) using the existing token plan target (field identifiers + public method names from evidence spans.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(field + public method evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Large Class (SIZE2); assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 25. High Weight of a Class (WAC) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(weight-contributing methods)
- Token plan: tokens in weighted methods and class header.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for High Weight of a Class (WAC) using the existing token plan target (tokens in weighted methods and class header.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(weight-contributing methods)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Weight of a Class (WAC); assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 26. High Lack of Cohesion of Methods (LCOM) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(field-access evidence)
- Token plan: field access tokens and method-field linkage tokens.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for High Lack of Cohesion of Methods (LCOM) using the existing token plan target (field access tokens and method-field linkage tokens.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(field-access evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Lack of Cohesion of Methods (LCOM); assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 27. High Response for a Class (RFC) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(external call-site evidence)
- Token plan: call expressions that contribute to RFC.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for High Response for a Class (RFC) using the existing token plan target (call expressions that contribute to RFC.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(external call-site evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Response for a Class (RFC); assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 28. High Number of Classes per Module [Not Implemented]
- Roles: ROLE0(module/file span), ROLE1(class evidence)
- Token plan: class definition tokens in module evidence.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for High Number of Classes per Module using the existing token plan target (class definition tokens in module evidence.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(module/file span), ROLE1(class evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Number of Classes per Module; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 29. Deep Inheritance Tree (DIT) [Implemented]
- Roles: ROLE0(target class span), ROLE2(inheritance path entries)
- Token plan: class header/base tokens per path entry.
- Fallback: per ROLE entry.

## 30. High Lines of Code (LOC) [Not Implemented]
- Roles: ROLE0(file evidence spans)
- Token plan: no extra thinning; keep line evidence tokens (or conservative statement tokens).
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for High Lines of Code (LOC) using the existing token plan target (no extra thinning; keep line evidence tokens (or conservative statement tokens).) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(file evidence spans)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Lines of Code (LOC); assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 31. High Message Passing Coupling (MPC) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(call evidence)
- Token plan: method call tokens contributing to MPC.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for High Message Passing Coupling (MPC) using the existing token plan target (method call tokens contributing to MPC.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(call evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Message Passing Coupling (MPC); assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 32. High Coupling Between Object Classes (CBO) [Not Implemented]
- Roles: ROLE0(class span), ROLE1(coupling evidence)
- Token plan: import/ref/call tokens that form external couplings.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for High Coupling Between Object Classes (CBO) using the existing token plan target (import/ref/call tokens that form external couplings.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(coupling evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Coupling Between Object Classes (CBO); assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 33. High Number of classes per Project [Not Implemented]
- Roles: ROLE0(project class entries)
- Token plan: class definition identifiers across project entries.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for High Number of classes per Project using the existing token plan target (class definition identifiers across project entries.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(project class entries)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Number of classes per Project; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 34. High Cyclomatic Complexity [Not Implemented]
- Roles: ROLE0(method span)
- Token plan: branch/control tokens driving complexity metric.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for High Cyclomatic Complexity using the existing token plan target (branch/control tokens driving complexity metric.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(method span)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for High Cyclomatic Complexity; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

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
- Implementation selector detail: define a smell-specific selector for Long File using the existing token plan target (conservative (line-equivalent) or statement heads only.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(file span)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Long File; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 38. Too Many Branches [Not Implemented]
- Roles: ROLE0(method span)
- Token plan: branch tokens and condition expressions.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for Too Many Branches using the existing token plan target (branch tokens and condition expressions.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(method span)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Too Many Branches; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

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
- Implementation selector detail: define a smell-specific selector for Potential Redundant Abstractions using the existing token plan target (overlapping function name/signature tokens.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(overlap function entries across files)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Potential Redundant Abstractions; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

## 42. God Object [Not Implemented]
- Roles: ROLE0(class span), ROLE1(public-method evidence)
- Token plan: public method def identifiers and high-responsibility call tokens.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for God Object using the existing token plan target (public method def identifiers and high-responsibility call tokens.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(class span), ROLE1(public-method evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for God Object; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 43. Potential Improper API Usage [Not Implemented]
- Roles: ROLE0(module span), ROLE1(API call evidence)
- Token plan: API call target tokens and misuse-site arguments.
- Fallback: per ROLE entry.
- Implementation selector detail: define a smell-specific selector for Potential Improper API Usage using the existing token plan target (API call target tokens and misuse-site arguments.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(module span), ROLE1(API call evidence)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Potential Improper API Usage; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE entry.) only when selector is truly missing.

## 44. Orphan Module [Not Implemented]
- Roles: ROLE0(module span)
- Token plan: conservative line-equivalent; sparse token rule not prioritized.
- Fallback: per ROLE0 entry.
- Implementation selector detail: define a smell-specific selector for Orphan Module using the existing token plan target (conservative line-equivalent; sparse token rule not prioritized.) and constrain selection to exact contributor lines only.
- Implementation entry/BIO detail: apply selection per evidence entry for roles (ROLE0(module span)); preserve entry identity and emit separate BIO strands for disjoint entries or multi-file evidence.
- Implementation exclusion detail: exclude structural markers, context padding, and any token outside the exact ROLE span; never allow cross-role leakage or cross-entry merge.
- Implementation validation detail: run detected/undetected spot checks for Orphan Module; assert non-empty positives for detected evidence entries, no out-of-range positives, token<=line positive counts, and fallback policy (per ROLE0 entry.) only when selector is truly missing.

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

