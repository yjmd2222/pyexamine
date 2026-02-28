from __future__ import annotations

import argparse
import ast
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

COHESION_LEVELS = ["coincidental", "logical", "temporal", "procedural", "communicational", "sequential", "functional"]
COUPLING_LEVELS = ["content", "common", "control", "stamp", "data", "message", "external"]
CONTROL_NAMES = {"mode", "flag", "verbose", "channel", "kind", "strategy", "strict", "dry_run", "cmd", "command"}
TEMPORAL_NAMES = {"init", "initialize", "bootstrap", "setup", "start", "shutdown", "cleanup", "teardown", "load", "save", "flush", "close"}
STAMP_ARG_NAMES = {"payload", "record", "ticket", "session", "item", "entry"}
DEFAULT_LABELS_RELATIVE_PATH = Path("LABELS") / "module_complexity_labels.json"


def _read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp949"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_rel(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace(os.sep, "/")


def _merge_lines(lines: Iterable[int], total_lines: int) -> List[Dict[str, int]]:
    vals = sorted({x for x in lines if 1 <= x <= total_lines})
    if not vals:
        return []
    spans: List[Tuple[int, int]] = []
    start = prev = vals[0]
    for line in vals[1:]:
        if line <= prev + 1:
            prev = line
            continue
        spans.append((start, prev + 1))
        start = prev = line
    spans.append((start, prev + 1))
    return [{"start_line_number": s, "end_line_number": e} for s, e in spans]


def _merge_ranges(ranges: Iterable[Tuple[int, int]], total_lines: int) -> List[Dict[str, int]]:
    vals = sorted((max(1, s), min(total_lines + 1, e)) for s, e in ranges if s < e)
    if not vals:
        return []
    out: List[List[int]] = []
    for s, e in vals:
        if not out or s > out[-1][1] + 1:
            out.append([s, e])
        else:
            out[-1][1] = max(out[-1][1], e)
    return [{"start_line_number": s, "end_line_number": e} for s, e in out]


def _full_file_span(total_lines: int) -> Dict[str, int]:
    return {"start_line_number": 1, "end_line_number": total_lines + 1}


def _default_levels() -> Dict[str, List[str]]:
    return {"cohesion": list(COHESION_LEVELS), "coupling": list(COUPLING_LEVELS)}


def resolve_labels_path(project_root: Path, labels_json: Optional[str] = None) -> Path:
    if labels_json:
        return Path(labels_json).resolve()
    return (project_root / DEFAULT_LABELS_RELATIVE_PATH).resolve()


def load_project_spec(project_root: Path, labels_json: Optional[str] = None) -> Tuple[Dict, Path]:
    labels_path = resolve_labels_path(project_root, labels_json)
    if not labels_path.exists():
        raise FileNotFoundError(f"Module complexity labels file not found: {labels_path}")
    payload = _load_json(labels_path)
    if "projects" in payload:
        project_name = project_root.resolve().name
        spec = (payload.get("projects", {}) or {}).get(project_name)
        if not spec:
            raise ValueError(f"Project {project_name!r} not found in labels manifest: {labels_path}")
        project_payload = {
            "schema_version": payload.get("schema_version", "1.0"),
            "levels": payload.get("levels") or _default_levels(),
            "project_name": project_name,
            **spec,
        }
        return project_payload, labels_path
    project_payload = {
        "schema_version": payload.get("schema_version", "1.0"),
        "levels": payload.get("levels") or _default_levels(),
        "project_name": payload.get("project_name") or project_root.resolve().name,
        "package": payload.get("package"),
        "project_intent": payload.get("project_intent", {}),
        "module_labels": payload.get("module_labels", {}),
    }
    return project_payload, labels_path


@dataclass
class CallSite:
    line: int
    target_module: Optional[str]
    target_name: Optional[str]
    arg_kinds: List[str] = field(default_factory=list)
    kw_names: List[str] = field(default_factory=list)
    arg_names: List[str] = field(default_factory=list)
    literal_values: List[str] = field(default_factory=list)


