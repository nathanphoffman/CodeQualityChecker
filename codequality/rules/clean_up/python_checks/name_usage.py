import ast
from collections import Counter

from ..Cleanup_Findings import Name_Usage
from ..limits import PRIVATE_PREFIX

DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
DUNDER = "__"


def is_private(name):
    return name.startswith(PRIVATE_PREFIX) and not (name.startswith(DUNDER) and name.endswith(DUNDER))


def python_name_usage(tree):
    """Private functions and classes, and how often every name is mentioned (names, attributes, imports, strings)."""
    references, private = Counter(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            references[node.id] += 1
        elif isinstance(node, ast.Attribute):
            references[node.attr] += 1
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            references[node.value] += 1
        elif isinstance(node, ast.alias):
            references[node.name.split(".")[-1]] += 1
        elif isinstance(node, DEFINITIONS):
            references[node.name] += 1
            private += [(node.name, node.lineno)] if is_private(node.name) else []
    return Name_Usage(private, references)
