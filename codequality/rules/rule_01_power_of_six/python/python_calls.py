import ast

from ....language_parsers.python.parse_python import parse_python

DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef)

def called_name(call):
    """The name being called: `run(x)` is run and `self.run(x)` is run too."""

    return call.func.id if isinstance(call.func, ast.Name) else getattr(call.func, "attr", None)

def own_calls(function):
    """Calls made by this function, leaving out the functions defined inside it since they get their own entry."""
    found, pending = set(), list(ast.iter_child_nodes(function))

    while pending:
        node = pending.pop()

        if isinstance(node, DEFINITIONS):
            continue

        if isinstance(node, ast.Call) and called_name(node):
            found.add(called_name(node))

        pending.extend(ast.iter_child_nodes(node))

    return frozenset(found)

def python_calls(source):
    """[(name, line_number, called_names)] for every def."""

    return [(node.name, node.lineno, own_calls(node)) for node in ast.walk(parse_python(source)) if isinstance(node, DEFINITIONS)]
