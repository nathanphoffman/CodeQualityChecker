from ...source_code import items_in_project
from .python_literals import python_literals
from .tree_literals import tree_literals


def literals_in_project(project):
    """[(file label, Literal_Use)] for every number and string in non-test Python, Rust and TypeScript files."""
    return items_in_project(project, python_literals, tree_literals)
