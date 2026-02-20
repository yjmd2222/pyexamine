from typing import Dict, List, Optional, Tuple


GROUP_COMPONENTS: Dict[str, List[str]] = {
    "A01": ["self.external_dependencies", "self.import_lines", "self.module_dependencies"],
    "A02": ["self.function_lines", "self.module_functions"],
    "A03": ["networkx", "self.import_lines", "self.module_dependencies"],
    "A04": ["self.class_lines", "self.class_method_lines", "self.class_methods", "self.class_modules"],
    "A05": ["self.api_call_lines", "self.api_usage"],
    "A06": ["raw_file_text", "self.module_dependencies"],
    "S01": ["self.dependency_graph", "self.import_lines"],
    "S02": ["raw_file_text", "self.module_info"],
    "S03": ["ast.BoolOp", "ast.ExceptHandler", "ast.For", "ast.If", "ast.While", "ast.walk", "self.class_info"],
    "S04": ["ast.Attribute", "ast.Name", "ast.walk", "self.class_info"],
    "S05": ["ast.For", "ast.FunctionDef", "ast.If", "ast.Name", "ast.Try", "ast.While", "ast.walk", "self.class_info"],
    "S06": ["ast.Attribute", "ast.Call", "ast.Name", "ast.walk", "self.class_info"],
    "S07": ["networkx", "self.class_info"],
    "S08": ["self.class_info"],
    "S09": ["self.class_info", "self.module_info"],
    "S10": ["ast.Name", "self.class_info"],
    "S11": ["ast.For", "ast.If", "ast.Try", "ast.While", "ast.walk", "self.class_info"],
    "S12": ["ast.Attribute", "ast.walk", "self.class_info"],
    "S13": ["ast.BoolOp", "ast.ExceptHandler", "ast.For", "ast.If", "ast.Try", "ast.While", "ast.walk", "self.class_info"],
    "C01": ["astroid", "astroid_module", "nodes.Attribute", "nodes.Call", "nodes.ClassDef", "nodes.Name"],
    "C02": ["astroid", "astroid_module", "nodes.ClassDef", "nodes.Name"],
    "C03": ["astroid", "astroid_module", "nodes.AssignName", "nodes.ClassDef", "nodes.FunctionDef", "nodes.Name"],
    "C04": ["astroid", "astroid_module", "raw_file_text", "regex", "self.file_content"],
    "C05": ["astroid", "astroid_module", "nodes.Attribute", "nodes.Call", "nodes.FunctionDef", "nodes.Name"],
    "C06": ["astroid", "astroid_module", "nodes.Assign", "nodes.FunctionDef", "nodes.Return", "regex"],
    "C07": ["astroid", "astroid_module", "nodes.Attribute", "nodes.Call", "nodes.ClassDef", "nodes.FunctionDef", "nodes.Name", "nodes.Return"],
    "C08": ["astroid", "astroid_module", "nodes.AssignAttr", "nodes.Attribute", "nodes.Call", "nodes.ClassDef", "nodes.Name"],
    "C09": ["astroid", "astroid_module", "nodes.Assign", "nodes.Attribute", "nodes.Call", "nodes.ClassDef", "nodes.FunctionDef", "nodes.Name", "nodes.Return"],
    "C10": ["astroid", "astroid_module", "nodes.Assign", "nodes.ClassDef", "nodes.Return"],
    "C11": ["astroid", "astroid_module", "nodes.Call", "nodes.ClassDef", "nodes.FunctionDef", "nodes.Name", "raw_file_text", "self.file_content"],
    "C12": ["astroid", "astroid_module", "nodes.ClassDef", "nodes.FunctionDef"],
    "C13": ["astroid", "astroid_module", "nodes.Attribute", "nodes.ClassDef", "nodes.FunctionDef"],
    "C14": ["astroid", "astroid_module", "nodes.Attribute", "nodes.Call", "nodes.ClassDef", "nodes.Name", "nodes.Return"],
    "C15": ["astroid", "astroid_module", "nodes.Call", "nodes.ClassDef", "nodes.FunctionDef", "nodes.Name"],
    "C16": ["astroid", "astroid_module", "nodes.ClassDef", "nodes.Name", "nodes.Pass"],
    "C17": ["astroid", "astroid_module", "nodes.Call", "nodes.Compare", "nodes.ExceptHandler", "nodes.Expr", "nodes.If"],
    "C18": ["astroid", "astroid_module", "nodes.AssignName", "nodes.Attribute", "nodes.Call", "nodes.ClassDef", "nodes.Const", "nodes.Expr", "nodes.FunctionDef", "nodes.Name"],
}

