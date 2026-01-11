import os
import ast
import networkx as nx
from collections import defaultdict
import yaml
from dataclasses import dataclass
import sys
import importlib.util
import logging
from .exceptions import CodeAnalysisError
from .smell_templates import (
    ArchitecturalFileLevelConnectedPayload,
    ArchitecturalFileLevelLineSpansPayload,
    ArchitecturalFileLevelPayload,
    ArchitecturalFilesPayload,
    ArchitecturalFunctionLevelConnectedPayload,
    ArchitecturalMultiFilePayload,
    FileInstanceLines,
    LineSpan,
    TemplateRenderer,
    render_architectural_file_level,
    render_architectural_file_level_connected,
    render_architectural_file_level_line_spans,
    render_architectural_files,
    render_architectural_function_level_connected,
    render_architectural_multi_file,
)

# Set up logger
logger = logging.getLogger(__name__)

@dataclass
class ArchitecturalSmell:
    name: str
    description: str
    file_path: str
    module_class: str
    start_line_number: int
    end_line_number: int
    severity: str

class ArchitecturalSmellRecorder:
    def __init__(self, architectural_smells):
        self._architectural_smells = architectural_smells

    def add_smell(self, name, description, file_path, module_class, start_line_number=None,
                  end_line_number=None, severity='medium'):
        """
        Add a detected architectural smell to the list.
        
        Args:
            name (str): The name of the smell
            description (str): Description of the smell
            file_path (str): Path to the file containing the smell
            module_class (str): The module or class containing the smell
            start_line_number (int, optional): The start line number where the smell was detected
            end_line_number (int, optional): The ending line number (+1 for slicing)
            severity (str, optional): The severity level of the smell (default: 'medium')
        """
        self._architectural_smells.append(ArchitecturalSmell(
            name=name,
            description=description,
            file_path=file_path,
            module_class=module_class,
            start_line_number=start_line_number,
            end_line_number=end_line_number,
            severity=severity
        ))