@dataclass
class FunctionInfo:
    name: str
    start: int
    end: int
    call_lines: List[int] = field(default_factory=list)
    if_lines: List[Tuple[int, int]] = field(default_factory=list)
    attr_lines: List[int] = field(default_factory=list)
    subscript_lines: List[int] = field(default_factory=list)
    return_lines: List[int] = field(default_factory=list)
    assigned_names: Set[str] = field(default_factory=set)
    used_names: Set[str] = field(default_factory=set)


@dataclass
class ModuleFacts:
    module_name: str
    rel_file_path: str
    total_lines: int
    imports: Dict[str, str] = field(default_factory=dict)
    functions: Dict[str, FunctionInfo] = field(default_factory=dict)
    callsites: List[CallSite] = field(default_factory=list)
    top_level_assign_lines: List[int] = field(default_factory=list)
    global_names: Set[str] = field(default_factory=set)
    global_access_lines: List[int] = field(default_factory=list)
    private_foreign_access_lines: List[int] = field(default_factory=list)
    external_access_lines: List[int] = field(default_factory=list)
    branch_lines: List[Tuple[int, int]] = field(default_factory=list)
    attr_lines: List[int] = field(default_factory=list)
    subscript_lines: List[int] = field(default_factory=list)
    return_lines: List[int] = field(default_factory=list)


def _root_name(node: ast.AST) -> Optional[str]:
    cur = node
    while isinstance(cur, ast.Attribute):
        cur = cur.value
    return cur.id if isinstance(cur, ast.Name) else None


def _classify_expr(node: ast.AST) -> Tuple[str, Optional[str], Optional[str]]:
    if isinstance(node, ast.Constant):
        return "literal", None, repr(node.value)
    if isinstance(node, ast.Name):
        return "name", node.id, None
    if isinstance(node, ast.Attribute):
        return "attribute", _root_name(node), None
    if isinstance(node, (ast.Dict, ast.List, ast.Set, ast.Tuple)):
        return "composite_literal", None, type(node).__name__
    if isinstance(node, ast.Call):
        return "call_result", None, None
    return type(node).__name__.lower(), None, None


def _module_name_for_file(file_path: Path, package_root: Path) -> str:
    rel = file_path.resolve().relative_to(package_root.resolve())
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


