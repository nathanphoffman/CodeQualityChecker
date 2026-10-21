import ast
import sys

from ....language_parsers.python.parse_python import parse_python

DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef)

def standard_library_aliases(tree):
    """Names bound by `import x` or `import x as y` for standard library modules. `subprocess.run(...)` is not our own `run`."""
    aliases = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            aliases.update(alias.asname or alias.name.split(".")[0] for alias in node.names
                           if alias.name.split(".")[0] in sys.stdlib_module_names)

    return aliases

def called_name(call, outside):
    """The name being called: `run(x)` is run and `self.run(x)` is run too, but `subprocess.run(x)` is outside the project."""

    if isinstance(call.func, ast.Name):
        return call.func.id

    belongs_outside = isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id in outside

    return None if belongs_outside else getattr(call.func, "attr", None)

def own_calls(function, outside):
    """Calls made by this function, leaving out the functions defined inside it since they get their own entry."""
    found, pending = set(), list(ast.iter_child_nodes(function))

    while pending:
        node = pending.pop()

        if isinstance(node, DEFINITIONS):
            continue

        if isinstance(node, ast.Call) and called_name(node, outside):
            found.add(called_name(node, outside))

        pending.extend(ast.iter_child_nodes(node))

    return frozenset(found)

def python_calls(source):
    """[(name, line_number, called_names)] for every def."""
    tree = parse_python(source)
    outside = standard_library_aliases(tree)

    return [(node.name, node.lineno, own_calls(node, outside)) for node in ast.walk(tree) if isinstance(node, DEFINITIONS)]