# (group_id, role0_source, role1_source, role2_source)
SMELL_ROLES: Dict[str, Tuple[str, str, str, str]] = {
    "Hub-like Dependency": ("A01", "file_range", "outgoing_evidence", "files_incoming"),
    "Unstable Dependency": ("A01", "file_range", "outgoing_evidence", "files_incoming"),
    "Scattered Functionality": ("A02", "files_evidence", "none", "none"),
    "Potential Redundant Abstractions": ("A02", "files_evidence", "none", "none"),
    "Cyclic Dependency": ("A03", "files_file_ranges", "files_evidence", "none"),
    "God Object": ("A04", "node_range", "evidence_lines", "none"),
    "Potential Improper API Usage": ("A05", "file_range", "evidence_lines", "none"),
    "Orphan Module": ("A06", "file_range", "none", "none"),
    "High Fan-out": ("S01", "file_range", "evidence_lines", "none"),
    "High Fan-in": ("S01", "file_range", "none", "files_evidence"),
    "High Lines of Code (LOC)": ("S02", "file_range", "evidence_lines", "none"),
    "Long File": ("S02", "file_range", "none", "none"),
    "High Number of Classes per Module": ("S03", "file_range", "evidence_lines", "none"),
    "High Cyclomatic Complexity": ("S03", "node_range", "none", "none"),
    "High Weight of a Class (WAC)": ("S04", "node_range", "evidence_lines", "none"),
    "High Lack of Cohesion of Methods (LCOM)": ("S04", "node_range", "evidence_lines", "none"),
    "Too Many Branches": ("S05", "node_range", "none", "none"),
    "High Coupling Between Object Classes (CBO)": ("S06", "node_range", "evidence_lines", "none"),
    "Deep Inheritance Tree": ("S07", "node_range", "none", "files_evidence"),
    "High Message Passing Coupling (MPC)": ("S08", "node_range", "evidence_lines", "none"),
    "High Number of classes per Project": ("S09", "files_evidence", "none", "none"),
    "High Number of Methods (NOM)": ("S10", "node_range", "methods_functions", "none"),
    "High Response for a Class (RFC)": ("S11", "node_range", "evidence_lines", "none"),
    "Large Class (SIZE2)": ("S12", "node_range", "evidence_lines", "none"),
    "High Weighted Methods per Class (WMPC)": ("S13", "node_range", "evidence_lines", "none"),
    "Long Method": ("C11", "node_range", "none", "none"),
    "Large Class": ("C09", "node_range", "evidence_lines", "none"),
    "Primitive Obsession": ("C03", "node_range", "none", "none"),
    "Long Parameter List": ("C12", "node_range", "none", "none"),
    "Data Clumps": ("C03", "methods_functions", "none", "none"),
    "Switch Statements": ("C17", "node_range", "none", "none"),
    "Temporary Field": ("C18", "node_range", "evidence_lines", "none"),
    "Alternative Classes with Different Interfaces": ("C01", "classes", "methods_functions", "none"),
    "Potential Divergent Change": ("C01", "node_range", "evidence_lines", "none"),
    "Parallel Inheritance Hierarchies": ("C02", "classes", "none", "none"),
    "Potential Shotgun Surgery": ("C15", "lines", "none", "none"),
    "Excessive Comments": ("C04", "evidence_lines", "none", "none"),
    "Duplicate Code": ("C06", "lines", "none", "none"),
    "Data Class": ("C02", "node_range", "evidence_lines", "none"),
    "Dead Code": ("C05", "node_range", "none", "none"),
    "Lazy Class": ("C10", "node_range", "none", "none"),
    "Speculative Generality": ("C16", "node_range", "evidence_lines", "none"),
    "Feature Envy": ("C07", "node_range", "evidence_lines", "none"),
    "Inappropriate Intimacy": ("C08", "node_range", "evidence_lines", "none"),
    "Message Chains": ("C13", "node_range", "none", "none"),
    "Middle Man": ("C14", "node_range", "evidence_lines", "none"),
}


