import ast

from ....python_support.parse_python import parse_python
from .Code_Use import Code_Use
from .python_strings import string_use


def dotted_name(node):
    """`os.path.join` for an attribute chain; chains that start from a call or literal keep only the attribute names."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def names_in(node):
    names = [n.id for n in ast.walk(node) if isinstance(n, ast.Name)]
    names += [n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)]
    return frozenset(name.lower() for name in names)


def call_use(node, lines):
    text = "".join(ast.unparse(node).split())
    return Code_Use(dotted_name(node.func), node.lineno, text, names_in(node), lines[node.lineno - 1].lower())


def python_uses(source):
    lines = source.splitlines()
    uses = []
    for node in ast.walk(parse_python(source)):
        if isinstance(node, ast.Call):
            uses.append(call_use(node, lines))
        built = string_use(node, lines)
        if built:
            uses.append(built)
    return uses
