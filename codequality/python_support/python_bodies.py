import ast

from .parse_python import parse_python
from .python_functions import RECEIVER_NAMES

BRANCH_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp, ast.match_case, ast.comprehension)
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


def local_names(function):
    """Parameters plus every name assigned inside the function."""
    parameters = [argument.arg for argument in ast.walk(function.args) if isinstance(argument, ast.arg)]
    assigned = [node.id for node in ast.walk(function) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)]
    return set(parameters + assigned) - RECEIVER_NAMES


def names_used(statement):
    return {node.id for node in ast.walk(statement) if isinstance(node, ast.Name)}


def branch_count(function):
    count = 0
    for node in ast.walk(function):
        count += isinstance(node, BRANCH_NODES)
        count += len(node.values) - 1 if isinstance(node, ast.BoolOp) else 0
    return count


def python_bodies(source):
    """(name, line_number, statement_variables, branch_count, last_line, has_docstring) for every def."""
    bodies = []

    for node in ast.walk(parse_python(source)):
        if isinstance(node, FUNCTIONS):
            locals_ = local_names(node)
            used = [names_used(statement) & locals_ for statement in node.body]
            bodies.append((node.name, node.lineno, used, branch_count(node), node.end_lineno, ast.get_docstring(node) is not None))
    return bodies
