import ast

from ....language_parsers.python.parse_python import parse_python
from ...rule_01_power_of_six.python.python_functions import RECEIVER_NAMES, count_arguments

BRANCH_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp, ast.match_case, ast.comprehension)
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
NESTING_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Match)
OWN_SCOPE = FUNCTIONS + (ast.Lambda, ast.ClassDef)  # measured on their own

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

def is_elif(node, parent):
    """An `elif` is an `if` alone in the else of another `if`: one more path, not one more level."""

    return isinstance(node, ast.If) and isinstance(parent, ast.If) and parent.orelse == [node]

def max_nesting(function):
    """How many blocks sit inside one another at the deepest point."""
    deepest, pending = 0, [(function, 0)]

    while pending:
        node, depth = pending.pop()
        deepest = max(deepest, depth)

        for child in ast.iter_child_nodes(node):
            if not isinstance(child, OWN_SCOPE):
                pending.append((child, depth + (isinstance(child, NESTING_NODES) and not is_elif(child, node))))

    return deepest

def is_boolean(annotation, default):
    return (isinstance(annotation, ast.Name) and annotation.id == "bool") or (isinstance(default, ast.Constant) and isinstance(default.value, bool))

def boolean_parameters(arguments):
    """How many parameters are annotated `bool` or default to True or False."""
    positional = arguments.posonlyargs + arguments.args
    defaults = [None] * (len(positional) - len(arguments.defaults)) + arguments.defaults
    pairs = list(zip(positional, defaults)) + list(zip(arguments.kwonlyargs, arguments.kw_defaults))

    return len([argument for argument, default in pairs if argument.arg not in RECEIVER_NAMES and is_boolean(argument.annotation, default)])

def python_bodies(source):
    """(name, line_number, statement_variables, branch_count, last_line, has_docstring, max_nesting, boolean_parameters, parameter_count)
    for every def."""
    bodies = []

    for node in ast.walk(parse_python(source)):
        if isinstance(node, FUNCTIONS):
            locals_ = local_names(node)
            used = [names_used(statement) & locals_ for statement in node.body]
            bodies.append((node.name, node.lineno, used, branch_count(node), node.end_lineno, ast.get_docstring(node) is not None,
                       max_nesting(node), boolean_parameters(node.args), count_arguments(node.args)))

    return bodies
