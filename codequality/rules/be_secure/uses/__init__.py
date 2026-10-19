"""Finds the calls and other constructs rule 5 looks at, in Python, Rust and TypeScript files."""
from ....source_code import SUFFIX_LANGUAGE, non_test_files
from .python_uses import python_uses
from .tree_uses import tree_uses


def find_uses(source, language):
    return python_uses(source) if language == "python" else tree_uses(source, language)


def uses_in_project(project):
    """(file label, language, uses) for every Python, Rust and TypeScript file."""
    found = []
    for path in non_test_files(project, SUFFIX_LANGUAGE):
        language = SUFFIX_LANGUAGE[path.suffix]
        found.append((project.label_for(path), language, find_uses(path.read_text(errors="ignore"), language)))
    return found
