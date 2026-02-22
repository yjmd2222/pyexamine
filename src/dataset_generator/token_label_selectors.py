import re
from typing import Callable, Dict, List, Set


def _norm(name: str) -> str:
    return " ".join(str(name or "").strip().split()).lower()


def _id_token(token: str) -> str:
    return re.sub(r"^[^A-Za-z_]+|[^A-Za-z0-9_]+$", "", token or "")


def _default_selector(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    return set()


def _select_all_candidates(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    # Conservative implementation: keep all candidate tokens for this evidence entry.
    return set(candidate_indices)


def _select_control_flow_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = set()
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
    for i in candidate_indices:
        tok = tokens[i]
        tid = _id_token(tok).lower()
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
        tid = _id_token(tok).lower()
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
    out = set()
    types = {"int", "str", "float", "bool", "list", "dict", "tuple", "set"}
    for i in candidate_indices:
        tok = tokens[i]
        tid = _id_token(tok).lower()
        if tok in {"def", "class"} or ":" in tok or "," in tok or "(" in tok:
            out.add(i)
            continue
        if tid in types:
            out.add(i)
    return out or set(candidate_indices)


def _select_comment_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = set()
    for i in candidate_indices:
        tok = tokens[i]
        if tok.startswith("#") or tok.startswith('"""') or tok.startswith("'''"):
            out.add(i)
    return out or set(candidate_indices)


def _select_dot_access(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = set()
    for i in candidate_indices:
        tok = tokens[i]
        if tok.count(".") >= 1:
            out.add(i)
    return out or set(candidate_indices)


def _select_message_chain(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = set()
    for i in candidate_indices:
        tok = tokens[i]
        if tok.count(".") >= 2:
            out.add(i)
    if out:
        return out
    # Degrade gracefully for short chains that may be tokenized across pieces.
    for i in candidate_indices:
        tok = tokens[i]
        if "." in tok or "(" in tok:
            out.add(i)
    return out or set(candidate_indices)


def _select_import_related(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = set()
    keywords = {"import", "from", "as"}
    for i in candidate_indices:
        tok = tokens[i]
        if tok in keywords or "." in tok:
            out.add(i)
    return out or set(candidate_indices)


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
        tid = _id_token(tok).lower()
        if tok in {"class", "def", "return"}:
            out.add(i)
            continue
        if tok.startswith("self."):
            out.add(i)
            continue
        if tid.startswith(("get", "set", "is")):
            out.add(i)
    return out


def _select_dit_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = set()
    class_name = str(entry.get("class_name", "") or "")
    ids = {x for x in class_name.split(".") if x}
    for i in candidate_indices:
        tok = tokens[i]
        tid = _id_token(tok)
        if tok == "class" or tid in ids:
            out.add(i)
    return out


def _select_scattered_like(
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    out = set()
    fn = str(entry.get("function", "") or "")
    for i in candidate_indices:
        tok = tokens[i]
        tid = _id_token(tok)
        if tok == "def" or (fn and (tid == fn or fn in tok)):
            out.add(i)
    return out


_REGISTRY: Dict[str, Callable[[str, List[str], List[Dict], List[int], Dict], Set[int]]] = {
    "long method": _select_control_flow_like,
    "large class": _select_class_method_like,
    "primitive obsession": _select_signature_like,
    "long parameter list": _select_signature_like,
    "data clumps": _select_signature_like,
    "switch statements": _select_control_flow_like,
    "temporary field": _select_class_method_like,
    "alternative classes with different interfaces": _select_class_method_like,
    "potential divergent change": _select_class_method_like,
    "parallel inheritance hierarchies": _select_class_method_like,
    "potential shotgun surgery": _select_all_candidates,
    "excessive comments": _select_comment_like,
    "duplicate code": _select_all_candidates,
    "data class": _select_data_class_like,
    "dead code": _select_all_candidates,
    "lazy class": _select_class_method_like,
    "speculative generality": _select_class_method_like,
    "feature envy": _select_dot_access,
    "inappropriate intimacy": _select_dot_access,
    "message chains": _select_message_chain,
    "middle man": _select_dot_access,
    "high number of methods (nom)": _select_class_method_like,
    "high weighted methods per class (wmpc)": _select_control_flow_like,
    "large class (size2)": _select_class_method_like,
    "high weight of a class (wac)": _select_control_flow_like,
    "high lack of cohesion of methods (lcom)": _select_dot_access,
    "high response for a class (rfc)": _select_dot_access,
    "high number of classes per module": _select_class_method_like,
    "deep inheritance tree (dit)": _select_dit_like,
    "high lines of code (loc)": _select_all_candidates,
    "high message passing coupling (mpc)": _select_dot_access,
    "high coupling between object classes (cbo)": _select_dot_access,
    "high number of classes per project": _select_class_method_like,
    "high cyclomatic complexity": _select_control_flow_like,
    "high fan-in": _select_import_related,
    "high fan-out": _select_import_related,
    "long file": _select_all_candidates,
    "too many branches": _select_control_flow_like,
    "hub-like dependency": _select_import_related,
    "unstable dependency": _select_import_related,
    "cyclic dependency": _select_import_related,
    "scattered functionality": _select_scattered_like,
    "potential redundant abstractions": _select_class_method_like,
    "god object": _select_class_method_like,
    "potential improper api usage": _select_dot_access,
    "orphan module": _select_all_candidates,
}


def select_positive_indices(
    smell_name: str,
    role: str,
    tokens: List[str],
    token_map: List[Dict],
    candidate_indices: List[int],
    entry: Dict,
) -> Set[int]:
    selector = _REGISTRY.get(_norm(smell_name), _default_selector)
    selected = selector(role, tokens, token_map, candidate_indices, entry)
    # Always constrain to candidate set from exact contributor lines.
    allowed = set(candidate_indices)
    return {i for i in selected if i in allowed}
