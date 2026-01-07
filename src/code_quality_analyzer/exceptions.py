class CodeAnalysisError(Exception):
    """Base exception class for code analysis errors"""
    def __init__(self, message, file_path=None, start_line_number=None, end_line_number=None, function_name=None):
        self.file_path = file_path
        self.start_line_number = start_line_number
        self.end_line_number = end_line_number
        self.function_name = function_name
        super().__init__(f"{message}\nFile: {file_path}\nStart Line: {start_line_number}\nEnd Line: {end_line_number}\nFunction: {function_name}") 