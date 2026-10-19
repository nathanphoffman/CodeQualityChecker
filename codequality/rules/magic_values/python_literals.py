import ast

from ...python_support.parse_python import parse_python
from .Literal_Use import KIND_NUMBER, KIND_STRING, Literal_Use


def is_constant_definition(node):
    """NAME = value, NAME: type = value, or A, B = 1, 2, where every name is in SCREAMING_SNAKE."""
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        return False
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    names = []
    for target in targets:
        names += target.elts if isinstance(target, ast.Tuple) else [target]
    return all(isinstance(name, ast.Name) and name.id.isupper() for name in names)


def is_number(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)


def literal_of(node, in_constant):
    """A Literal_Use for a number or string, or None. `-5` is read as one number."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and is_number(node.operand):
        return Literal_Use(KIND_NUMBER, -node.operand.value, node.lineno, in_constant)
    if is_number(node):
        return Literal_Use(KIND_NUMBER, node.value, node.lineno, in_constant)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return Literal_Use(KIND_STRING, node.value, node.lineno, in_constant)
    return None


def children_are_named(node, child, in_constant):
    """Whether a child is already named: part of a constant definition, a docstring, or text inside an f-string."""
    inside_text = isinstance(node, (ast.JoinedStr, ast.Expr)) and isinstance(child, ast.Constant)
    return in_constant or is_constant_definition(node) or inside_text


def python_literals(source):
    found, pending = [], [(parse_python(source), False)]
    while pending:
        node, in_constant = pending.pop()
        literal = literal_of(node, in_constant)
        if literal:
            found.append(literal)
        if literal and literal.kind == KIND_NUMBER and isinstance(node, ast.UnaryOp):
            continue
        pending += [(child, children_are_named(node, child, in_constant)) for child in ast.iter_child_nodes(node)]
    return found
