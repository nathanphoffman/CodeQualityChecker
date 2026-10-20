"""Finds the calls and other constructs rule 5 looks at, in Python, Rust and TypeScript files."""
from ....source_code import PYTHON, SUFFIX_LANGUAGE, non_test_files, read_source
from ..python.python_uses import python_uses
from ..tree_sitter.tree_uses import tree_uses

def find_uses(source, language):
    return python_uses(source) if language == PYTHON else tree_uses(source, language)

def uses_in_project(project):
    """(file label, language, uses) for every Python, Rust and TypeScript file."""

    return project.remember("uses_in_project", lambda: uses_in_files(project))

def uses_in_files(project):
    found = []

    for path in non_test_files(project, SUFFIX_LANGUAGE):
        language = SUFFIX_LANGUAGE[path.suffix]
        found.append((project.label_for(path), language, find_uses(read_source(path), language)))

    return found
