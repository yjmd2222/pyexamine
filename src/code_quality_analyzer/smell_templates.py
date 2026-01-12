from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass
class LineSpan:
    start_line_number: int
    end_line_number: int


@dataclass
class NamedLineSpan:
    name: str
    start_line_number: int
    end_line_number: int


@dataclass
class FileInstanceLines:
    name: str
    instance_lines: List[LineSpan]


@dataclass
class FileNameOnly:
    name: str


@dataclass
class FlatFunctionLevelPayload:
    type: str
    name: str
    description: str
    file_path: str
    function: str
    start_line_number: int
    end_line_number: int
    severity: str


@dataclass
class FlatMethodFunctionPayload:
    type: str
    name: str
    description: str
    file_path: str
    class_name: str
    method_function: str
    start_line_number: int
    end_line_number: int
    severity: str


@dataclass
class FlatStatementPayload:
    type: str
    name: str
    description: str
    file_path: str
    start_line_number: int
    end_line_number: int
    severity: str


@dataclass
class FlatChainPayload:
    type: str
    name: str
    description: str
    file_path: str
    start_line_number: int
    end_line_number: int
    severity: str


@dataclass
class FileLineSpansPayload:
    type: str
    name: str
    description: str
    file_path: str
    lines: List[LineSpan]
    severity: str


@dataclass
class FileLevelWithoutLineSpansPayload:
    type: str
    name: str
    description: str
    file_path: str
    severity: str


@dataclass
class FileClassLineSpansPayload:
    type: str
    name: str
    description: str
    file_path: str
    class_name: str
    start_line_number: int
    end_line_number: int
    instance_lines: List[LineSpan]
    severity: str


@dataclass
class FileLevelMethodFunctionLineSpansPayload:
    type: str
    name: str
    description: str
    file_path: str
    methods_functions: List[NamedLineSpan]
    severity: str


@dataclass
class FileFunctionLineSpansPayload:
    type: str
    name: str
    description: str
    file_path: str
    function: str
    start_line_number: int
    end_line_number: int
    instance_lines: List[LineSpan]
    severity: str


@dataclass
class FileMultipleClassesPayload:
    type: str
    name: str
    description: str
    file_path: str
    classes: List[NamedLineSpan]
    severity: str


@dataclass
class FlatClassLevelPayload:
    type: str
    name: str
    description: str
    file_path: str
    class_name: str
    start_line_number: int
    end_line_number: int
    severity: str


@dataclass
class StructuralClassMethodPayload:
    type: str
    name: str
    description: str
    file_path: str
    class_name: str
    method_function: str
    start_line_number: int
    end_line_number: int
    severity: str


@dataclass
class StructuralClassLevelPayload:
    type: str
    name: str
    description: str
    file_path: str
    class_name: str
    start_line_number: int
    end_line_number: int
    severity: str


@dataclass
class StructuralClassLevelLineSpansPayload:
    type: str
    name: str
    description: str
    file_path: str
    class_name: str
    start_line_number: int
    end_line_number: int
    instance_lines: List[LineSpan]
    severity: str


@dataclass
class StructuralFileLevelPayload:
    type: str
    name: str
    description: str
    file_path: str
    severity: str


@dataclass
class StructuralClassOnlyPayload:
    type: str
    name: str
    description: str
    file_path: str
    class_name: str
    severity: str


@dataclass
class StructuralFileLevelConnectedPayload:
    type: str
    name: str
    description: str
    file_path: str
    files: List[FileInstanceLines]
    severity: str


@dataclass
class StructuralFileLevelLineSpansPayload:
    type: str
    name: str
    description: str
    file_path: str
    instance_lines: List[LineSpan]
    severity: str


@dataclass
class StructuralProjectLevelPayload:
    type: str
    name: str
    description: str
    severity: str


@dataclass
class ArchitecturalFileLevelConnectedPayload:
    type: str
    name: str
    description: str
    file_path: str
    files: List[FileInstanceLines]
    severity: str