def _span(start_line_number: int, end_line_number: int) -> Dict[str, int]:
    return {"start_line_number": int(start_line_number), "end_line_number": int(end_line_number)}


def _safe_span(start_line_number: Optional[int], end_line_number: Optional[int]) -> Optional[Dict[str, int]]:
    if start_line_number is None or end_line_number is None:
        return None
    if end_line_number <= start_line_number:
        return None
    return _span(start_line_number, end_line_number)


def _line_spans_to_dict(line_spans) -> List[Dict[str, int]]:
    spans = []
    for item in (line_spans or []):
        start = getattr(item, "start_line_number", None)
        end = getattr(item, "end_line_number", None)
        if start is None and isinstance(item, dict):
            start = item.get("start_line_number")
            end = item.get("end_line_number")
        safe = _safe_span(start, end)
        if safe:
            spans.append(safe)
    return spans


def _file_span(file_path: Optional[str]) -> Dict[str, int]:
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                total_lines = sum(1 for _ in handle)
            if total_lines > 0:
                return _span(1, total_lines + 1)
        except OSError:
            pass
    return _span(1, 2)


def _single_file_role(file_path: Optional[str], spans: List[Dict[str, int]]) -> List[Dict]:
    name = file_path or "Unknown"
    return [{"name": name, "evidence_lines": spans}] if spans else [{"name": name, "evidence_lines": [_span(1, 2)]}]


def _from_named_lines(named_items) -> List[Dict]:
    by_name: Dict[str, List[Dict[str, int]]] = {}
    for item in (named_items or []):
        name = getattr(item, "name", None)
        start = getattr(item, "start_line_number", None)
        end = getattr(item, "end_line_number", None)
        if name is None and isinstance(item, dict):
            name = item.get("name")
            start = item.get("start_line_number")
            end = item.get("end_line_number")
        if not name:
            continue
        safe = _safe_span(start, end)
        if safe:
            by_name.setdefault(name, []).append(safe)
    return [{"name": name, "evidence_lines": spans} for name, spans in by_name.items()]


def _files_role(files, field_name: str) -> List[Dict]:
    role = []
    for entry in (files or []):
        name = getattr(entry, "name", None) or "Unknown"
        spans = _line_spans_to_dict(getattr(entry, field_name, []))
        role.append({"name": name, "evidence_lines": spans})
    return role


def _roles_from_payload(payload, file_path: Optional[str], role_source: str) -> List[Dict]:
    payload_file = getattr(payload, "file_path", None) or file_path
    if role_source == "none":
        return []
    if role_source == "file_range":
        return _single_file_role(payload_file, [_file_span(payload_file)])
    if role_source == "node_range":
        span = _safe_span(getattr(payload, "start_line_number", None), getattr(payload, "end_line_number", None))
        if span:
            return _single_file_role(payload_file, [span])
        return _single_file_role(payload_file, [_file_span(payload_file)])
    if role_source == "evidence_lines":
        return _single_file_role(payload_file, _line_spans_to_dict(getattr(payload, "evidence_lines", [])))
    if role_source == "outgoing_evidence":
        return _single_file_role(payload_file, _line_spans_to_dict(getattr(payload, "outgoing_evidence_lines", [])))
    if role_source == "lines":
        return _single_file_role(payload_file, _line_spans_to_dict(getattr(payload, "lines", [])))
    if role_source == "methods_functions":
        return _from_named_lines(getattr(payload, "methods_functions", []))
    if role_source == "classes":
        return _from_named_lines(getattr(payload, "classes", []))
    if role_source == "files_evidence":
        return _files_role(getattr(payload, "files", []), "evidence_lines")
    if role_source == "files_incoming":
        return _files_role(getattr(payload, "files", []), "incoming_evidence_lines")
    if role_source == "files_file_ranges":
        role = []
        for entry in (getattr(payload, "files", []) or []):
            name = getattr(entry, "name", None) or "Unknown"
            role.append({"name": name, "evidence_lines": [_file_span(name)]})
        return role
    return []


