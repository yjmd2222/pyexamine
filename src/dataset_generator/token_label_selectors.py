import re
from typing import Callable, Dict, List, Set


def _norm(name: str) -> str:
    return " ".join(str(name or "").strip().split()).lower()


def _id_token(token: str) -> str:
    return re.sub(r"^[^A-Za-z_]+|[^A-Za-z0-9_]+$", "", token or "")


def _id_lower(token: str) -> str:
    return _id_token(token).lower()


def _is_number_token(token: str) -> bool:
    return bool(re.match(r"^[+-]?\d+(\.\d+)?$", token or ""))


def _is_string_like_token(token: str) -> bool:
    return (token or "").startswith(("'", '"'))


def _select_all_candidates(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    return set(candidate_indices)


def _select_by_predicate(
    tokens: List[str],
    candidate_indices: List[int],
    predicate: Callable[[str], bool],
) -> Set[int]:
    out = set()
    for i in candidate_indices:
        if predicate(tokens[i]):
            out.add(i)
    return out


def _select_control_flow_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    keys = {
        "if",
        "elif",
        "else",
        "for",
        "while",
        "try",
        "except",
        "finally",
        "match",
        "case",
        "with",
        "and",
        "or",
        "not",
        "return",
        "break",
        "continue",
    }
    out = set()
    for i in candidate_indices:
        tok = tokens[i]
        tid = _id_lower(tok)
        if tok in keys or tid in keys or "(" in tok:
            out.add(i)
    return out or set(candidate_indices)


def _select_class_method_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = set()
    for i in candidate_indices:
        tok = tokens[i]
        tid = _id_lower(tok)
        if tok in {"class", "def", "return"}:
            out.add(i)
            continue
        if tok.startswith("self.") or tid.startswith("__"):
            out.add(i)
            continue
        if tid:
            out.add(i)
    return out or set(candidate_indices)


def _select_signature_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    types = {"int", "str", "float", "bool", "list", "dict", "tuple", "set"}
    out = set()
    for i in candidate_indices:
        tok = tokens[i]
        tid = _id_lower(tok)
        if tok in {"def", "class"} or ":" in tok or "," in tok or "(" in tok:
            out.add(i)
            continue
        if tid in types or _is_number_token(tok) or _is_string_like_token(tok):
            out.add(i)
    return out or set(candidate_indices)


def _select_comment_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = _select_by_predicate(
        tokens,
        candidate_indices,
        lambda t: t.startswith("#") or t.startswith('"""') or t.startswith("'''"),
    )
    return out or set(candidate_indices)


def _select_dot_access(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = _select_by_predicate(tokens, candidate_indices, lambda t: "." in t)
    return out or set(candidate_indices)


def _select_foreign_dot_access(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = _select_by_predicate(
        tokens,
        candidate_indices,
        lambda t: "." in t and not t.startswith("self."),
    )
    return out or _select_dot_access(role, tokens, token_map, candidate_indices, entry)


def _select_message_chain(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = _select_by_predicate(tokens, candidate_indices, lambda t: t.count(".") >= 2)
    if out:
        return out
    out = _select_by_predicate(tokens, candidate_indices, lambda t: "." in t or "(" in t)
    return out or set(candidate_indices)


def _select_import_related(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    keys = {"import", "from", "as"}
    out = set()
    for i in candidate_indices:
        tok = tokens[i]
        if tok in keys or "." in tok:
            out.add(i)
    return out or set(candidate_indices)


def _select_calls_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = _select_by_predicate(
        tokens,
        candidate_indices,
        lambda t: "(" in t or "." in t or _id_lower(t) in {"return", "yield"},
    )
    return out or set(candidate_indices)


def _select_class_header_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = _select_by_predicate(
        tokens,
        candidate_indices,
        lambda t: t == "class" or _id_lower(t).startswith(("class", "__")),
    )
    return out or _select_class_method_like(role, tokens, token_map, candidate_indices, entry)


def _select_data_class_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = set()
    for i in candidate_indices:
        tok = tokens[i]
        tid = _id_lower(tok)
        if tok in {"class", "def", "return"}:
            out.add(i)
            continue
        if tok.startswith("self."):
            out.add(i)
            continue
        if tid.startswith(("get", "set", "is")):
            out.add(i)
    return out or set(candidate_indices)


def _select_dit_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    class_name = str(entry.get("class_name", "") or "")
    ids = {x for x in class_name.split(".") if x}
    out = set()
    for i in candidate_indices:
        tok = tokens[i]
        tid = _id_token(tok)
        if tok == "class" or tid in ids:
            out.add(i)
    return out or set(candidate_indices)


def _select_scattered_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    fn = str(entry.get("function", "") or "")
    out = set()
    for i in candidate_indices:
        tok = tokens[i]
        tid = _id_token(tok)
        if tok == "def" or (fn and (tid == fn or fn in tok)):
            out.add(i)
    return out or set(candidate_indices)


# Explicit selectors for previously not-implemented smells.
def _select_long_method_like(*args):
    return _select_control_flow_like(*args)


def _select_large_class_like(*args):
    role = args[0]
    if role == "ROLE1":
        return _select_class_method_like(*args)
    return _select_class_header_like(*args)


def _select_primitive_obsession_like(*args):
    return _select_signature_like(*args)


def _select_long_parameter_list_like(*args):
    return _select_signature_like(*args)


def _select_data_clumps_like(*args):
    return _select_signature_like(*args)


def _select_switch_statements_like(*args):
    return _select_control_flow_like(*args)


def _select_temporary_field_like(*args):
    role = args[0]
    if role == "ROLE1":
        return _select_dot_access(*args)
    return _select_class_header_like(*args)


def _select_alternative_classes_like(*args):
    role = args[0]
    if role == "ROLE1":
        return _select_signature_like(*args)
    return _select_class_header_like(*args)


def _select_divergent_change_like(*args):
    role = args[0]
    if role == "ROLE1":
        return _select_signature_like(*args)
    return _select_class_header_like(*args)


def _select_parallel_inheritance_like(*args):
    return _select_class_header_like(*args)


def _select_shotgun_surgery_like(*args):
    return _select_calls_like(*args)


def _select_excessive_comments_like(*args):
    return _select_comment_like(*args)


def _select_duplicate_code_like(*args):
    return _select_calls_like(*args)


def _select_dead_code_like(*args):
    return _select_class_method_like(*args)


def _select_lazy_class_like(*args):
    return _select_class_header_like(*args)


def _select_speculative_generality_like(*args):
    return _select_class_method_like(*args)


def _select_inappropriate_intimacy_like(*args):
    return _select_foreign_dot_access(*args)


def _select_middle_man_like(*args):
    return _select_calls_like(*args)


def _select_nom_like(*args):
    role = args[0]
    if role == "ROLE1":
        return _select_signature_like(*args)
    return _select_class_header_like(*args)


def _select_wmpc_like(*args):
    return _select_control_flow_like(*args)


def _select_size2_like(*args):
    return _select_class_method_like(*args)


def _select_wac_like(*args):
    return _select_control_flow_like(*args)


def _select_lcom_like(*args):
    return _select_dot_access(*args)


def _select_rfc_like(*args):
    return _select_calls_like(*args)


def _select_noc_module_like(*args):
    role = args[0]
    if role == "ROLE1":
        return _select_class_header_like(*args)
    return _select_all_candidates(*args)


def _select_loc_like(*args):
    return _select_all_candidates(*args)


def _select_mpc_like(*args):
    return _select_calls_like(*args)


def _select_cbo_like(*args):
    return _select_import_related(*args)


def _select_noc_project_like(*args):
    return _select_class_header_like(*args)


def _select_cyclomatic_like(*args):
    return _select_control_flow_like(*args)


def _select_long_file_like(*args):
    return _select_all_candidates(*args)


def _select_branches_like(*args):
    return _select_control_flow_like(*args)


def _select_redundant_abstractions_like(*args):
    return _select_signature_like(*args)


def _select_god_object_like(*args):
    role = args[0]
    if role == "ROLE1":
        return _select_calls_like(*args)
    return _select_class_header_like(*args)


def _select_improper_api_usage_like(*args):
    role = args[0]
    if role == "ROLE1":
        return _select_calls_like(*args)
    return _select_all_candidates(*args)


def _select_orphan_module_like(*args):
    return _select_all_candidates(*args)


_REGISTRY: Dict[str, Callable[[str, List[str], List[Dict], List[int], Dict], Set[int]]] = {
    "long method": _select_long_method_like,
    "large class": _select_large_class_like,
    "primitive obsession": _select_primitive_obsession_like,
    "long parameter list": _select_long_parameter_list_like,
    "data clumps": _select_data_clumps_like,
    "switch statements": _select_switch_statements_like,
    "temporary field": _select_temporary_field_like,
    "alternative classes with different interfaces": _select_alternative_classes_like,
    "potential divergent change": _select_divergent_change_like,
    "parallel inheritance hierarchies": _select_parallel_inheritance_like,
    "potential shotgun surgery": _select_shotgun_surgery_like,
    "excessive comments": _select_excessive_comments_like,
    "duplicate code": _select_duplicate_code_like,
    "data class": _select_data_class_like,
    "dead code": _select_dead_code_like,
    "lazy class": _select_lazy_class_like,
    "speculative generality": _select_speculative_generality_like,
    "feature envy": _select_dot_access,
    "inappropriate intimacy": _select_inappropriate_intimacy_like,
    "message chains": _select_message_chain,
    "middle man": _select_middle_man_like,
    "high number of methods (nom)": _select_nom_like,
    "high weighted methods per class (wmpc)": _select_wmpc_like,
    "large class (size2)": _select_size2_like,
    "high weight of a class (wac)": _select_wac_like,
    "high lack of cohesion of methods (lcom)": _select_lcom_like,
    "high response for a class (rfc)": _select_rfc_like,
    "high number of classes per module": _select_noc_module_like,
    "deep inheritance tree (dit)": _select_dit_like,
    "high lines of code (loc)": _select_loc_like,
    "high message passing coupling (mpc)": _select_mpc_like,
    "high coupling between object classes (cbo)": _select_cbo_like,
    "high number of classes per project": _select_noc_project_like,
    "high cyclomatic complexity": _select_cyclomatic_like,
    "high fan-in": _select_import_related,
    "high fan-out": _select_import_related,
    "long file": _select_long_file_like,
    "too many branches": _select_branches_like,
    "hub-like dependency": _select_import_related,
    "unstable dependency": _select_import_related,
    "cyclic dependency": _select_import_related,
    "scattered functionality": _select_scattered_like,
    "potential redundant abstractions": _select_redundant_abstractions_like,
    "god object": _select_god_object_like,
    "potential improper api usage": _select_improper_api_usage_like,
    "orphan module": _select_orphan_module_like,
}


def select_positive_indices(
    smell_name: str,
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    selector = _REGISTRY.get(_norm(smell_name), _select_all_candidates)
    selected = selector(role, tokens, token_map, candidate_indices, entry)
    allowed = set(candidate_indices)
    return {i for i in selected if i in allowed}
