import astroid
from astroid import nodes, exceptions as astroid_exceptions
import os
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations, product
import re
import logging
from typing import Any, Optional
from .exceptions import CodeAnalysisError
from .smell_templates import (
    CodeFileLevelEvidenceLinesPayload,
    FileClassLineSpansPayload,
    FileFunctionLineSpansPayload,
    FileLevelMethodFunctionLineSpansPayload,
    FileLineSpansPayload,
    FileMultipleClassesPayload,
    FlatChainPayload,
    FlatClassLevelPayload,
    FlatFunctionLevelPayload,
    FlatMethodFunctionPayload,
    FlatStatementPayload,
    LineSpan,
    NamedLineSpan,
    TemplateRenderer,
    render_code_file_level_evidence_lines,
    render_file_class_line_spans,
    render_file_function_line_spans,
    render_file_level_method_function_line_spans,
    render_file_line_spans,
    render_file_multiple_classes,
    render_flat_chain,
    render_flat_class_level,
    render_flat_function_level,
    render_flat_method_function,
    render_flat_statement,
)
from .ast_graph_emit import build_ast_graph_for_payload, emit_c11_long_method, emit_c17_switch_statements

# Set up logger
logger = logging.getLogger(__name__)

@dataclass
class CodeSmell:
    name: str
    description: str
    file_path: str
    module_class: str
    start_line_number: int
    end_line_number: int
    severity: str
    template_id: Optional[str] = None
    payload: Optional[Any] = None

class CodeSmellRecorder:
    def __init__(self, code_smells, template_renderer):
        self._code_smells = code_smells
        self._template_renderer = template_renderer

    def add_smell(self, name, description, file_path, module_class, start_line_number=None,
                  end_line_number=None, severity='medium'):
        """
        Add a detected smell to the list of code smells.
        
        Args:
            name (str): The name of the smell
            description (str): Description of the smell
            file_path (str): Path to the file containing the smell
            module_class (str): The module or class containing the smell
            start_line_number (int, optional): The start line number where the smell was detected
            end_line_number (int, optional): The ending line number (+1 for slicing)
            severity (str, optional): The severity level of the smell (default: 'medium')
        """
        self._code_smells.append(CodeSmell(
            name=name,
            description=description,
            file_path=file_path,
            module_class=module_class,
            start_line_number=start_line_number,
            end_line_number=end_line_number,
            severity=severity
        ))

    def record_smell(self, template_id, payload, file_path, module_class, start_line_number=None,
                     end_line_number=None, severity=None):
        if getattr(payload, "ast_graph", None) is None:
            payload.ast_graph = build_ast_graph_for_payload(payload, file_path=file_path)
        description = self._template_renderer.render(template_id, payload)
        resolved_severity = severity or getattr(payload, "severity", "medium")
        self._code_smells.append(CodeSmell(
            name=payload.name,
            description=description,
            file_path=file_path,
            module_class=module_class,
            start_line_number=start_line_number,
            end_line_number=end_line_number,
            severity=resolved_severity,
            template_id=template_id,
            payload=payload
        ))