def build_ast_graph_for_payload(payload, file_path: Optional[str] = None) -> Optional[Dict]:
    smell_name = getattr(payload, "name", None)
    if smell_name not in SMELL_ROLES:
        return None

    group_id, role0_source, role1_source, role2_source = SMELL_ROLES[smell_name]
    role0 = _roles_from_payload(payload, file_path, role0_source)
    role1 = _roles_from_payload(payload, file_path, role1_source)
    role2 = _roles_from_payload(payload, file_path, role2_source)

    return {
        "group_id": group_id,
        "components": GROUP_COMPONENTS.get(group_id, []),
        "roles": {"role0": role0, "role1": role1, "role2": role2},
        "component_slice": {},
    }


def emit_a01_hub_like(detector, module_name, payload, in_degree, out_degree, external_dep_count, total_modules):
    ast_graph = build_ast_graph_for_payload(payload, file_path=getattr(payload, "file_path", None)) or {}
    ast_graph["component_slice"] = {
        "metrics": {
            "in_degree": in_degree,
            "out_degree": out_degree,
            "external_dependency_count": external_dep_count,
            "total_modules_in_group": total_modules,
        },
        "graph": {
            "predecessors": sorted(detector.module_dependencies.predecessors(module_name)),
            "successors": sorted(detector.module_dependencies.successors(module_name)),
            "external_dependencies": sorted([dep for _, dep in detector.external_dependencies.get(module_name, set())]),
        },
    }
    return ast_graph


def emit_s01_fanout(detector, module_name, payload, significant_deps, threshold):
    ast_graph = build_ast_graph_for_payload(payload, file_path=getattr(payload, "file_path", None)) or {}
    ast_graph["component_slice"] = {
        "metrics": {"significant_dependencies": significant_deps, "threshold": threshold},
        "graph": {"successors": sorted(detector.dependency_graph.successors(module_name))},
    }
    return ast_graph


def emit_s01_fanin(detector, module_name, payload, fanin, threshold):
    ast_graph = build_ast_graph_for_payload(payload, file_path=getattr(payload, "file_path", None)) or {}
    if ast_graph.get("roles", {}).get("role2"):
        for entry in ast_graph["roles"]["role2"]:
            module_or_path = entry["name"]
            entry["name"] = detector.file_paths.get(module_or_path, module_or_path)
    ast_graph["component_slice"] = {
        "metrics": {"fanin": fanin, "threshold": threshold},
        "graph": {"predecessors": sorted(detector.dependency_graph.predecessors(module_name))},
    }
    return ast_graph


def emit_c11_long_method(payload, actual_lines, threshold):
    ast_graph = build_ast_graph_for_payload(payload, file_path=getattr(payload, "file_path", None)) or {}
    ast_graph["component_slice"] = {
        "metrics": {"actual_lines": actual_lines, "threshold": threshold},
        "ast_summary": {
            "class_name": getattr(payload, "class_name", ""),
            "method_function": getattr(payload, "method_function", ""),
        },
    }
    return ast_graph


def emit_c17_switch_statements(payload, condition_count, threshold, is_guard_clause, is_type_check):
    ast_graph = build_ast_graph_for_payload(payload, file_path=getattr(payload, "file_path", None)) or {}
    ast_graph["component_slice"] = {
        "metrics": {"condition_count": condition_count, "threshold": threshold},
        "flags": {"is_guard_clause": is_guard_clause, "is_type_check": is_type_check},
    }
    return ast_graph
