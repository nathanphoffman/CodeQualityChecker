import ast

from ....language_parsers.python.parse_python import parse_python
from ...rule_01_power_of_six.python.python_functions import RECEIVER_NAMES

def names_declared_by(node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]

    if isinstance(node, ast.ExceptHandler) and node.name:
        return [node.name]

    if isinstance(node, ast.arg) and node.arg not in RECEIVER_NAMES:
        return [node.arg]

    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        return [node.id]

    return []

def python_names(source):
    names = []

    for node in ast.walk(parse_python(source)):
        names += names_declared_by(node)

    return [name for name in names if name != "_"]