class CodeSmellDetector:
    """
    A class to detect various code smells in Python source code.

    This class analyzes Python source code for common code smells and anti-patterns,
    providing a comprehensive report on potential issues in the codebase.

    Attributes:
        code_smells (list): A list to store detected code smells.
        thresholds (dict): A dictionary of threshold values for various code smell detections.
        file_content (list): A list of strings representing the content of the analyzed file.
    """

    def __init__(self, thresholds):
        """
        Initialize the CodeSmellDetector with given thresholds.

        Args:
            thresholds (dict): A dictionary of threshold values for various code smell detections.
        """
        self.code_smells = []
        self._template_renderer = TemplateRenderer({
            "flat_function_level": render_flat_function_level,
            "flat_method_function": render_flat_method_function,
            "flat_statement": render_flat_statement,
            "flat_chain": render_flat_chain,
            "file_line_spans": render_file_line_spans,
            "file_class_line_spans": render_file_class_line_spans,
            "file_level_method_function_line_spans": render_file_level_method_function_line_spans,
            "file_function_line_spans": render_file_function_line_spans,
            "file_multiple_classes": render_file_multiple_classes,
            "flat_class_level": render_flat_class_level,
            "code_file_level_evidence_lines": render_code_file_level_evidence_lines,
        })
        self._smell_recorder = CodeSmellRecorder(self.code_smells, self._template_renderer)
        self.add_smell = self._smell_recorder.add_smell
        self.thresholds = thresholds

    def detect_smells(self, file_path):
        """
        Detect code smells in the given file.
        """
        detection_methods = [
            (self.detect_long_methods, "detect_long_methods"),
            (self.detect_large_classes, "detect_large_classes"),
            (self.detect_primitive_obsession, "detect_primitive_obsession"),
            (self.detect_long_parameter_lists, "detect_long_parameter_lists"),
            (self.detect_data_clumps, "detect_data_clumps"),
            (self.detect_switch_statements, "detect_switch_statements"),
            (self.detect_temporary_fields, "detect_temporary_fields"),
            (self.detect_alternative_classes, "detect_alternative_classes"),
            (self.detect_divergent_change, "detect_divergent_change"),
            (self.detect_parallel_inheritance, "detect_parallel_inheritance"),
            (self.detect_shotgun_surgery, "detect_shotgun_surgery"),
            (self.detect_comments, "detect_comments"),
            (self.detect_duplicate_code, "detect_duplicate_code"),
            (self.detect_data_class, "detect_data_class"),
            (self.detect_dead_code, "detect_dead_code"),
            (self.detect_lazy_class, "detect_lazy_class"),
            (self.detect_speculative_generality, "detect_speculative_generality"),
            (self.detect_feature_envy, "detect_feature_envy"),
            (self.detect_inappropriate_intimacy, "detect_inappropriate_intimacy"),
            (self.detect_message_chains, "detect_message_chains"),
            (self.detect_middle_man, "detect_middle_man")
        ]

        try:
            content = None
            for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp949']:
                try:
                    with open(file_path, 'r', encoding=enc, errors='ignore') as file:
                        content = file.read()
                    break
                except UnicodeDecodeError:
                    continue
            if content is None:
                raise CodeAnalysisError(
                    message="File encoding error: could not decode with utf-8/utf-8-sig/latin-1/cp949",
                    file_path=file_path
                )

            try:
                module = astroid.parse(content)
            except astroid_exceptions.AstroidSyntaxError as e:
                logger.error(f"Syntax error in {file_path}: {str(e)}")
                raise CodeAnalysisError(
                    message=f"Failed to parse Python file: {str(e)}",
                    file_path=file_path,
                    start_line_number=getattr(e, 'lineno', None)
                )
            
            self.file_content = content.split('\n')
            self._node_spans = {}
            for node in module.body:
                if isinstance(node, (nodes.FunctionDef, nodes.ClassDef)):
                    start = getattr(node, "lineno", None)
                    end = getattr(node, "end_lineno", None) or getattr(node, "tolineno", None) or start
                    if start is not None:
                        self._node_spans[(node.name, start)] = end
            
            # Run each detection method
            for detect_method, method_name in detection_methods:
                try:
                    logger.debug(f"Running {method_name} on {file_path}")
                    detect_method(module, file_path)
                except Exception as e:
                    logger.error(
                        f"Error in {method_name} analyzing {file_path}: {str(e)}", 
                        exc_info=True
                    )
                    raise CodeAnalysisError(
                        message=f"Error in {method_name}: {str(e)}",
                        file_path=file_path,
                        function_name=method_name
                    )
                
        except CodeAnalysisError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error analyzing {file_path}: {str(e)}", exc_info=True)
            raise CodeAnalysisError(
                message=f"Unexpected error: {str(e)}",
                file_path=file_path
            )

    def detect_long_methods(self, module, file_path):
        """
        Detect long methods in the given module.
        """
        def detect(node, file_path):
            # Skip property decorators and simple getter/setters
            if node.decorators:
                is_property = False
                for decorator in node.decorators.nodes:
                    # Handle both direct name and call decorators
                    if isinstance(decorator, nodes.Name) and decorator.name == 'property':
                        is_property = True
                        break
                    elif isinstance(decorator, nodes.Call) and isinstance(decorator.func, nodes.Name) and decorator.func.name == 'property':
                        is_property = True
                        break
                if is_property:
                    return
            
            # Count non-empty, non-comment lines
            actual_lines = 0
            for line_no in range(node.fromlineno, node.tolineno + 1):
                if line_no <= len(self.file_content):
                    line = self.file_content[line_no - 1].strip()
                    if line and not line.startswith('#'):
                        actual_lines += 1
            
            if actual_lines > self.thresholds["LONG_METHOD_LINES"]:
                threshold = self.thresholds["LONG_METHOD_LINES"]
                payload = FlatMethodFunctionPayload(
                    type="Code",
                    name="Long Method",
                    description=f"'{node.name}' has {actual_lines} lines in {file_path} at line {node.lineno}",
                    file_path=file_path,
                    class_name=node.parent.name if isinstance(node.parent, nodes.ClassDef) else "",
                    method_function=node.name,
                    start_line_number=node.lineno,
                    end_line_number=node.tolineno + 1,
                    severity="medium"
                )
                payload.ast_graph = emit_c11_long_method(
                    payload=payload,
                    actual_lines=actual_lines,
                    threshold=threshold,
                )
                self._smell_recorder.record_smell(
                    "flat_method_function",
                    payload,
                    file_path=file_path,
                    module_class=node.name,
                    start_line_number=node.lineno,
                    end_line_number=node.tolineno + 1
                )
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                for node_child in node.body:
                    if isinstance(node_child, nodes.FunctionDef):
                        detect(node_child, file_path)
            elif isinstance(node, nodes.FunctionDef):
                detect(node, file_path)

    def detect_large_classes(self, module, file_path):
        """
        Detect large classes in the given module.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                # Skip data classes and exception classes
                is_dataclass = False
                if node.decorators:
                    for decorator in node.decorators.nodes:
                        if isinstance(decorator, nodes.Name) and decorator.name == 'dataclass':
                            is_dataclass = True
                            break
                        elif isinstance(decorator, nodes.Call):
                            if isinstance(decorator.func, nodes.Name) and decorator.func.name == 'dataclass':
                                is_dataclass = True
                                break
                        elif isinstance(decorator, nodes.Attribute):
                            if decorator.attrname == 'dataclass':
                                is_dataclass = True
                                break

                if (is_dataclass or
                    any(base.name.endswith('Exception') for base in node.bases if isinstance(base, nodes.Name))):
                    continue

                # Count non-trivial methods (exclude simple getters/setters)
                non_trivial_methods = []
                for method in node.body:
                    if isinstance(method, nodes.FunctionDef):
                        # Skip magic methods
                        if method.name.startswith('__') and method.name.endswith('__'):
                            continue
                        # Skip simple getters/setters
                        if len(method.body) == 1 and isinstance(method.body[0], (nodes.Return, nodes.Assign)):
                            continue
                        non_trivial_methods.append(method)

                if len(non_trivial_methods) > self.thresholds["LARGE_CLASS_METHODS"]:
                    payload = FlatClassLevelPayload(
                        type="Code",
                        name="Large Class",
                        description=f"'{node.name}' has {len(non_trivial_methods)} non-trivial methods in {file_path}",
                        file_path=file_path,
                        class_name=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        severity="medium"
                    )
                    self._smell_recorder.record_smell(
                        "flat_class_level",
                        payload,
                        file_path=file_path,
                        module_class=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1
                    )

    def detect_primitive_obsession(self, module, file_path):
        """
        Detect primitive obsession in the given module.
        """
        def detect(node, file_path):
            primitives = []
            total_args = len(node.args.args)
            
            # Skip if it's a small number of total arguments
            if total_args <= self.thresholds.get('PRIMITIVE_MIN_ARGS', 3):
                return

            for i, arg in enumerate(node.args.args):
                if isinstance(arg, nodes.AssignName):
                    # Skip 'self' parameter in methods
                    if i == 0 and arg.name == 'self':
                        continue
                    
                    if i < len(node.args.annotations):
                        arg_type = node.args.annotations[i]
                        if (isinstance(arg_type, nodes.Name) and 
                            arg_type.name in ['int', 'str', 'float', 'bool']):
                            primitives.append(arg)

            # Calculate primitive ratio
            primitive_ratio = len(primitives) / (total_args - 1 if 'self' in node.args.args[0].name else total_args)
            if (len(primitives) > self.thresholds["PRIMITIVE_OBSESSION_COUNT"] and 
                primitive_ratio > self.thresholds.get('PRIMITIVE_RATIO_THRESHOLD', 0.7)):
                payload = FlatMethodFunctionPayload(
                    type="Code",
                    name="Primitive Obsession",
                    description=f"'{node.name}' has {len(primitives)} primitive parameters in {file_path}",
                    file_path=file_path,
                    class_name=node.parent.name if isinstance(node.parent, nodes.ClassDef) else "",
                    method_function=node.name,
                    start_line_number=node.lineno,
                    end_line_number=node.tolineno + 1,
                    severity='medium'
                )
                self._smell_recorder.record_smell(
                    "flat_method_function",
                    payload,
                    file_path=file_path,
                    module_class=node.name,
                    start_line_number=node.lineno,
                    end_line_number=node.tolineno + 1,
                    severity='medium'
                )
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                for node_child in node.body:
                    if isinstance(node_child, nodes.FunctionDef):
                        detect(node_child, file_path)
            elif isinstance(node, nodes.FunctionDef):
                detect(node, file_path)

    def detect_long_parameter_lists(self, module, file_path):
        """
        Detect long parameter lists in the given module.
        """
        def detect(node, file_path):
            args = node.args.args
            
            # Skip if it's a constructor
            if node.name == '__init__':
                return
            
            # Skip 'self' in method parameter count
            if args and args[0].name == 'self':
                args = args[1:]
            
            # Check for **kwargs or *args
            has_var_args = node.args.vararg is not None
            has_kwargs = node.args.kwarg is not None
            
            # Reduce severity if function has variable arguments
            threshold = (
                self.thresholds["LONG_PARAMETER_LIST"] + 2 
                if (has_var_args or has_kwargs) 
                else self.thresholds["LONG_PARAMETER_LIST"]
            )

            if len(args) > threshold:
                payload = FlatMethodFunctionPayload(
                    type="Code",
                    name="Long Parameter List",
                    description=f"'{node.name}' has {len(args)} parameters in {file_path}",
                    file_path=file_path,
                    class_name=node.parent.name if isinstance(node.parent, nodes.ClassDef) else "",
                    method_function=node.name,
                    start_line_number=node.lineno,
                    end_line_number=node.tolineno + 1,
                    severity='medium'
                )
                self._smell_recorder.record_smell(
                    "flat_method_function",
                    payload,
                    file_path=file_path,
                    module_class=node.name,
                    start_line_number=node.lineno,
                    end_line_number=node.tolineno + 1,
                    severity='medium'
                )
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                for node_child in node.body:
                    if isinstance(node_child, nodes.FunctionDef):
                        detect(node_child, file_path)
            elif isinstance(node, nodes.FunctionDef):
                detect(node, file_path)

    def detect_data_clumps(self, module, file_path):
        """
        Detect data clumps in the given module.
        """
        parameter_groups = defaultdict(list)
        def find_parameter_groups(node, parameter_groups):
            if isinstance(node, nodes.FunctionDef):
                # Skip if it's a constructor or property
                if node.name == '__init__' or (node.decorators and 
                    any(isinstance(d, nodes.Name) and d.name == 'property' 
                        for d in node.decorators.nodes)):
                    return
                
                # Get parameters excluding self
                params = [arg.name for arg in node.args.args 
                         if isinstance(arg, nodes.AssignName) and arg.name != 'self']
                
                # Skip if too few parameters
                if len(params) < self.thresholds["DATA_CLUMPS_THRESHOLD"]:
                    return
                    
                # Create combinations of parameters that appear together
                min_combo = self.thresholds.get('DATA_CLUMP_MIN_COMBO_SIZE', 3)
                for size in range(min_combo, len(params) + 1):
                    for combo in combinations(sorted(params), size):
                        parameter_groups[combo].append({
                            "name": node.name,
                            "start_line_number": node.lineno,
                            "end_line_number": node.tolineno + 1
                        })
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                for node_child in node.body:
                    if isinstance(node_child, nodes.FunctionDef):
                        find_parameter_groups(node_child, parameter_groups)
            elif isinstance(node, nodes.FunctionDef):
                find_parameter_groups(node, parameter_groups)
        
        for params, functions in parameter_groups.items():
            # Only report if parameters appear together in multiple functions
            # and represent a significant portion of each function's parameters
            if (len(functions) > 1 and 
                len(params) >= self.thresholds["DATA_CLUMPS_THRESHOLD"]):
                function_lines = ", ".join(
                    f"{d['name']} (lines {d['start_line_number']}-{d['end_line_number']})"
                    for d in functions
                )
                payload = FileLevelMethodFunctionLineSpansPayload(
                    type="Code",
                    name="Data Clumps",
                    description=f"Parameters {', '.join(params)} appear together in functions: {function_lines} in {file_path}",
                    file_path=file_path,
                    methods_functions=[
                        NamedLineSpan(
                            name=d["name"],
                            start_line_number=d["start_line_number"],
                            end_line_number=d["end_line_number"]
                        )
                        for d in functions
                    ],
                    severity='medium'
                )
                self._smell_recorder.record_smell(
                    "file_level_method_function_line_spans",
                    payload,
                    file_path=file_path,
                    module_class=', '.join(d["name"] for d in functions),
                    severity='medium'
                )

    def detect_switch_statements(self, module, file_path):
        """
        Detect switch statements in the given module.
        """
        def count_conditions(node):
            count = 1  # Start with 1 for the initial if
            for else_node in node.orelse:
                if isinstance(else_node, nodes.If):
                    count += 1
                elif isinstance(else_node, nodes.Expr):
                    continue  # Skip comments or docstrings
            return count

        for node in module.nodes_of_class(nodes.If):
            # Skip simple if/else statements
            if not node.orelse:
                continue
                
            # Check if this is part of a try/except block
            if any(isinstance(parent, nodes.ExceptHandler) for parent in node.node_ancestors()):
                continue
                
            condition_count = count_conditions(node)
            
            # Check for common valid patterns
            is_guard_clause = len(node.body) <= 2 and isinstance(node.test, nodes.Compare)
            is_type_check = isinstance(node.test, nodes.Call) and getattr(node.test.func, 'name', '') == 'isinstance'
            
            if (condition_count > self.thresholds["COMPLEX_CONDITIONAL"] and 
                not is_guard_clause and 
                not is_type_check):
                threshold = self.thresholds["COMPLEX_CONDITIONAL"]
                payload = FlatStatementPayload(
                    type="Code",
                    name="Switch Statements",
                    description=f"Complex conditional with {condition_count} branches at line {node.lineno} in {file_path}",
                    file_path=file_path,
                    start_line_number=node.lineno,
                    end_line_number=node.tolineno + 1,
                    severity='medium'
                )
                payload.ast_graph = emit_c17_switch_statements(
                    payload=payload,
                    condition_count=condition_count,
                    threshold=threshold,
                    is_guard_clause=is_guard_clause,
                    is_type_check=is_type_check,
                )
                self._smell_recorder.record_smell(
                    "flat_statement",
                    payload,
                    file_path=file_path,
                    module_class=None,
                    start_line_number=node.lineno,
                    end_line_number=node.tolineno + 1,
                    severity='medium'
                )

    def detect_temporary_fields(self, module, file_path):
        """
        Detect temporary fields in the given module.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                # Skip data classes and exception classes
                is_dataclass = False
                if node.decorators:
                    for decorator in node.decorators.nodes:
                        if isinstance(decorator, nodes.Name) and decorator.name == 'dataclass':
                            is_dataclass = True
                            break
                        elif isinstance(decorator, nodes.Call):
                            if isinstance(decorator.func, nodes.Name) and decorator.func.name == 'dataclass':
                                is_dataclass = True
                                break
                        elif isinstance(decorator, nodes.Attribute):
                            if decorator.attrname == 'dataclass':
                                is_dataclass = True
                                break

                if (is_dataclass or
                    any(base.name.endswith('Exception') for base in node.bases if isinstance(base, nodes.Name))):
                    continue

                init_fields = set()
                used_fields = set()
                cached_fields = set()  # For fields that might be used for caching
                
                for child in node.body:
                    if isinstance(child, nodes.FunctionDef):
                        if child.name == '__init__':
                            for target in child.nodes_of_class(nodes.AssignName):
                                # Check if field has a comment indicating it's for caching
                                if any(isinstance(sibling, nodes.Expr) and 
                                      isinstance(sibling.value, nodes.Const) and 
                                      'cache' in str(sibling.value.value).lower() 
                                      for sibling in child.body):
                                    cached_fields.add(target.name)
                                else:
                                    init_fields.add(target.name)
                        else:
                            used_fields.update(
                                n.attrname for n in child.nodes_of_class(nodes.Attribute)
                                if isinstance(n.expr, nodes.Name) and n.expr.name == 'self'
                            )
                
                # Exclude common patterns and cached fields
                temp_fields = (init_fields - used_fields - cached_fields - 
                             {'logger', 'config', 'cache', '_cache'})
                
                if len(temp_fields) >= self.thresholds["TEMPORARY_FIELD_THRESHOLD"]:
                    payload = FlatClassLevelPayload(
                        type="Code",
                        name="Temporary Field",
                        description=f"Potentially unused fields {', '.join(temp_fields)} in class '{node.name}' at line {node.lineno} in {file_path}",
                        file_path=file_path,
                        class_name=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        severity='low'
                    )
                    self._smell_recorder.record_smell(
                        "flat_class_level",
                        payload,
                        file_path=file_path,
                        module_class=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        severity='low'
                    )

    def detect_alternative_classes(self, module, file_path):
        """
        Detect alternative classes with different interfaces in the given module.
        """
        class_methods = defaultdict(list)
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                # Skip data classes, exceptions, and abstract base classes
                is_excluded = False
                if node.decorators:
                    for decorator in node.decorators.nodes:
                        if isinstance(decorator, nodes.Name) and decorator.name in {'dataclass', 'abstractmethod'}:
                            is_excluded = True
                            break
                        elif isinstance(decorator, nodes.Call):
                            if isinstance(decorator.func, nodes.Name) and decorator.func.name in {'dataclass', 'abstractmethod'}:
                                is_excluded = True
                                break
                        elif isinstance(decorator, nodes.Attribute):
                            if decorator.attrname in {'dataclass', 'abstractmethod'}:
                                is_excluded = True
                                break

                if (is_excluded or
                    any(base.name.endswith(('Exception', 'ABC')) 
                        for base in node.bases if isinstance(base, nodes.Name))):
                    continue
                
                # Get non-private methods excluding standard methods
                methods = frozenset(
                    n.name for n in node.mymethods()
                    if not n.name.startswith('_') and
                    n.name not in {'__init__', '__str__', '__repr__', '__eq__', '__hash__'}
                )
                
                # Skip if too few methods
                if len(methods) < 2:
                    continue
                    
                class_methods[methods].append({
                    "name": node.name,
                    "start_line_number": node.lineno,
                    "end_line_number": node.tolineno + 1,
                })
        
        for methods, classes in class_methods.items():
            if len(classes) >= self.thresholds["ALTERNATIVE_CLASSES_THRESHOLD"]:
                # Check if classes share a common base class
                class_names = [entry["name"] for entry in classes]
                class_nodes = [node for node in module.body
                             if isinstance(node, nodes.ClassDef) and node.name in class_names]
                share_base_class = len({base.name for node in class_nodes 
                                      for base in node.bases if isinstance(base, nodes.Name)}) > 0
                
                if not share_base_class:
                    class_ranges = ", ".join(
                        f"{entry['name']} (lines {entry['start_line_number']}-{entry['end_line_number']})"
                        for entry in classes
                    )
                    payload = FileMultipleClassesPayload(
                        type="Code",
                        name="Alternative Classes with Different Interfaces",
                        description=f"Classes {class_ranges} share similar methods {', '.join(methods)} in {file_path}",
                        file_path=file_path,
                        classes=[
                            NamedLineSpan(
                                name=entry["name"],
                                start_line_number=entry["start_line_number"],
                                end_line_number=entry["end_line_number"]
                            )
                            for entry in classes
                        ],
                        severity='medium'
                    )
                    self._smell_recorder.record_smell(
                        "file_multiple_classes",
                        payload,
                        file_path=file_path,
                        module_class=', '.join(class_names),
                        severity='medium'
                    )

    def detect_divergent_change(self, module, file_path):
        """
        Detect divergent change in the given module.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                # Skip data classes, exceptions, and utility classes
                is_dataclass = False
                if node.decorators:
                    for decorator in node.decorators.nodes:
                        if isinstance(decorator, nodes.Name) and decorator.name == 'dataclass':
                            is_dataclass = True
                            break
                        elif isinstance(decorator, nodes.Call):
                            if isinstance(decorator.func, nodes.Name) and decorator.func.name == 'dataclass':
                                is_dataclass = True
                                break
                        elif isinstance(decorator, nodes.Attribute):
                            if decorator.attrname == 'dataclass':
                                is_dataclass = True
                                break

                if (is_dataclass or
                    any(base.name.endswith('Exception') for base in node.bases if isinstance(base, nodes.Name)) or
                    node.name.endswith(('Utils', 'Helper', 'Mixin'))):
                    continue

                # Get method prefixes, excluding common patterns
                method_prefixes = []
                methods = []
                for method in node.mymethods():
                    # Skip magic methods, properties, and private methods
                    is_property = False
                    if method.decorators:
                        for decorator in method.decorators.nodes:
                            if isinstance(decorator, nodes.Name) and decorator.name == 'property':
                                is_property = True
                                break
                            elif isinstance(decorator, nodes.Call):
                                if isinstance(decorator.func, nodes.Name) and decorator.func.name == 'property':
                                    is_property = True
                                    break
                            elif isinstance(decorator, nodes.Attribute):
                                if decorator.attrname == 'property':
                                    is_property = True
                                    break

                    if (method.name.startswith('__') or is_property or method.name.startswith('_')):
                        continue
                        
                    prefix = method.name.split('_')[0]
                    # Skip common CRUD and utility prefixes
                    if prefix not in {'get', 'set', 'is', 'has', 'validate', 'create', 'update', 'delete'}:
                        method_prefixes.append(prefix)
                        methods.append({
                            "name": method.name,
                            "start_line_number": method.lineno,
                            "end_line_number": method.tolineno + 1,
                        })

                unique_prefixes = set(method_prefixes)
                if (len(unique_prefixes) > self.thresholds["DIVERGENT_CHANGE_PREFIXES"] and
                    len(method_prefixes) > self.thresholds["DIVERGENT_CHANGE_METHODS"]):
                    payload = FileClassLineSpansPayload(
                        type="Code",
                        name="Potential Divergent Change",
                        description=f"Class '{node.name}' has {len(unique_prefixes)} different method prefixes: {', '.join(unique_prefixes)} in {file_path}",
                        file_path=file_path,
                        class_name=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno,
                        evidence_lines=[
                            LineSpan(
                                start_line_number=entry["start_line_number"],
                                end_line_number=entry["end_line_number"]
                            )
                            for entry in methods
                        ],
                        severity='medium'
                    )
                    self._smell_recorder.record_smell(
                        "file_class_line_spans",
                        payload,
                        file_path=file_path,
                        module_class=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno,
                        severity='medium'
                    )

    def detect_parallel_inheritance(self, module, file_path):
        """
        Detect parallel inheritance hierarchies in the given module.
        """
        class_hierarchies = defaultdict(list)
        class_info = {}  # Store class information for better analysis
        class_entries = {}

        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                class_entries[node.name] = {
                    "name": node.name,
                    "start_line_number": node.lineno,
                    "end_line_number": node.tolineno + 1
                }

        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                # Skip exception classes and mixins
                if (any(base.name.endswith('Exception') for base in node.bases if isinstance(base, nodes.Name)) or
                    node.name.endswith('Mixin')):
                    continue
                    
                for base in node.bases:
                    if isinstance(base, nodes.Name):
                        class_hierarchies[base.name].append(node.name)
                        # Store method names for similarity comparison
                        class_info[node.name] = {m.name for m in node.mymethods() 
                                           if not m.name.startswith('_')}
        
        if len(class_hierarchies) > 1:
            parallel_hierarchies = []
            for (base1, h1), (base2, h2) in combinations(class_hierarchies.items(), 2):
                if len(h1) > 1 and len(h2) > 1:
                    # Check for naming patterns
                    if any(c1.replace(h1[0], '') == c2.replace(h2[0], '')
                          for c1, c2 in product(h1, h2)):
                        # Check for method similarity
                        if (h1[0] in class_info and h2[0] in class_info and 
                            (class_info[h1[0]] or class_info[h2[0]])):  # Ensure at least one set has methods
                            union_size = len(class_info[h1[0]] | class_info[h2[0]])
                            if union_size > 0:  # Prevent division by zero
                                similarity = len(class_info[h1[0]] & class_info[h2[0]]) / union_size
                                if similarity > self.thresholds.get('PARALLEL_INHERITANCE_SIMILARITY_THRESHOLD', 0.3):  # More than configured percent similar methods
                                    parallel_hierarchies.append((base1, h1))
                                    parallel_hierarchies.append((base2, h2))

            if parallel_hierarchies:
                def build_hierarchy_evidences(base, classes):
                    evidences = []
                    for name in [base] + classes:
                        if name in class_entries:
                            evidences.append(class_entries[name])
                        else:
                            evidences.append({"name": name})
                    return evidences
                def format_hierarchy(evidences):
                    return " -> ".join(
                        f"{entry['name']} (lines {entry['start_line_number']}-{entry['end_line_number']})"
                        if "start_line_number" in entry else entry["name"]
                        for entry in evidences
                    )
                payload = FileMultipleClassesPayload(
                    type="Code",
                    name="Parallel Inheritance Hierarchies",
                    description=(
                        f"Parallel hierarchies detected: "
                        f"{' and '.join([format_hierarchy(build_hierarchy_evidences(base, h)) for base, h in parallel_hierarchies])} "
                        f"in {file_path}"
                    ),
                    file_path=file_path,
                    classes=[
                        NamedLineSpan(
                            name=entry["name"],
                            start_line_number=entry["start_line_number"],
                            end_line_number=entry["end_line_number"]
                        )
                        for entry in class_entries.values()
                        if "start_line_number" in entry and "end_line_number" in entry
                    ],
                    severity='high'
                )
                self._smell_recorder.record_smell(
                    "file_multiple_classes",
                    payload,
                    file_path=file_path,
                    module_class=None,
                    severity='high'
                )

    def detect_shotgun_surgery(self, module, file_path):
        """
        Detect potential shotgun surgery in the given module.
        """
        method_calls = defaultdict(list)
        for node in module.body:
            for call in node.nodes_of_class(nodes.Call):
                if isinstance(call.func, nodes.Name):
                    # Skip common utility methods and logging
                    exclude_names = set(self.thresholds.get('SHOTGUN_SURGERY_EXCLUDE_NAMES', ['log', 'print', 'str', 'len', 'isinstance', 'super']))
                    if call.func.name.lower() in exclude_names:
                        continue
                        
                    # Store both line number and context
                    context = None # call name
                    for parent in call.node_ancestors():
                        if isinstance(parent, (nodes.FunctionDef, nodes.ClassDef)):
                            context = parent.name
                            break
                    method_calls[call.func.name].append({
                        "call_name": context,
                        "start_line_number": call.lineno,
                        "end_line_number": call.tolineno + 1,
                    })
        
        for method, calls in method_calls.items():
            unique_contexts = len(set(d["call_name"] for d in calls))
            if (len(calls) > self.thresholds["SHOTGUN_SURGERY_CALLS"] and
                unique_contexts > self.thresholds["SHOTGUN_SURGERY_CONTEXTS"]):
                payload = FileLineSpansPayload(
                    type="Code",
                    name="Potential Shotgun Surgery",
                    description=f"Method '{method}' called in {unique_contexts} different contexts across {len(calls)} locations in {file_path}",
                    file_path=file_path,
                    lines=[
                        LineSpan(
                            start_line_number=entry["start_line_number"],
                            end_line_number=entry["end_line_number"]
                        )
                        for entry in calls
                    ],
                    severity='high'
                )
                self._smell_recorder.record_smell(
                    "file_line_spans",
                    payload,
                    file_path=file_path,
                    module_class=method,
                    severity='high'
                )

    def detect_comments(self, module, file_path):
        """
        Detect excessive comments in the given module and file.

        Args:
            module (astroid.Module): The AST module being analyzed
            file_path (str): Path to the file being analyzed
        """
        comment_line_re = re.compile(r'^\s*#')
        comment_blocks = []
        current_block = []
        code_lines = 0
        
        for i, line in enumerate(self.file_content):
            stripped_line = line.strip()
            is_regex_comment = comment_line_re.match(line) is not None
            if is_regex_comment:
                current_block.append(i)
            else:
                if current_block:
                    comment_blocks.append(current_block)
                    current_block = []
                if stripped_line and not stripped_line.startswith('"""'):
                    code_lines += 1
        
        if current_block:
            comment_blocks.append(current_block)
        
        # Filter out license headers and module docstrings
        if comment_blocks and comment_blocks[0][0] == 0:
            comment_blocks.pop(0)
        
        # Calculate meaningful metrics
        comment_lines = sum(len(block) for block in comment_blocks)
        comment_ratio = comment_lines / max(code_lines, 1)
        large_comment_blocks = sum(1 for block in comment_blocks if len(block) > 5)
        comment_line_spans = [
            LineSpan(start_line_number=block[0] + 1, end_line_number=block[-1] + 2)
            for block in comment_blocks
        ]
        
        if (comment_ratio > self.thresholds["EXCESSIVE_COMMENTS_RATIO"] and
            large_comment_blocks > self.thresholds["LARGE_COMMENT_BLOCKS"]):
            payload = CodeFileLevelEvidenceLinesPayload(
                type="Code",
                name="Excessive Comments",
                description=f"File has {comment_ratio:.1%} comment ratio with {large_comment_blocks} large comment blocks in {file_path}",
                file_path=file_path,
                evidence_lines=comment_line_spans,
                severity='low'
            )
            self._smell_recorder.record_smell(
                "code_file_level_evidence_lines",
                payload,
                file_path=file_path,
                module_class=None,
                severity='low'
            )

    def detect_duplicate_code(self, module, file_path):
        """
        Detect duplicate code in the given module.
        """
        def normalize_code(node):
            """Normalize code by removing variable names and whitespace."""
            code = node.as_string()
            # Replace variable names with placeholders
            code = re.sub(r'\b[a-zA-Z_]\w*\b', 'VAR', code)
            # Remove whitespace and comments
            code = re.sub(r'\s+', '', code)
            code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
            return code

        code_blocks = defaultdict(list)
        for node in module.body:
            if isinstance(node, nodes.FunctionDef):
                # Skip small functions and test methods
                if (len(node.body) < self.thresholds["DUPLICATE_CODE_MIN_LINES"] or
                    node.name.startswith('test_')):
                    continue

                # Skip simple getter/setter methods
                if len(node.body) == 1 and isinstance(node.body[0], (nodes.Return, nodes.Assign)):
                    continue

                normalized_code = normalize_code(node)
                code_blocks[normalized_code].append({
                    "name": node.name,
                    "length": len(node.body),
                    "start_line_number": node.lineno,
                    "end_line_number": node.tolineno + 1,
                })

        for block, functions in code_blocks.items():
            if len(functions) >= self.thresholds["DUPLICATE_CODE_THRESHOLD"]:
                total_lines = sum(d["length"] for d in functions)
                payload = FileLineSpansPayload(
                    type="Code",
                    name="Duplicate Code",
                    description=f"Similar code found in functions: {', '.join(d['name'] for d in functions)} ({total_lines} total lines) in {file_path}",
                    file_path=file_path,
                    lines=[
                        LineSpan(
                            start_line_number=entry["start_line_number"],
                            end_line_number=entry["end_line_number"]
                        )
                        for entry in functions
                    ],
                    severity='high'
                )
                self._smell_recorder.record_smell(
                    "file_line_spans",
                    payload,
                    file_path=file_path,
                    module_class=', '.join(d["name"] for d in functions),
                    severity='high'
                )

    def detect_data_class(self, module, file_path):
        """
        Detect data classes in the given module.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                # Skip if it's already a dataclass or an exception
                if (any(decorator.name == 'dataclass' for decorator in node.decorators.nodes) if node.decorators else False or
                    any(base.name.endswith('Exception') for base in node.bases if isinstance(base, nodes.Name))):
                    continue

                methods = list(node.mymethods())

                # Skip empty classes or those with no methods
                if not methods:
                    continue

                # Count different types of methods
                getters = 0
                setters = 0
                others = 0

                code_blocks = defaultdict(list)
                kind = None
                for method in methods:
                    if method.name.startswith('__'):
                        continue  # Skip magic methods
                    elif method.name.startswith('get_') and len(method.body) == 1:
                        getters += 1
                        kind = "getters"
                    elif method.name.startswith('set_') and len(method.body) == 1:
                        setters += 1
                        kind = "setters"
                    else:
                        others += 1
                        kind = "others"
                    if kind != "others":
                        code_blocks[method.name].append({
                            "kind": kind,
                            "start_line_number": method.lineno,
                            "end_line_number": method.tolineno + 1
                        })

                # Only flag if class is predominantly getters/setters
                if (others == 0 and getters + setters >= self.thresholds["DATA_CLASS_METHODS"] and
                    not node.name.endswith(('DTO', 'Model', 'Entity', 'Record'))):  # Skip known data structures
                    evidence_lines = [
                        LineSpan(
                            start_line_number=entry["start_line_number"],
                            end_line_number=entry["end_line_number"]
                        )
                        for block in code_blocks.values()
                        for entry in block
                    ]
                    payload = FileClassLineSpansPayload(
                        type="Code",
                        name="Data Class",
                        description=f"Class '{node.name}' has {getters} getters and {setters} setters with no other methods in {file_path}",
                        file_path=file_path,
                        class_name=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        evidence_lines=evidence_lines,
                        severity='medium'
                    )
                    self._smell_recorder.record_smell(
                        "file_class_line_spans",
                        payload,
                        file_path=file_path,
                        module_class=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        severity='medium'
                    )

    def detect_dead_code(self, module, file_path):
        """
        Detect dead code in the given module.
        """
        defined_functions = {}  # Store function with its decorator info
        called_functions = set()
        exported_functions = set()  # Functions that might be used externally
        
        for node in module.body:
            if isinstance(node, nodes.FunctionDef):
                # Skip test functions and property methods
                if node.name.startswith('test_'):
                    continue
                if node.decorators:
                    deco_names = []
                    for deco in node.decorators.nodes:
                        name_attr = getattr(deco, "name", None) or getattr(deco, "attrname", None)
                        if name_attr:
                            deco_names.append(name_attr)
                    if 'property' in deco_names:
                        continue
                        
                # Check for decorators that suggest external use
                has_public_decorator = False
                if node.decorators:
                    for decorator in node.decorators.nodes:
                        if any(name in str(decorator) for name in ['api', 'route', 'endpoint', 'public', 'export']):
                            has_public_decorator = True
                            break

                defined_functions[node.name] = {
                    "name": node.name,
                    "has_public_decorator": has_public_decorator,
                    "start_line_number": node.lineno,
                    "end_line_number": node.tolineno + 1
                }

                # Check if function is likely to be exported
                if (not node.name.startswith('_') or  # Public functions
                    node.name.startswith('__')):      # Magic methods
                    exported_functions.add(node.name)

            # Collect function calls
            for call in node.nodes_of_class(nodes.Call):
                if isinstance(call.func, nodes.Name):
                    called_functions.add(call.func.name)
                elif isinstance(call.func, nodes.Attribute):
                    called_functions.add(call.func.attrname)

        # Consider only truly unused functions
        unused_functions = []
        for func_name, d in defined_functions.items():
            if (func_name not in called_functions and
                not d["has_public_decorator"] and
                func_name not in exported_functions and
                func_name not in unused_functions):
                unused_functions.append({
                    "name": func_name,
                    "start_line_number": d["start_line_number"],
                    "end_line_number": d["end_line_number"]
                })

        if len(unused_functions) >= self.thresholds["DEAD_CODE_THRESHOLD"]:
            for d in unused_functions:
                payload = FlatFunctionLevelPayload(
                    type="Code",
                    name="Dead Code",
                    description=f"Potentially unused function '{d['name']}' in {file_path}",
                    file_path=file_path,
                    function=d["name"],
                    start_line_number=d["start_line_number"],
                    end_line_number=d["end_line_number"],
                    severity='low'
                )
                self._smell_recorder.record_smell(
                    "flat_function_level",
                    payload,
                    file_path=file_path,
                    module_class=d["name"],
                    start_line_number=d["start_line_number"],
                    end_line_number=d["end_line_number"],
                    severity='low'
                )

    def detect_lazy_class(self, module, file_path):
        """
        Detect lazy classes in the given module.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                # Skip known valid small classes
                if (any(node.name.endswith(suffix) for suffix in 
                    ['Exception', 'Error', 'Mixin', 'Interface', 'Abstract', 'Base']) or
                    (node.decorators and any(d.name == 'dataclass' for d in node.decorators.nodes))):
                    continue
                
                # Count non-trivial methods
                methods = []
                for method in node.mymethods():
                    # Skip magic methods and simple getters/setters
                    if (method.name.startswith('__') or
                        (len(method.body) == 1 and isinstance(method.body[0], (nodes.Return, nodes.Assign)))):
                        continue
                    methods.append(method)
                
                # Check complexity of methods
                total_lines = sum(m.tolineno - m.fromlineno for m in methods)
                if (len(methods) <= self.thresholds["LAZY_CLASS_METHODS"] and
                    total_lines <= self.thresholds["LAZY_CLASS_LINES"]):
                    payload = FlatClassLevelPayload(
                        type="Code",
                        name="Lazy Class",
                        description=f"Class '{node.name}' has only {len(methods)} non-trivial methods with {total_lines} total lines in {file_path}",
                        file_path=file_path,
                        class_name=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        severity='low'
                    )
                    self._smell_recorder.record_smell(
                        "flat_class_level",
                        payload,
                        file_path=file_path,
                        module_class=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        severity='low'
                    )

    def detect_speculative_generality(self, module, file_path):
        """
        Detect speculative generality in the given module.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                # Skip legitimate abstract base classes
                if (any(base.name.endswith('ABC') for base in node.bases if isinstance(base, nodes.Name)) or
                    node.name.endswith(('Interface', 'Base', 'Abstract'))):
                    continue
                
                abstract_methods = []
                unused_params = []
                
                for method in node.mymethods():
                    # Check for empty/pass methods
                    if method.body and isinstance(method.body[0], nodes.Pass):
                        abstract_methods.append({
                            "name": method.name,
                            "start_line_number": method.lineno,
                            "end_line_number": method.tolineno + 1
                        })
                    
                    # Check for unused parameters
                    used_names = {n.name for n in method.nodes_of_class(nodes.Name)}
                    param_names = {arg.name for arg in method.args.args if arg.name != 'self'}
                    unused = param_names - used_names
                    if unused:
                        unused_params.extend({
                            "name": param,
                            "method": method.name,
                            "start_line_number": method.lineno,
                            "end_line_number": method.tolineno + 1
                        } for param in unused)
                
                if (len(abstract_methods) >= self.thresholds["SPECULATIVE_GENERALITY_THRESHOLD"] or
                    len(unused_params) >= self.thresholds["UNUSED_PARAMETERS_THRESHOLD"]):
                    description = []
                    if abstract_methods:
                        abstract_detail = ", ".join(
                            f"{d['name']} (lines {d['start_line_number']}-{d['end_line_number']})"
                            for d in abstract_methods
                        )
                        description.append(f"has {len(abstract_methods)} empty methods: {abstract_detail}")
                    if unused_params:
                        unused_detail = ", ".join(
                            f"{p['name']} in {p['method']} (lines {p['start_line_number']}-{p['end_line_number']})"
                            for p in unused_params
                        )
                        description.append(f"has {len(unused_params)} unused parameters: {unused_detail}")
                    evidence_lines = [
                        LineSpan(
                            start_line_number=entry["start_line_number"],
                            end_line_number=entry["end_line_number"]
                        )
                        for entry in abstract_methods + unused_params
                    ]
                    payload = FileClassLineSpansPayload(
                        type="Code",
                        name="Speculative Generality",
                        description=f"Class '{node.name}' {' and '.join(description)} in {file_path}",
                        file_path=file_path,
                        class_name=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        evidence_lines=evidence_lines,
                        severity='medium'
                    )
                    
                    self._smell_recorder.record_smell(
                        "file_class_line_spans",
                        payload,
                        file_path=file_path,
                        module_class=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        severity='medium'
                    )

    def detect_feature_envy(self, module, file_path):
        """
        Detect feature envy in the given module.
        """
        def detect(node, file_path):
            # Skip property methods and simple delegators
            is_property = False
            if node.decorators:
                for decorator in node.decorators.nodes:
                    if isinstance(decorator, nodes.Name) and decorator.name == 'property':
                        is_property = True
                        break
                    elif isinstance(decorator, nodes.Call):
                        if isinstance(decorator.func, nodes.Name) and decorator.func.name == 'property':
                            is_property = True
                            break
                    elif isinstance(decorator, nodes.Attribute):
                        if decorator.attrname == 'property':
                            is_property = True
                            break

            if (is_property or
                len(node.body) == 1 and isinstance(node.body[0], nodes.Return)):
                return
            
            # Track method calls by class
            class_calls = {}
            local_calls = {"count": 0, "lines": []}
            
            for sub_node in node.nodes_of_class(nodes.Attribute):
                if isinstance(sub_node.expr, nodes.Name):
                    if sub_node.expr.name == 'self':
                        local_calls["count"] += 1
                        local_calls["lines"].append({
                            "start_line_number": sub_node.lineno,
                            "end_line_number": sub_node.tolineno + 1
                        })
                    else:
                        # Skip common utility objects
                        if sub_node.expr.name.lower() not in {'logger', 'config', 'utils', 'helper'}:
                            call_data = class_calls.setdefault(
                                sub_node.expr.name, {"count": 0, "lines": []}
                            )
                            call_data["count"] += 1
                            call_data["lines"].append({
                                "start_line_number": sub_node.lineno,
                                "end_line_number": sub_node.tolineno + 1
                            })
            
            if class_calls:
                max_class, max_call_data = max(
                    class_calls.items(),
                    key=lambda item: item[1]["count"]
                )
                
                # Check if external calls significantly outnumber local calls
                if (max_call_data["count"] > self.thresholds["FEATURE_ENVY_CALLS"] and
                    max_call_data["count"] > local_calls["count"] * self.thresholds.get('FEATURE_ENVY_LOCAL_RATIO', 2.0)):
                    line_ranges = ", ".join(
                        f"{d['start_line_number']}-{d['end_line_number']}"
                        for d in max_call_data["lines"]
                    )
                    local_line_ranges = ", ".join(
                        f"{d['start_line_number']}-{d['end_line_number']}"
                        for d in local_calls["lines"]
                    )
                    payload = FileFunctionLineSpansPayload(
                        type="Code",
                        name="Feature Envy",
                        description=(
                            f"Method '{node.name}' makes {max_call_data['count']} calls to '{max_class}' "
                            f"at lines {line_ranges} but only {local_calls['count']} local calls "
                            f"at lines {local_line_ranges} in {file_path}"
                        ),
                        file_path=file_path,
                        function=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        evidence_lines=[
                            LineSpan(
                                start_line_number=entry["start_line_number"],
                                end_line_number=entry["end_line_number"]
                            )
                            for entry in max_call_data["lines"]
                        ],
                        severity='medium'
                    )
                    self._smell_recorder.record_smell(
                        "file_function_line_spans",
                        payload,
                        file_path=file_path,
                        module_class=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        severity='medium'
                    )
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                for node_child in node.body:
                    if isinstance(node_child, nodes.FunctionDef):
                        detect(node_child, file_path)
            elif isinstance(node, nodes.FunctionDef):
                detect(node, file_path)

    def detect_inappropriate_intimacy(self, module, file_path):
        """
        Detect inappropriate intimacy in the given module.
        """
        class_fields = defaultdict(set)
        class_methods = defaultdict(set)
        class_relationships = defaultdict(set)  # Track inheritance and composition
        class_ranges = {}

        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                # Skip data classes and utility classes
                is_dataclass = False
                if node.decorators:
                    for decorator in node.decorators.nodes:
                        if isinstance(decorator, nodes.Name) and decorator.name == 'dataclass':
                            is_dataclass = True
                            break
                        elif isinstance(decorator, nodes.Call):
                            if isinstance(decorator.func, nodes.Name) and decorator.func.name == 'dataclass':
                                is_dataclass = True
                                break
                        elif isinstance(decorator, nodes.Attribute):
                            if decorator.attrname == 'dataclass':
                                is_dataclass = True
                                break

                if (is_dataclass or node.name.endswith(('Utils', 'Helper', 'Factory'))):
                    continue

                # Store class methods and fields
                class_methods[node.name] = {
                    n.name for n in node.mymethods()
                    if not n.name.startswith('__')  # Skip magic methods
                }
                # astroid exposes inferred instance fields via instance_attrs
                instance_attrs = getattr(node, "instance_attrs", {}) or {}
                class_fields[node.name] = {
                    name for name in instance_attrs.keys()
                    if not name.startswith('_')  # Skip private fields
                }
                class_ranges[node.name] = (node.lineno, node.tolineno + 1)

                # Track inheritance relationships
                for base in node.bases:
                    if isinstance(base, nodes.Name):
                        class_relationships[node.name].add(base.name)

                # Track composition through assigned instance attributes
                for assignments in instance_attrs.values():
                    for assign in assignments:
                        if isinstance(assign, nodes.AssignAttr) and isinstance(assign.expr, nodes.Name):
                            class_relationships[node.name].add(assign.expr.name)

        for class_name, methods in class_methods.items():
            for other_class, other_fields in class_fields.items():
                if class_name != other_class:
                    # Skip if there's a valid relationship
                    if (other_class in class_relationships[class_name] or
                        class_name in class_relationships[other_class]):
                        continue

                    shared = len(methods.intersection(other_fields))
                    method_ratio = shared / len(methods) if methods else 0

                    # Track where class_name methods overlap with other_class fields
                    overlap_lines = []
                    # Track where class_name accesses attributes that match other_class fields
                    access_lines = []
                    class_node = next(
                        (n for n in module.body
                         if isinstance(n, nodes.ClassDef) and n.name == class_name),
                        None
                    )
                    if class_node:
                        for method in class_node.mymethods():
                            if method.name in other_fields:
                                overlap_lines.append({
                                    "start_line_number": method.lineno,
                                    "end_line_number": method.tolineno + 1
                                })
                            for attr in method.nodes_of_class(nodes.Attribute):
                                if attr.attrname in other_fields:
                                    access_lines.append({
                                        "start_line_number": attr.lineno,
                                        "end_line_number": attr.tolineno + 1
                                    })

                    if (shared > self.thresholds["INAPPROPRIATE_INTIMACY_SHARED"] and
                        method_ratio > self.thresholds.get('INAPPROPRIATE_INTIMACY_METHOD_RATIO', 0.3)):
                        merged_ranges = {
                            (d["start_line_number"], d["end_line_number"])
                            for d in overlap_lines
                        }
                        merged_ranges.update(
                            (d["start_line_number"], d["end_line_number"])
                            for d in access_lines
                        )
                        merged_sorted = sorted(merged_ranges)
                        collapsed_ranges = []
                        for start, end in merged_sorted:
                            if not collapsed_ranges:
                                collapsed_ranges.append([start, end])
                                continue
                            last_start, last_end = collapsed_ranges[-1]
                            if start <= last_end:
                                collapsed_ranges[-1][1] = max(last_end, end)
                            else:
                                collapsed_ranges.append([start, end])
                        merged_line_ranges = ", ".join(
                            f"{start}-{end}" for start, end in collapsed_ranges
                        )
                        payload = FileClassLineSpansPayload(
                            type="Code",
                            name="Inappropriate Intimacy",
                            description=f"Class '{class_name}' might be too intimate with '{other_class}' "
                                      f"({shared} shared members, {method_ratio:.1%} of methods) "
                                      f"at lines {merged_line_ranges} in {file_path}",
                            file_path=file_path,
                            class_name=class_name,
                            start_line_number=class_ranges[class_name][0],
                            end_line_number=class_ranges[class_name][1],
                            evidence_lines=[
                                LineSpan(start_line_number=start, end_line_number=end)
                                for start, end in collapsed_ranges
                            ],
                            severity='medium'
                        )
                        self._smell_recorder.record_smell(
                            "file_class_line_spans",
                            payload,
                            file_path=file_path,
                            module_class=class_name,
                            start_line_number=class_ranges[class_name][0],
                            end_line_number=class_ranges[class_name][1],
                            severity='medium'
                        )

    def detect_message_chains(self, module, file_path):
        """
        Detect message chains in the given module.
        """
        def get_chain_length(node):
            length = 0
            chain = []
            chain_lines = []
            current = node
            while isinstance(current, nodes.Attribute):
                length += 1
                chain.append(current.attrname)
                chain_lines.append({
                    "start_line_number": current.lineno,
                    "end_line_number": current.tolineno + 1
                })
                current = current.expr
            return length, chain, chain_lines

        def is_builder_pattern(chain):
            """Check if the chain follows builder pattern."""
            return all(name.startswith(('set_', 'with_', 'add_')) for name in chain)

        def is_common_pattern(chain):
            """Check if the chain is a common valid pattern."""
            common_patterns = {
                'logging': {'debug', 'info', 'warning', 'error', 'critical'},
                'paths': {'parent', 'name', 'suffix', 'stem'},
                'testing': {'assert_', 'expect', 'mock'},
                'db': {'query', 'filter', 'order_by', 'limit', 'all', 'first'}
            }
            return any(any(method in pattern for method in chain) 
                      for pattern in common_patterns.values())

        for node in module.nodes_of_class(nodes.Attribute):
            chain_length, chain, chain_lines = get_chain_length(node)
            
            # Skip if it's a valid pattern
            if (chain_length <= self.thresholds["MESSAGE_CHAIN_LENGTH"] or
                is_builder_pattern(chain) or
                is_common_pattern(chain)):
                continue

            # Get context for better description
            context = None
            for parent in node.node_ancestors():
                if isinstance(parent, (nodes.FunctionDef, nodes.ClassDef)):
                    context = parent.name
                    break

            merged_ranges = {
                (d["start_line_number"], d["end_line_number"])
                for d in chain_lines
            }
            merged_sorted = sorted(merged_ranges)
            collapsed_ranges = []
            for start, end in merged_sorted:
                if not collapsed_ranges:
                    collapsed_ranges.append([start, end])
                    continue
                last_start, last_end = collapsed_ranges[-1]
                if start <= last_end:
                    collapsed_ranges[-1][1] = max(last_end, end)
                else:
                    collapsed_ranges.append([start, end])
            line_ranges = ", ".join(
                f"{start}-{end}" for start, end in collapsed_ranges
            )

            payload = FlatChainPayload(
                type="Code",
                name="Message Chains",
                description=f"Long chain ({chain_length} calls: {' -> '.join(reversed(chain))}) "
                           f"at lines {line_ranges} in {context or 'unknown context'} in {file_path}",
                file_path=file_path,
                start_line_number=node.lineno,
                end_line_number=node.tolineno + 1,
                severity='medium'
            )
            self._smell_recorder.record_smell(
                "flat_chain",
                payload,
                file_path=file_path,
                module_class=context,
                start_line_number=node.lineno,
                end_line_number=node.tolineno + 1,
                severity='medium'
            )

    def detect_middle_man(self, module, file_path):
        """
        Detect middle man classes in the given module.
        """
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                # Skip known patterns and small classes
                if (node.name.endswith(('Proxy', 'Delegate', 'Adapter', 'Facade')) or
                    len(node.body) <= 3):  # Very small classes might be intentional adapters
                    continue

                methods = list(node.mymethods())
                total_methods = len(methods)
                
                if total_methods == 0:
                    continue

                delegating_methods = 0
                delegate_targets = defaultdict(list)

                for method in methods:
                    # Skip property methods and magic methods
                    is_property = False
                    if method.decorators:
                        for decorator in method.decorators.nodes:
                            if isinstance(decorator, nodes.Name) and decorator.name == 'property':
                                is_property = True
                                break
                            elif isinstance(decorator, nodes.Call):
                                if isinstance(decorator.func, nodes.Name) and decorator.func.name == 'property':
                                    is_property = True
                                    break
                            elif isinstance(decorator, nodes.Attribute):
                                if decorator.attrname == 'property':
                                    is_property = True
                                    break

                    if is_property or method.name.startswith('__'):
                        continue

                    # Check if method is just delegating
                    if len(method.body) == 1 and isinstance(method.body[0], nodes.Return):
                        return_value = method.body[0].value
                        if isinstance(return_value, nodes.Call):
                            delegating_methods += 1
                            # Track which object we're delegating to
                            if isinstance(return_value.func, nodes.Attribute):
                                delegate_targets[return_value.func.expr.as_string()].append(method.name)

                delegation_ratio = delegating_methods / total_methods if total_methods > 0 else 0
                if (delegation_ratio > self.thresholds["MIDDLE_MAN_RATIO"] and
                    len(delegate_targets) <= self.thresholds.get('MIDDLE_MAN_MAX_DELEGATE_TARGETS', 2)):
                    primary_delegate = max(delegate_targets.items(), key=lambda x: len(x[1]))
                    evidence_lines = [
                        LineSpan(
                            start_line_number=method.lineno,
                            end_line_number=method.tolineno + 1
                        )
                        for method in methods
                        if method.name in primary_delegate[1]
                    ]
                    payload = FileClassLineSpansPayload(
                        type="Code",
                        name="Middle Man",
                        description=f"Class '{node.name}' delegates {delegating_methods}/{total_methods} methods "
                                  f"({delegation_ratio:.1%}), mainly to {primary_delegate[0]} in {file_path}",
                        file_path=file_path,
                        class_name=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        evidence_lines=evidence_lines,
                        severity='medium'
                    )
                    self._smell_recorder.record_smell(
                        "file_class_line_spans",
                        payload,
                        file_path=file_path,
                        module_class=node.name,
                        start_line_number=node.lineno,
                        end_line_number=node.tolineno + 1,
                        severity='medium'
                    )

    def print_report(self):
        """
        Print a report of all detected code smells.

        If no code smells are detected, it prints a message indicating so.
        """
        if not self.code_smells:
            print("No code smells detected.")
        else:
            print("Detected Code Smells:")
            for smell in self.code_smells:
                print(f"- {smell.name}: {smell.description}")

