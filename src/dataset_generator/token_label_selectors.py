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
    return out


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
    return out


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
    return out


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
    "data class": _select_data_class_like,
    "feature envy": _select_dot_access,
    "message chains": _select_message_chain,
    "deep inheritance tree (dit)": _select_dit_like,
    "high fan-in": _select_import_related,
    "high fan-out": _select_import_related,
    "hub-like dependency": _select_import_related,
    "unstable dependency": _select_import_related,
    "cyclic dependency": _select_import_related,
    "scattered functionality": _select_scattered_like,
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