def analyze_project(project_root: Path) -> Dict[str, ModuleFacts]:
    src_dir = project_root / "src"
    py_files = sorted(p for p in src_dir.rglob("*.py") if p.is_file())
    package_modules = {_module_name_for_file(p, src_dir) for p in py_files}
    facts: Dict[str, ModuleFacts] = {}
    for file_path in py_files:
        module_name = _module_name_for_file(file_path, src_dir)
        source = _read_text(file_path)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        mod = ModuleFacts(module_name=module_name, rel_file_path=_safe_rel(file_path, project_root), total_lines=len(source.splitlines()))
        func_stack: List[FunctionInfo] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    local = alias.asname or name.split(".")[-1]
                    if name in package_modules or any(m.startswith(name + ".") for m in package_modules):
                        mod.imports[local] = name
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    parts = module_name.split(".")
                    base_parts = parts[:-node.level] if node.level <= len(parts) else parts
                    if node.module:
                        base_parts.extend(node.module.split("."))
                    base = ".".join(base_parts)
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    candidate = f"{base}.{alias.name}" if base else alias.name
                    mod.imports[local] = candidate if candidate in package_modules else base
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                mod.functions[node.name] = FunctionInfo(node.name, node.lineno, getattr(node, "end_lineno", node.lineno) + 1)
            elif isinstance(node, ast.Assign):
                if any(isinstance(t, ast.Name) for t in node.targets):
                    mod.top_level_assign_lines.append(node.lineno)
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            mod.global_names.add(t.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                mod.top_level_assign_lines.append(node.lineno)
                mod.global_names.add(node.target.id)
            elif isinstance(node, ast.Name):
                if node.id in mod.global_names:
                    mod.global_access_lines.append(node.lineno)
            elif isinstance(node, ast.Attribute):
                mod.attr_lines.append(node.lineno)
                root = _root_name(node.value)
                if root in mod.imports and node.attr.startswith("_"):
                    mod.private_foreign_access_lines.append(node.lineno)
                text = f"{root}.{node.attr}" if root else node.attr
                if "os.environ" in text or node.attr in {"read_text", "write_text", "read_bytes", "write_bytes", "open"}:
                    mod.external_access_lines.append(node.lineno)
            elif isinstance(node, ast.Subscript):
                mod.subscript_lines.append(node.lineno)
            elif isinstance(node, ast.Return):
                mod.return_lines.append(node.lineno)
            elif isinstance(node, (ast.If, ast.Match)):
                mod.branch_lines.append((node.lineno, getattr(node, "end_lineno", node.lineno) + 1))
            elif isinstance(node, ast.Call):
                target_module = target_name = None
                if isinstance(node.func, ast.Name):
                    target_name = node.func.id
                    target_module = mod.imports.get(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    target_name = node.func.attr
                    root = _root_name(node.func.value)
                    target_module = mod.imports.get(root) if root else None
                arg_kinds: List[str] = []
                arg_names: List[str] = []
                literal_values: List[str] = []
                for arg in node.args:
                    kind, name, literal = _classify_expr(arg)
                    arg_kinds.append(kind)
                    if name:
                        arg_names.append(name)
                    if literal:
                        literal_values.append(literal)
                mod.callsites.append(CallSite(node.lineno, target_module, target_name, arg_kinds, [kw.arg for kw in node.keywords if kw.arg], arg_names, literal_values))
        facts[module_name] = mod
    return facts


def build_cohesion_candidate_row(level: str, facts: ModuleFacts) -> Dict:
    ranges: List[Tuple[int, int]] = []
    lines: List[int] = []
    if level == "functional":
        ranges.extend((fi.start, fi.end) for fi in facts.functions.values()); lines.extend(facts.return_lines)
    elif level == "logical":
        ranges.extend(facts.branch_lines); lines.extend(cs.line for cs in facts.callsites if any(k in CONTROL_NAMES for k in cs.kw_names))
    elif level == "temporal":
        ranges.extend((fi.start, fi.end) for fi in facts.functions.values() if any(tok in fi.name.lower() for tok in TEMPORAL_NAMES)); lines.extend(facts.top_level_assign_lines + facts.external_access_lines)
    elif level == "procedural":
        ranges.extend((fi.start, fi.end) for fi in facts.functions.values() if len(fi.call_lines) >= 2 or (fi.end - fi.start) > 4); lines.extend(cs.line for cs in facts.callsites)
    elif level == "communicational":
        lines.extend(facts.attr_lines + facts.subscript_lines)
    elif level == "sequential":
        lines.extend(cs.line for cs in facts.callsites[:2]); ranges.extend((fi.start, fi.end) for fi in facts.functions.values())
    elif level == "coincidental":
        ranges.extend((fi.start, fi.end) for fi in facts.functions.values()); lines.extend(facts.top_level_assign_lines)
    evidence = _merge_ranges(ranges, facts.total_lines) if ranges else _merge_lines(lines, facts.total_lines)
    if not evidence:
        evidence = [_full_file_span(facts.total_lines)]
    return {"type": "ModuleComplexity", "name": f"Module Cohesion - {level.title()}", "description": f"Module-level cohesion evidence for {facts.module_name}", "file_path": facts.rel_file_path, "start_line_number": 1, "end_line_number": facts.total_lines + 1, "severity": "Info", "evidence_lines": evidence}


def build_coupling_candidate_rows(all_facts: Dict[str, ModuleFacts]) -> List[Dict]:
    pair_buckets: Dict[Tuple[Tuple[str, str], str], Tuple[Set[int], Set[int]]] = {}
    base_buckets: Dict[Tuple[str, str], Tuple[Set[int], Set[int]]] = {}

    def _add(bucket_map, left_path, left_lines, right_path, right_lines, level=None):
        pair = (left_path, right_path) if left_path <= right_path else (right_path, left_path)
        key = (pair, level) if level is not None else pair
        if key not in bucket_map:
            bucket_map[key] = (set(), set())
        left_set, right_set = bucket_map[key]
        if left_path == pair[0]:
            left_set.update(left_lines); right_set.update(right_lines)
        else:
            left_set.update(right_lines); right_set.update(left_lines)

    def _peer_lines(peer: ModuleFacts, target_name: Optional[str]) -> List[int]:
        if target_name and target_name in peer.functions:
            fi = peer.functions[target_name]
            return [fi.start]
        return [1]

    for facts in all_facts.values():
        for cs in facts.callsites:
            if cs.target_module and cs.target_module in all_facts:
                peer = all_facts[cs.target_module]
                _add(base_buckets, facts.rel_file_path, [cs.line], peer.rel_file_path, _peer_lines(peer, cs.target_name))
                _add(pair_buckets, facts.rel_file_path, [cs.line], peer.rel_file_path, _peer_lines(peer, cs.target_name), "message")
                is_control = any(k in CONTROL_NAMES for k in cs.kw_names) or any(v in {"True", "False"} for v in cs.literal_values)
                is_stamp = any(k in {"composite_literal", "call_result"} for k in cs.arg_kinds) or any(name in STAMP_ARG_NAMES for name in cs.arg_names)
                if is_control:
                    _add(pair_buckets, facts.rel_file_path, [cs.line], peer.rel_file_path, _peer_lines(peer, cs.target_name), "control")
                elif is_stamp:
                    _add(pair_buckets, facts.rel_file_path, [cs.line], peer.rel_file_path, _peer_lines(peer, cs.target_name), "stamp")
                else:
                    _add(pair_buckets, facts.rel_file_path, [cs.line], peer.rel_file_path, _peer_lines(peer, cs.target_name), "data")
        if facts.global_access_lines:
            for module_name in facts.imports.values():
                peer = all_facts.get(module_name)
                if peer and peer.global_names:
                    _add(base_buckets, facts.rel_file_path, facts.global_access_lines, peer.rel_file_path, peer.top_level_assign_lines or [1])
                    _add(pair_buckets, facts.rel_file_path, facts.global_access_lines, peer.rel_file_path, peer.top_level_assign_lines or [1], "common")
        if facts.private_foreign_access_lines:
            for module_name in facts.imports.values():
                peer = all_facts.get(module_name)
                if peer:
                    defs = [fi.start for name, fi in peer.functions.items() if name.startswith("_")] or [1]
                    _add(base_buckets, facts.rel_file_path, facts.private_foreign_access_lines, peer.rel_file_path, defs)
                    _add(pair_buckets, facts.rel_file_path, facts.private_foreign_access_lines, peer.rel_file_path, defs, "content")
        if facts.external_access_lines:
            _add(base_buckets, facts.rel_file_path, facts.external_access_lines, facts.rel_file_path, facts.external_access_lines)
            _add(pair_buckets, facts.rel_file_path, facts.external_access_lines, facts.rel_file_path, facts.external_access_lines, "external")

    rows: List[Dict] = []
    path_to_facts = {f.rel_file_path: f for f in all_facts.values()}
    for pair, (left_base, right_base) in sorted(base_buckets.items()):
        left_facts = path_to_facts[pair[0]]
        right_facts = path_to_facts[pair[1]]
        base_left = _merge_lines(left_base or {1}, left_facts.total_lines) or [_full_file_span(left_facts.total_lines)]
        base_right = _merge_lines(right_base or {1}, right_facts.total_lines) or [_full_file_span(right_facts.total_lines)]
        for level in COUPLING_LEVELS:
            specific = pair_buckets.get((pair, level))
            left_spans = _merge_lines(specific[0], left_facts.total_lines) if specific else base_left
            right_spans = _merge_lines(specific[1], right_facts.total_lines) if specific else base_right
            rows.append({"type": "ModuleComplexity", "name": f"Module Coupling - {level.title()}", "description": f"Module-pair coupling evidence for {pair[0]} and {pair[1]}", "severity": "Info", "files": [{"name": pair[0], "evidence_lines": left_spans or base_left}, {"name": pair[1], "evidence_lines": right_spans or base_right}]})
    return rows


def build_universe_rows_for_project(project_root: Path, project_spec: Dict) -> List[Dict]:
    all_facts = analyze_project(project_root)
    rows: List[Dict] = []
    for facts in sorted(all_facts.values(), key=lambda x: x.rel_file_path):
        for level in COHESION_LEVELS:
            rows.append(build_cohesion_candidate_row(level, facts))
    rows.extend(build_coupling_candidate_rows(all_facts))
    return rows


def module_complexity_key(row: Dict) -> Tuple:
    smell_name = str(row.get("name", "")).strip()
    if smell_name.startswith("Module Cohesion - "):
        return (smell_name, "cohesion", row.get("file_path"))
    if smell_name.startswith("Module Coupling - "):
        files = row.get("files", []) or []
        return (smell_name, "coupling", tuple(sorted(str(item.get("name")) for item in files[:2])))
    return (smell_name, json.dumps(row, sort_keys=True))


def select_positive_rows(universe_rows: Sequence[Dict], project_spec: Dict) -> List[Dict]:
    selected: List[Dict] = []
    for short_name, labels in (project_spec.get("module_labels", {}) or {}).items():
        suffix = f"/{short_name}.py"
        cohesion = labels.get("cohesion")
        if cohesion:
            smell_name = f"Module Cohesion - {str(cohesion).title()}"
            for row in universe_rows:
                if row.get("name") == smell_name and str(row.get("file_path", "")).endswith(suffix):
                    selected.append(row)
                    break
        for level in labels.get("coupling", []) or []:
            smell_name = f"Module Coupling - {str(level).title()}"
            for row in universe_rows:
                if row.get("name") != smell_name:
                    continue
                names = [str(item.get("name", "")) for item in row.get("files", [])[:2]]
                if any(name.endswith(suffix) for name in names):
                    selected.append(row)
    seen, ordered = set(), []
    for row in selected:
        key = module_complexity_key(row)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(row)
    return ordered


def build_positive_rows_for_project(project_root: Path, project_spec: Dict) -> List[Dict]:
    return select_positive_rows(build_universe_rows_for_project(project_root, project_spec), project_spec)


def _write_project_report(project_root: Path, labels_json: Optional[str], output_dir: Path) -> Dict:
    project_spec, labels_path = load_project_spec(project_root, labels_json)
    rows = build_positive_rows_for_project(project_root, project_spec)
    project_name = project_root.resolve().name
    out_path = output_dir / f"{project_name}.module_complexity_report.json"
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "rows": len(rows),
        "output": str(out_path),
        "labels": str(labels_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build module complexity report rows.")
    parser.add_argument("project_root", help="Path to a single project directory")
    parser.add_argument("--labels-json", help="Optional labels path. If omitted, uses project-local LABELS/module_complexity_labels.json")
    parser.add_argument("--output-dir", required=True, help="Directory to write per-project report JSON files")
    args = parser.parse_args()

    out_root = Path(args.output_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    summary = {}
    project_root = Path(args.project_root).resolve()
    summary[project_root.name] = _write_project_report(project_root, args.labels_json, out_root)
    (out_root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
