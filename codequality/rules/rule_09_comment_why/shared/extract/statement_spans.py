import ast

from .....language_parsers.python.parse_python import parse_python
from ...deor.deor_comments import deor_ends
from .....source_code import DEOR, PYTHON
from .....language_parsers.tree_sitter.parse_tree import parse_tree
from .....language_parsers.tree_sitter.tree_walk import walk

def python_ends(source):
    """{line a statement starts on: last line of the longest statement starting there}. Decorators start a function."""
    ends = {}

    for node in ast.walk(parse_python(source)):
        if isinstance(node, ast.stmt):
            start = min([decorator.lineno for decorator in getattr(node, "decorator_list", [])] + [node.lineno])
            ends[start] = max(ends.get(start, 0), node.end_lineno)

    return ends

def tree_ends(source, language):
    """The same for Rust and TypeScript, using every named node except comments and the file itself."""
    ends = {}

    for node in walk(parse_tree(source, language)):
        if node.is_named and node.parent is not None and "comment" not in node.type:
            start = node.start_point.row + 1
            ends[start] = max(ends.get(start, 0), node.end_point.row + 1)

    return ends

def statement_ends(source, language):
    if language == DEOR:
        return deor_ends(source)

    return python_ends(source) if language == PYTHON else tree_ends(source, language)
