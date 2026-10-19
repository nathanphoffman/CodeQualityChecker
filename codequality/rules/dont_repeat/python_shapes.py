import ast

from ...python_support.parse_python import parse_python
from .Function_Shape import Function_Shape, Statement_Shape

FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
BLOCK_FIELDS = ("body", "orelse", "finalbody")


def shape_of(node):
    """(text, size) for a node with variable names and literal values removed. Method names are kept."""
    label = type(node).__name__ + (f".{node.attr}" if isinstance(node, ast.Attribute) else "")
    children = [shape_of(child) for child in ast.iter_child_nodes(node) if not isinstance(child, ast.expr_context)]
    return f"{label}({','.join(text for text, _ in children)})", 1 + sum(size for _, size in children)


def is_docstring(statement):
    return isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str)


def statement_shapes(statements):
    shapes = []
    for statement in statements:
        if not is_docstring(statement):
            text, size = shape_of(statement)
            shapes.append(Statement_Shape(text, size, statement.lineno, statement.end_lineno))

    return shapes


def sequences_of(function):
    """Every list of statements in the function, body first. Nested functions are left to their own entry."""
    sequences, pending = [], [function]

    while pending:
        node = pending.pop()
        for field in BLOCK_FIELDS:
            statements = getattr(node, field, None)
            if isinstance(statements, list) and statements and isinstance(statements[0], ast.stmt):
                sequences.append(statement_shapes(statements))

        pending += [child for child in ast.iter_child_nodes(node) if not isinstance(child, FUNCTIONS)]

    return sequences


def python_shapes(source):
    return [Function_Shape(node.name, node.lineno, sequences_of(node))
            for node in ast.walk(parse_python(source)) if isinstance(node, FUNCTIONS)]
