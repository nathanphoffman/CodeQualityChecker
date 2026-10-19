from ...source_code import PYTHON, SUFFIX_LANGUAGE, non_test_files, read_source
from .python_literals import python_literals
from .tree_literals import tree_literals


def literals_in_project(project):
    """[(file label, Literal_Use)] for every number and string in non-test Python, Rust and TypeScript files."""
    found = []
    for path in non_test_files(project, SUFFIX_LANGUAGE):
        language = SUFFIX_LANGUAGE[path.suffix]
        source = read_source(path)
        literals = python_literals(source) if language == PYTHON else tree_literals(source, language)
        found += [(project.label_for(path), literal) for literal in literals]
    return found
