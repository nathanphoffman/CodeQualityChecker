"""Finds the calls and other constructs rule 5 looks at, in Python, Rust and TypeScript files."""
from ....source_code import DEOR, PYTHON, SUFFIX_LANGUAGE, non_test_files, read_source
from ..python.python_uses import python_uses
from ..tree_sitter.tree_uses import deor_uses, tree_uses

def find_uses(source, language):
    if language == PYTHON:
        return python_uses(source)

    return deor_uses(source) if language == DEOR else tree_uses(source, language)

def uses_in_project(project):
    """(file label, language, uses) for every Python, Rust, TypeScript and Deor file."""
    paths = non_test_files(project, SUFFIX_LANGUAGE)

    return project.remember("uses_in_project", lambda: [
        (project.label_for(path), SUFFIX_LANGUAGE[path.suffix], find_uses(read_source(path), SUFFIX_LANGUAGE[path.suffix]))
        for path in paths])