@dataclass
class ArchitecturalFunctionLevelConnectedPayload:
    type: str
    name: str
    description: str
    file_path: str
    function: str
    files: List[FileInstanceLines]
    severity: str


@dataclass
class ArchitecturalFilesPayload:
    type: str
    name: str
    description: str
    files: List[FileInstanceLines]
    severity: str


@dataclass
class ArchitecturalFileLevelLineSpansPayload:
    type: str
    name: str
    description: str
    file_path: str
    start_line_number: int
    end_line_number: int
    instance_lines: List[LineSpan]
    severity: str


@dataclass
class ArchitecturalFileLevelInstanceLinesPayload:
    type: str
    name: str
    description: str
    file_path: str
    instance_lines: List[LineSpan]
    severity: str


@dataclass
class ArchitecturalFileLevelPayload:
    type: str
    name: str
    description: str
    file_path: str
    severity: str


@dataclass
class ArchitecturalMultiFilePayload:
    type: str
    name: str
    description: str
    files: List[FileNameOnly]
    severity: str


def render_flat_function_level(payload: FlatFunctionLevelPayload) -> str:
    return payload.description


def render_flat_method_function(payload: FlatMethodFunctionPayload) -> str:
    return payload.description


def render_flat_statement(payload: FlatStatementPayload) -> str:
    return payload.description


def render_flat_chain(payload: FlatChainPayload) -> str:
    return payload.description


def render_file_line_spans(payload: FileLineSpansPayload) -> str:
    return payload.description


def render_file_level_without_line_spans(payload: FileLevelWithoutLineSpansPayload) -> str:
    return payload.description


def render_file_class_line_spans(payload: FileClassLineSpansPayload) -> str:
    return payload.description


def render_file_level_method_function_line_spans(payload: FileLevelMethodFunctionLineSpansPayload) -> str:
    return payload.description


def render_file_function_line_spans(payload: FileFunctionLineSpansPayload) -> str:
    return payload.description


def render_file_multiple_classes(payload: FileMultipleClassesPayload) -> str:
    return payload.description


def render_flat_class_level(payload: FlatClassLevelPayload) -> str:
    return payload.description


def render_structural_class_method(payload: StructuralClassMethodPayload) -> str:
    return payload.description


def render_structural_class_level(payload: StructuralClassLevelPayload) -> str:
    return payload.description


def render_structural_class_level_line_spans(payload: StructuralClassLevelLineSpansPayload) -> str:
    return payload.description


def render_structural_file_level(payload: StructuralFileLevelPayload) -> str:
    return payload.description


def render_structural_class_only(payload: StructuralClassOnlyPayload) -> str:
    return payload.description


def render_structural_file_level_connected(payload: StructuralFileLevelConnectedPayload) -> str:
    return payload.description


def render_structural_file_level_line_spans(payload: StructuralFileLevelLineSpansPayload) -> str:
    return payload.description


def render_structural_project_level(payload: StructuralProjectLevelPayload) -> str:
    return payload.description


def render_architectural_file_level_connected(payload: ArchitecturalFileLevelConnectedPayload) -> str:
    return payload.description


def render_architectural_function_level_connected(payload: ArchitecturalFunctionLevelConnectedPayload) -> str:
    return payload.description


def render_architectural_files(payload: ArchitecturalFilesPayload) -> str:
    return payload.description


def render_architectural_file_level_line_spans(payload: ArchitecturalFileLevelLineSpansPayload) -> str:
    return payload.description


def render_architectural_file_level_instance_lines(payload: ArchitecturalFileLevelInstanceLinesPayload) -> str:
    return payload.description


def render_architectural_file_level(payload: ArchitecturalFileLevelPayload) -> str:
    return payload.description


def render_architectural_multi_file(payload: ArchitecturalMultiFilePayload) -> str:
    return payload.description


class TemplateRenderer:
    def __init__(self, renderers: Dict[str, Callable[[object], str]]):
        self._renderers = renderers

    def render(self, template_id: str, payload: object) -> str:
        return self._renderers[template_id](payload)
