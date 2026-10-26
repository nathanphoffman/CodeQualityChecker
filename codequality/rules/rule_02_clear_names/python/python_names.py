import ast

from ....language_parsers.python.parse_python import parse_python
from ...rule_01_power_of_six.python.python_functions import RECEIVER_NAMES
from ..shared.name_styles import FUNCTION, TYPE, VALUE, VARIABLE

def assigned_names_in_body(body):
    """The names assigned directly in a module or class body, which may be constants, so they are not judged as locals."""
    targets = []

    for statement in body:
        if isinstance(statement, ast.Assign):
            targets += statement.targets
        elif isinstance(statement, ast.AnnAssign):
            targets.append(statement.target)

    # every Name node inside every assignment target, found by id because ast nodes compare by identity
    return {id(part) for target in targets for part in ast.walk(target)}

def kinded_names_declared_by(node, shared_assignments):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return [(node.name, FUNCTION)]

    if isinstance(node, ast.ClassDef):
        return [(node.name, TYPE)]

    if isinstance(node, ast.ExceptHandler) and node.name:
        return [(node.name, VARIABLE)]

    if isinstance(node, ast.arg) and node.arg not in RECEIVER_NAMES:
        return [(node.arg, VARIABLE)]

    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        return [(node.id, VALUE if id(node) in shared_assignments else VARIABLE)]

    return []

def python_kinded_names(source):
    """(name, kind) for every name the file declares."""
    tree = parse_python(source)
    bodies = [tree] + [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    shared_assignments = set().union(*(assigned_names_in_body(body.body) for body in bodies))
    names = []

    for node in ast.walk(tree):
        names += kinded_names_declared_by(node, shared_assignments)

    return [(name, kind) for name, kind in names if name != "_"]

def python_names(source):
    return [name for name, _ in python_kinded_names(source)]
