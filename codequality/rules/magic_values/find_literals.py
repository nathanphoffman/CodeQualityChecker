from ...source_code import SUFFIX_LANGUAGE, non_test_files
from .python_literals import python_literals
from .tree_literals import tree_literals


def literals_in_project(project):
    """[(file label, Literal_Use)] for every number and string in non-test Python, Rust and TypeScript files."""
    found = []
    for path in non_test_files(project, SUFFIX_LANGUAGE):
        language = SUFFIX_LANGUAGE[path.suffix]
        source = path.read_text(errors="ignore")
        literals = python_literals(source) if language == "python" else tree_literals(source, language)
        found += [(project.label_for(path), literal) for literal in literals]
    return found