class ArchitecturalSmellDetector:
    """
    A class to detect architectural smells in Python projects.

    This class analyzes Python source code files within a directory to identify
    various architectural smells based on predefined thresholds.

    Attributes:
        architectural_smells (list): A list to store detected architectural smells.
        module_dependencies (nx.DiGraph): A directed graph to represent module dependencies.
        module_functions (defaultdict): A dictionary to store functions for each module.
        api_usage (defaultdict): A dictionary to store API usage for each module.
        thresholds (dict): A dictionary of threshold values for various smell detections.
        file_paths (dict): A dictionary to store file paths for each module.
        external_dependencies (dict): A dictionary to store external dependencies for each module.
        function_calls (defaultdict): A dictionary to track inter-module function calls.
    """

    def __init__(self, thresholds):
        """
        Initialize the ArchitecturalSmellDetector with given thresholds.

        Args:
            thresholds (dict): A dictionary of threshold values for various smell detections.
        """
        self.architectural_smells = []
        self._smell_recorder = ArchitecturalSmellRecorder(self.architectural_smells)
        self.add_smell = self._smell_recorder.add_smell
        self._template_renderer = TemplateRenderer({
            "architectural_file_level_connected": render_architectural_file_level_connected,
            "architectural_function_level_connected": render_architectural_function_level_connected,
            "architectural_files": render_architectural_files,
            "architectural_file_level_line_spans": render_architectural_file_level_line_spans,
            "architectural_file_level": render_architectural_file_level,
            "architectural_multi_file": render_architectural_multi_file,
        })
        self.module_dependencies = nx.DiGraph()
        self.module_functions = defaultdict(set)
        self.api_usage = defaultdict(list)
        self.thresholds = thresholds
        self.file_paths = {}  # New attribute to store file paths
        self.external_dependencies = defaultdict(set)
        self.function_calls = defaultdict(set)  # Track inter-module function calls
        self.import_lines = defaultdict(list)
        self.function_lines = defaultdict(lambda: defaultdict(list))
        self.api_call_lines = defaultdict(list)
        self.class_methods = defaultdict(set)
        self.class_method_lines = defaultdict(lambda: defaultdict(list))
        self.class_lines = {}
        self.class_modules = {}

    def load_thresholds(self, config_path):
        """
        Load threshold values from a YAML configuration file.

        Args:
            config_path (str): Path to the YAML configuration file.

        Returns:
            dict: A dictionary of threshold values for architectural smells.
        """
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return {k: v['value'] for k, v in config['architectural_smells'].items()}

    def detect_smells(self, directory_path):
        """
        Detect architectural smells in the given directory.
        """
        detection_methods = [
            (self.detect_hub_like_dependency, "detect_hub_like_dependency"),
            (self.detect_scattered_functionality, "detect_scattered_functionality"),
            (self.detect_redundant_abstractions, "detect_redundant_abstractions"),
            (self.detect_god_objects, "detect_god_objects"),
            (self.detect_improper_api_usage, "detect_improper_api_usage"),
            (self.detect_orphan_modules, "detect_orphan_modules"),
            (self.detect_cyclic_dependencies, "detect_cyclic_dependencies"),
            (self.detect_unstable_dependencies, "detect_unstable_dependencies")
        ]

        try:
            # First analyze the directory structure
            logger.info(f"Analyzing directory structure: {directory_path}")
            self.analyze_directory(directory_path)
            
            # Then run each detection method
            for detect_method, method_name in detection_methods:
                try:
                    logger.debug(f"Running {method_name}")
                    detect_method()
                except Exception as e:
                    logger.error(f"Error in {method_name}: {str(e)}", exc_info=True)
                    raise CodeAnalysisError(
                        message=str(e),
                        file_path=directory_path,
                        function_name=method_name
                    )
                    
        except Exception as e:
            logger.error(f"Error analyzing directory {directory_path}: {str(e)}", exc_info=True)
            raise CodeAnalysisError(
                message=str(e),
                file_path=directory_path
            )

    def analyze_directory(self, directory_path):
        """
        Analyze all Python files in the given directory and its subdirectories.

        Args:
            directory_path (str): The path to the directory to be analyzed.
        """
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.analyze_file(file_path)
        
        # After analyzing all files, resolve external dependencies
        self.resolve_external_dependencies()

    def analyze_file(self, file_path):
        """
        Analyze a single Python file for architectural information with improved
        intra-project dependency detection.
        """
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
                print(f"Encoding error in file {file_path}: unable to decode with utf-8/utf-8-sig/latin-1")
                return
            tree = ast.parse(content)

            # Get relative module path
            module_name = os.path.relpath(file_path, os.path.dirname(os.path.dirname(file_path)))
            module_name = module_name.replace(os.path.sep, '.')[:-3]  # Remove .py extension
            self.module_dependencies.add_node(module_name)
            self.file_paths[module_name] = file_path
            
            # Track local imports and their line numbers
            local_imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_name = alias.name
                        local_imports.append((import_name, node.lineno))
                        self.module_dependencies.add_edge(module_name, import_name)
                        self.import_lines[module_name].append({
                            "name": import_name,
                            "start_line_number": node.lineno,
                            "end_line_number": node.lineno + 1
                        })
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Handle relative imports
                        if node.level > 0:  # This is a relative import
                            current_package = module_name.split('.')
                            # Go up by node.level
                            parent_package = '.'.join(current_package[:-node.level])
                            if parent_package:
                                import_name = f"{parent_package}.{node.module}"
                            else:
                                import_name = node.module
                        else:
                            import_name = node.module
                        
                        local_imports.append((import_name, node.lineno))
                        self.module_dependencies.add_edge(module_name, import_name)
                        self.import_lines[module_name].append({
                            "name": import_name,
                            "start_line_number": node.lineno,
                            "end_line_number": node.lineno + 1
                        })
                        
                        # Track imported names for more detailed dependency analysis
                        for alias in node.names:
                            if alias.name != '*':
                                full_import = f"{import_name}.{alias.name}"
                                self.module_functions[import_name].add(alias.name)
                
                elif isinstance(node, ast.ClassDef):
                    class_key = f"{module_name}.{node.name}"
                    self.class_modules[class_key] = module_name
                    class_end = getattr(node, "end_lineno", node.lineno)
                    self.class_lines[class_key] = (node.lineno, class_end + 1)
                    for class_item in node.body:
                        if isinstance(class_item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            self.class_methods[class_key].add(class_item.name)
                            method_end = getattr(class_item, "end_lineno", class_item.lineno)
                            self.class_method_lines[class_key][class_item.name].append(
                                (class_item.lineno, method_end + 1)
                            )
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.module_functions[module_name].add(node.name)
                    end_lineno = getattr(node, "end_lineno", node.lineno)
                    self.function_lines[module_name][node.name].append(
                        (node.lineno, end_lineno + 1)
                    )
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        self.api_usage[module_name].append(node.func.attr)
                        call_end = getattr(node, "end_lineno", node.lineno)
                        self.api_call_lines[module_name].append({
                            "name": node.func.attr,
                            "start_line_number": node.lineno,
                            "end_line_number": call_end + 1
                        })
                        
                        # Track function calls between modules
                        if isinstance(node.func.value, ast.Name):
                            # Check if this is a call to an imported module
                            module_called = node.func.value.id
                            if any(module_called == imp[0].split('.')[-1] for imp in local_imports):
                                self.function_calls[module_name].add((module_called, node.func.attr))

        except SyntaxError as e:
            print(f"Parse error in file {file_path}: {str(e)}")
        except Exception as e:
            print(f"Error analyzing file {file_path}: {str(e)}")

    def resolve_external_dependencies(self):
        """
        Resolve external dependencies while preserving intra-project dependencies.
        """
        # Get all project modules
        project_root = os.path.dirname(os.path.dirname(next(iter(self.file_paths.values()))))
        all_modules = set(self.module_dependencies.nodes())
        standard_lib_modules = set(sys.stdlib_module_names)
        
        for module in list(self.module_dependencies.nodes()):
            for dependency in list(self.module_dependencies.successors(module)):
                # Check if it's a project module by looking for the file
                possible_paths = [
                    os.path.join(project_root, *dependency.split('.')) + '.py',
                    os.path.join(project_root, dependency.split('.')[0], '__init__.py')
                ]
                
                is_project_module = (
                    dependency in all_modules or
                    any(os.path.exists(path) for path in possible_paths)
                )
                
                # Keep project dependencies, handle external ones
                if not is_project_module:
                    is_stdlib = any(dependency.startswith(std_lib) for std_lib in standard_lib_modules)
                    
                    try:
                        spec = importlib.util.find_spec(dependency.split('.')[0])
                        is_third_party = spec is not None and not is_stdlib
                    except (ModuleNotFoundError, ValueError):
                        is_third_party = False
                    
                    self.module_dependencies.remove_edge(module, dependency)
                    
                    if is_stdlib:
                        self.external_dependencies[module].add(('stdlib', dependency))
                    elif is_third_party:
                        self.external_dependencies[module].add(('third_party', dependency))
                    
                    # Remove isolated external nodes
                    if not self.module_dependencies.in_edges(dependency) and \
                       not self.module_dependencies.out_edges(dependency):
                        self.module_dependencies.remove_node(dependency)


    def detect_hub_like_dependency(self):
        """
        Detect hub-like dependencies in the project with improved accuracy.\n

        Location data is derived from import statements and represented as\n
        {name: <module>, start_line_number: <start>, end_line_number: <end>}.
        """
        total_modules = len(self.module_dependencies.nodes())
        # Skip analysis for very small projects
        min_project_modules = self.thresholds.get('HUB_MIN_PROJECT_MODULES', 3)
        if total_modules < min_project_modules:
            return

        threshold = self.thresholds.get('HUB_LIKE_DEPENDENCY_THRESHOLD', 0.5)
        min_connections = self.thresholds.get('MIN_HUB_CONNECTIONS', 5)
        
        for node in self.module_dependencies.nodes():
            def _format_instances(instances):
                grouped = defaultdict(list)
                for entry in instances:
                    grouped[entry["name"]].append(
                        (entry["start_line_number"], entry["end_line_number"])
                    )
                parts = []
                for name in sorted(grouped):
                    ranges = ", ".join(f"{start}-{end}" for start, end in grouped[name])
                    parts.append(f"{name}({ranges})")
                return ", ".join(parts)

            # Count both internal and external dependencies
            in_degree = self.module_dependencies.in_degree(node)
            out_degree = self.module_dependencies.out_degree(node)
            external_deps = len(self.external_dependencies[node])
            total_connections = in_degree + out_degree + external_deps
            
            # Calculate fan-in and fan-out ratios
            fan_in_ratio = in_degree / total_modules if total_modules > 0 else 0
            fan_out_ratio = (out_degree + external_deps) / total_modules if total_modules > 0 else 0
            
            # Check for hub-like characteristics
            is_hub = (total_connections >= min_connections and 
                     (total_connections / total_modules) > threshold)
            
            # Additional checks to reduce false positives
            if is_hub:
                # Exclude common infrastructure modules
                if any(pattern in node.lower() for pattern in ['util', 'common', 'base', 'core']):
                    continue

                # Check if the module has balanced dependencies
                bal_min = self.thresholds.get('HUB_BALANCE_RATIO_MIN', 0.2)
                bal_max = self.thresholds.get('HUB_BALANCE_RATIO_MAX', 5)
                # avoid division by zero by using conditional
                if fan_out_ratio == 0:
                    ratio = float('inf') if fan_in_ratio > 0 else 0
                else:
                    ratio = fan_in_ratio / fan_out_ratio
                is_balanced = (bal_min <= ratio <= bal_max)
                
                if not is_balanced:
                    outgoing_instances = [
                        entry for entry in self.import_lines.get(node, [])
                        if (
                            entry["name"] in self.module_dependencies.successors(node) or
                            any(entry["name"] == dep for _, dep in self.external_dependencies[node])
                        )
                    ]
                    # outgoing_instances: {name, start_line_number, end_line_number} per import in this module
                    incoming_instances = []
                    for predecessor in self.module_dependencies.predecessors(node):
                        for entry in self.import_lines.get(predecessor, []):
                            if entry["name"] == node:
                                incoming_instances.append({
                                    "name": predecessor,
                                    "start_line_number": entry["start_line_number"],
                                    "end_line_number": entry["end_line_number"]
                                })
                    # incoming_instances: {name, start_line_number, end_line_number} per import of this module

                    outgoing_detail = _format_instances(outgoing_instances) or "None"
                    incoming_detail = _format_instances(incoming_instances) or "None"
                    instance_start = None
                    instance_end = None
                    if outgoing_instances:
                        instance_start = min(d["start_line_number"] for d in outgoing_instances)
                        instance_end = max(d["end_line_number"] for d in outgoing_instances)
                    grouped = defaultdict(list)
                    for entry in outgoing_instances + incoming_instances:
                        grouped[entry["name"]].append(
                            LineSpan(
                                start_line_number=entry["start_line_number"],
                                end_line_number=entry["end_line_number"]
                            )
                        )
                    payload = ArchitecturalFileLevelConnectedPayload(
                        type="Architectural",
                        name="Hub-like Dependency",
                        description=(
                            f"Module '{node}' is a potential hub with {total_connections} connections "
                            f"(in: {in_degree}, out: {out_degree}, external: {external_deps})\n"
                            f"Outgoing dependency instances: {outgoing_detail}\n"
                            f"Incoming dependency instances: {incoming_detail}"
                        ),
                        file_path=self.file_paths.get(node, "Unknown"),
                        files=[
                            FileInstanceLines(name=name, instance_lines=lines)
                            for name, lines in grouped.items()
                        ],
                        severity='high' if total_connections > min_connections * 2 else 'medium'
                    )
                    self.add_smell(
                        name="Hub-like Dependency",
                        description=self._template_renderer.render(
                            "architectural_file_level_connected",
                            payload
                        ),
                        file_path=self.file_paths.get(node, "Unknown"),
                        module_class=node,
                        severity='high' if total_connections > min_connections * 2 else 'medium'
                    )

    def detect_scattered_functionality(self):
        """
        Detect scattered functionality in the project.\n

        Location data is derived from function definitions and represented as\n
        {name: <module>, start_line_number: <start>, end_line_number: <end>}.
        """
        function_modules = defaultdict(list)
        min_function_length = self.thresholds.get('SCATTERED_MIN_FUNCTION_NAME_LENGTH', 3)
        excluded_names = set(self.thresholds.get('SCATTERED_EXCLUDED_NAMES', ['main', 'init', 'setup', 'test']))
        
        for module, functions in self.module_functions.items():
            for func in functions:
                # Skip common/utility functions and short names
                if (len(func) >= min_function_length and 
                    func.lower() not in excluded_names and 
                    not func.startswith('_')):  # Skip private functions
                    function_modules[func].append(module)
        
        min_occurrences = self.thresholds.get('MIN_SCATTERED_OCCURRENCES', 3)
        for func, modules in function_modules.items():
            if len(modules) >= min_occurrences:  # Increase minimum occurrences threshold
                grouped = defaultdict(list)
                for module in modules:
                    for start, end in self.function_lines.get(module, {}).get(func, []):
                        grouped[module].append((start, end))
                # grouped -> locations per module; becomes {name, start_line_number, end_line_number}
                parts = []
                for module in sorted(grouped):
                    ranges = ", ".join(f"{start}-{end}" for start, end in grouped[module])
                    parts.append(f"{module}({ranges})")
                detail = ", ".join(parts) if parts else ", ".join(modules)
                files = [
                    FileInstanceLines(
                        name=module,
                        instance_lines=[
                            LineSpan(start_line_number=start, end_line_number=end)
                            for start, end in grouped[module]
                        ]
                    )
                    for module in sorted(grouped)
                ]
                payload = ArchitecturalFunctionLevelConnectedPayload(
                    type="Architectural",
                    name="Scattered Functionality",
                    description=f"Function '{func}' appears in {len(modules)} modules: {detail}",
                    file_path=self.file_paths.get(modules[0], "Unknown"),
                    function=func,
                    files=files,
                    severity='medium'
                )
                self.add_smell(
                    name="Scattered Functionality",
                    description=self._template_renderer.render(
                        "architectural_function_level_connected",
                        payload
                    ),
                    file_path=self.file_paths.get(modules[0], "Unknown"),
                    module_class=modules[0]
                )

    def detect_redundant_abstractions(self):
        """
        Detect potential redundant abstractions in the project.

        Location data is derived from function definitions and represented as
        {name: <module>.<function>, start_line_number: <start>, end_line_number: <end>}.
        """
        similar_modules = defaultdict(list)
        min_functions = self.thresholds.get('REDUNDANT_MIN_FUNCTIONS', 3)  # Minimum number of functions to consider
        
        for module, functions in self.module_functions.items():
            # Only consider modules with sufficient functions
            if len(functions) >= min_functions:
                # Filter out private functions and common utility functions
                public_functions = {f for f in functions 
                                 if not f.startswith('_') 
                                 and len(f) > 3 
                                 and f.lower() not in {'main', 'init', 'setup', 'test'}}
                
                if public_functions:  # Only proceed if there are public functions
                    signature = frozenset(public_functions)
                    similar_modules[signature].append(module)
        
        similarity_threshold = self.thresholds.get('REDUNDANT_SIMILARITY_THRESHOLD', 0.8)
        for signature, modules in similar_modules.items():
            if len(modules) > 1 and len(signature) >= min_functions:
                # Calculate similarity score between modules
                for i in range(len(modules)):
                    for j in range(i + 1, len(modules)):
                        module1_funcs = self.module_functions[modules[i]]
                        module2_funcs = self.module_functions[modules[j]]
                        similarity = len(module1_funcs & module2_funcs) / len(module1_funcs | module2_funcs)
                        
                        if similarity >= similarity_threshold:
                            redundant_instances = []
                            overlap = module1_funcs & module2_funcs
                            for module_name in (modules[i], modules[j]):
                                for func in sorted(overlap):
                                    for start, end in self.function_lines.get(module_name, {}).get(func, []):
                                        redundant_instances.append({
                                            "name": f"{module_name}.{func}",
                                            "start_line_number": start,
                                            "end_line_number": end
                                        })
                            # redundant_instances: {name, start_line_number, end_line_number} per overlapping function
                            instances_detail = (
                                ", ".join(
                                    f"{entry['name']}({entry['start_line_number']}-{entry['end_line_number']})"
                                    for entry in redundant_instances
                                ) or "None"
                            )
                            grouped = defaultdict(list)
                            for entry in redundant_instances:
                                module_name = entry["name"].rsplit('.', 1)[0]
                                grouped[module_name].append(
                                    LineSpan(
                                        start_line_number=entry["start_line_number"],
                                        end_line_number=entry["end_line_number"]
                                    )
                                )
                            payload = ArchitecturalFilesPayload(
                                type="Architectural",
                                name="Potential Redundant Abstractions",
                                description=(
                                    f"Modules {modules[i]} and {modules[j]} have {similarity:.1%} similar functionalities\n"
                                    f"Overlapping function instances: {instances_detail}"
                                ),
                                files=[
                                    FileInstanceLines(name=module, instance_lines=lines)
                                    for module, lines in grouped.items()
                                ],
                                severity='medium'
                            )
                            self.add_smell(
                                name="Potential Redundant Abstractions",
                                description=self._template_renderer.render(
                                    "architectural_files",
                                    payload
                                ),
                                file_path=self.file_paths.get(modules[i], "Unknown"),
                                module_class=modules[i]
                            )

    def detect_god_objects(self):
        """
        Detect god objects in the project.

        Location data is derived from function definitions and represented as
        {name: <module>.<class>.<function>, start_line_number: <start>, end_line_number: <end>}.
        """
        min_functions = self.thresholds.get('MIN_GOD_OBJECT_FUNCTIONS', 5)
        excluded_patterns = {'test_', 'setup_', 'config_'}  # Common prefixes to exclude
        
        for class_key, methods in self.class_methods.items():
            # Filter out private methods and common test/setup functions
            public_functions = {f for f in methods 
                              if not f.startswith('_') and 
                              not any(f.startswith(pattern) for pattern in excluded_patterns)}
            
            if (len(public_functions) >= min_functions and 
                len(public_functions) > self.thresholds['GOD_OBJECT_FUNCTIONS']):
                class_start, class_end = self.class_lines.get(class_key, (None, None))
                god_instances = []
                for func in sorted(public_functions):
                    for start, end in self.class_method_lines.get(class_key, {}).get(func, []):
                        god_instances.append({
                            "name": f"{class_key}.{func}",
                            "start_line_number": start,
                            "end_line_number": end
                        })
                # god_instances: {name, start_line_number, end_line_number} per public function
                instances_detail = (
                    ", ".join(
                        f"{entry['name']}({entry['start_line_number']}-{entry['end_line_number']})"
                    for entry in god_instances
                    ) or "None"
                )
                instance_lines = [
                    LineSpan(
                        start_line_number=entry["start_line_number"],
                        end_line_number=entry["end_line_number"]
                    )
                    for entry in god_instances
                ]
                payload = ArchitecturalFileLevelLineSpansPayload(
                    type="Architectural",
                    name="God Object",
                    description=(
                        f"Class '{class_key}' has too many public methods ({len(public_functions)})\n"
                        f"Public function instances: {instances_detail}"
                    ),
                    file_path=self.file_paths.get(self.class_modules.get(class_key, ""), "Unknown"),
                    start_line_number=class_start,
                    end_line_number=class_end,
                    instance_lines=instance_lines,
                    severity='medium'
                )
                self.add_smell(
                    name="God Object",
                    description=(
                        self._template_renderer.render(
                            "architectural_file_level_line_spans",
                            payload
                        )
                    ),
                    file_path=self.file_paths.get(self.class_modules.get(class_key, ""), "Unknown"),
                    module_class=class_key,
                    start_line_number=class_start,
                    end_line_number=class_end
                )

    def detect_improper_api_usage(self):
        """
        Detect potential improper API usage in the project.

        Location data is derived from call sites and represented as
        {name: <call>, start_line_number: <start>, end_line_number: <end>}.
        """
        min_calls = self.thresholds.get('MIN_API_CALLS', 10)  # Minimum calls to consider
        repetition_threshold = self.thresholds.get('API_REPETITION_THRESHOLD', 0.4)
        repetition_min_count = self.thresholds.get('API_REPETITION_MIN_COUNT', 3)
        
        for module, api_calls in self.api_usage.items():
            if len(api_calls) >= min_calls:
                # Count frequency of each API call
                call_frequency = {}
                for call in api_calls:
                    call_frequency[call] = call_frequency.get(call, 0) + 1
                
                # Check for highly repetitive calls
                repetitive_calls = {call: count for call, count in call_frequency.items() 
                                  if count >= repetition_min_count}  # Ignore calls repeated less than configured
                
                if (repetitive_calls and 
                    sum(repetitive_calls.values()) / len(api_calls) > repetition_threshold):
                    repetitive_instances = [
                        entry for entry in self.api_call_lines.get(module, [])
                        if entry["name"] in repetitive_calls
                    ]
                    # repetitive_instances: {name, start_line_number, end_line_number} per call site
                    instances_detail = (
                        ", ".join(
                            f"{entry['name']}({entry['start_line_number']}-{entry['end_line_number']})"
                            for entry in repetitive_instances
                        ) or "None"
                    )
                    instance_lines = [
                        LineSpan(
                            start_line_number=entry["start_line_number"],
                            end_line_number=entry["end_line_number"]
                        )
                        for entry in repetitive_instances
                    ]
                    payload = ArchitecturalFileLevelLineSpansPayload(
                        type="Architectural",
                        name="Potential Improper API Usage",
                        description=(
                            f"Module '{module}' has repetitive API calls: " +
                            ", ".join(f"{call}({count}x)" for call, count in repetitive_calls.items()) +
                            f"\nRepetitive call instances: {instances_detail}"
                        ),
                        file_path=self.file_paths.get(module, "Unknown"),
                        start_line_number=None,
                        end_line_number=None,
                        instance_lines=instance_lines,
                        severity='medium'
                    )
                    self.add_smell(
                        name="Potential Improper API Usage",
                        description=self._template_renderer.render(
                            "architectural_file_level_line_spans",
                            payload
                        ),
                        file_path=self.file_paths.get(module, "Unknown"),
                        module_class=module
                    )

    def detect_orphan_modules(self):
        """
        Detect orphan modules in the project.
        """
        excluded_modules = set(self.thresholds.get('ORPHAN_EXCLUDED_MODULES', ['__init__', 'setup', 'tests', 'utils']))
        min_project_size = self.thresholds.get('MIN_PROJECT_SIZE', 3)
        
        if len(self.module_dependencies.nodes()) < min_project_size:
            return
            
        for node in self.module_dependencies.nodes():
            module_name = node.split('.')[-1]
            # Fix: Check if any excluded module name is in the full node path
            if (self.module_dependencies.in_degree(node) + self.module_dependencies.out_degree(node) == 0 and
                module_name not in excluded_modules and
                not any(excluded in node.lower() for excluded in excluded_modules)):
                self.add_smell(
                    name="Orphan Module",
                    description=self._template_renderer.render(
                        "architectural_file_level",
                        ArchitecturalFileLevelPayload(
                            type="Architectural",
                            name="Orphan Module",
                            description=f"'{node}' is isolated from other modules",
                            file_path=self.file_paths.get(node, "Unknown"),
                            severity='medium'
                        )
                    ),
                    file_path=self.file_paths.get(node, "Unknown"),
                    module_class=node,
                    severity='medium'
                )

    def detect_cyclic_dependencies(self):
        """
        Detect cyclic dependencies with improved accuracy and cycle classification.
        """
        min_cycle_size = self.thresholds.get('MIN_CYCLE_SIZE', 2)
        max_cycle_size = self.thresholds.get('MAX_CYCLE_SIZE', 5)
        excluded_modules = set(self.thresholds.get('CYCLE_EXCLUDED_MODULES', ['__init__', 'utils', 'common', 'base', 'core']))
        
        # Find all simple cycles
        cycles = list(nx.simple_cycles(self.module_dependencies))
        
        # Group cycles by their shared nodes to identify related cycles
        cycle_groups = defaultdict(list)
        
        for cycle in cycles:
            if min_cycle_size <= len(cycle) <= max_cycle_size:
                # Skip cycles containing excluded modules
                if any(any(excluded in node.lower() for excluded in excluded_modules) 
                      for node in cycle):
                    continue
                
                # Calculate cycle metrics
                cycle_strength = 0
                for i in range(len(cycle)):
                    node1 = cycle[i]
                    node2 = cycle[(i + 1) % len(cycle)]
                    # Count mutual dependencies
                    cycle_strength += sum(1 for _ in nx.all_simple_paths(
                        self.module_dependencies, node1, node2))
                
                # Group related cycles
                cycle_key = frozenset(cycle)
                cycle_groups[cycle_key].append((cycle, cycle_strength))
        
        # Report cycles with additional context
        for cycle_group in cycle_groups.values():
            strongest_cycle = max(cycle_group, key=lambda x: x[1])
            cycle, strength = strongest_cycle
            
            # Calculate severity based on cycle size and strength
            cycle_high_size = self.thresholds.get('CYCLE_HIGH_MIN_SIZE', 3)
            cycle_high_strength = self.thresholds.get('CYCLE_HIGH_MIN_STRENGTH', 3)
            severity = 'high' if len(cycle) >= cycle_high_size and strength >= cycle_high_strength else 'medium'
            
            cycle_str = ' -> '.join(cycle + [cycle[0]])
            payload = ArchitecturalMultiFilePayload(
                type="Architectural",
                name="Cyclic Dependency",
                description=(
                    f"Strong cyclic dependency detected: {cycle_str}\n"
                    f"Cycle strength: {strength} mutual dependencies"
                ),
                files=[self.file_paths.get(name, name) for name in cycle],
                severity=severity
            )
            self.add_smell(
                name="Cyclic Dependency",
                description=(
                    self._template_renderer.render(
                        "architectural_multi_file",
                        payload
                    )
                ),
                file_path=self.file_paths.get(cycle[0], "Unknown"),
                module_class=cycle[0],
                severity=severity
            )

    def detect_unstable_dependencies(self):
        """
        Detect unstable dependencies in the project.

        Location data is derived from import statements and represented as
        {name: <module>, start_line_number: <start>, end_line_number: <end>}.
        """
        min_dependencies = self.thresholds.get('MIN_DEPENDENCIES', 5)  # Minimum dependencies to consider
        excluded_patterns = {'test_', 'setup_', '__init__'}  # Patterns to exclude
        
        for node in self.module_dependencies.nodes():
            if any(pattern in node for pattern in excluded_patterns):
                continue
                
            in_degree = self.module_dependencies.in_degree(node)
            out_degree = self.module_dependencies.out_degree(node)
            total_dependencies = in_degree + out_degree
            
            if total_dependencies >= min_dependencies:
                instability = out_degree / total_dependencies
                if instability > self.thresholds['UNSTABLE_DEPENDENCY_THRESHOLD']:
                    def _format_instances(instances):
                        grouped = defaultdict(list)
                        for entry in instances:
                            grouped[entry["name"]].append(
                                (entry["start_line_number"], entry["end_line_number"])
                            )
                        parts = []
                        for name in sorted(grouped):
                            ranges = ", ".join(f"{start}-{end}" for start, end in grouped[name])
                            parts.append(f"{name}({ranges})")
                        return ", ".join(parts)

                    outgoing_instances = [
                        entry for entry in self.import_lines.get(node, [])
                        if (
                            entry["name"] in self.module_dependencies.successors(node) or
                            any(entry["name"] == dep for _, dep in self.external_dependencies[node])
                        )
                    ]
                    # outgoing_instances: {name, start_line_number, end_line_number} per import in this module
                    incoming_instances = []
                    for predecessor in self.module_dependencies.predecessors(node):
                        for entry in self.import_lines.get(predecessor, []):
                            if entry["name"] == node:
                                incoming_instances.append({
                                    "name": predecessor,
                                    "start_line_number": entry["start_line_number"],
                                    "end_line_number": entry["end_line_number"]
                                })
                    # incoming_instances: {name, start_line_number, end_line_number} per import of this module

                    outgoing_detail = _format_instances(outgoing_instances) or "None"
                    incoming_detail = _format_instances(incoming_instances) or "None"
                    instance_lines = [
                        LineSpan(
                            start_line_number=entry["start_line_number"],
                            end_line_number=entry["end_line_number"]
                        )
                        for entry in outgoing_instances + incoming_instances
                    ]
                    payload = ArchitecturalFileLevelLineSpansPayload(
                        type="Architectural",
                        name="Unstable Dependency",
                        description=(
                            f"Module '{node}' has high instability ({instability:.2f}) "
                            f"with {out_degree} outgoing and {in_degree} incoming dependencies\n"
                            f"Outgoing dependency instances: {outgoing_detail}\n"
                            f"Incoming dependency instances: {incoming_detail}"
                        ),
                        file_path=self.file_paths.get(node, "Unknown"),
                        start_line_number=None,
                        end_line_number=None,
                        instance_lines=instance_lines,
                        severity='medium'
                    )
                    self.add_smell(
                        name="Unstable Dependency",
                        description=(
                            self._template_renderer.render(
                                "architectural_file_level_line_spans",
                                payload
                            )
                        ),
                        file_path=self.file_paths.get(node, "Unknown"),
                        module_class=node
                    )

    def print_report(self):
        """
        Print a report of all detected architectural smells.

        If no smells are detected, it prints a message indicating so.
        """
        if not self.architectural_smells:
            print("No architectural smells detected.")
        else:
            print("Detected Architectural Smells:")
            for smell in self.architectural_smells:
                print(f"- {smell}")

def analyze_architecture(directory_path, config_path):
    """
    Analyze the architecture of a Python project and detect architectural smells.

    Args:
        directory_path (str): The path to the directory containing the Python project to analyze.
        config_path (str): The path to the configuration file containing smell detection thresholds.
    """
    detector = ArchitecturalSmellDetector(config_path)
    detector.detect_smells(directory_path)
    detector.print_report()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Detect architectural smells in Python code.")
    parser.add_argument("directory", help="Directory path to analyze")
    parser.add_argument("--config", default="code_quality_config.yaml", help="Path to the configuration file")
    args = parser.parse_args()

    analyze_architecture(args.directory, args.config)
