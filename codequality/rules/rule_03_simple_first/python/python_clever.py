import ast

from ....language_parsers.python.parse_python import parse_python

REGEX_FUNCTIONS = {"compile", "match", "search", "sub", "subn", "findall", "finditer", "fullmatch", "split"}
PIPELINE_FUNCTIONS = {"map", "filter", "reduce", "sorted", "zip", "reversed"}
BIT_OPERATORS = (ast.LShift, ast.RShift, ast.BitXor)
COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
MIN_PIPELINE_CALLS = 3

def called_name(node):
    if not isinstance(node, ast.Call):
        return None

    return node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)

def is_regex_call(node):
    is_re_module = isinstance(getattr(node, "func", None), ast.Attribute) and getattr(node.func.value, "id", None) == "re"

    return is_re_module and called_name(node) in REGEX_FUNCTIONS

def is_nested_comprehension(node):
    if not isinstance(node, COMPREHENSIONS):
        return False

    return len(node.generators) > 1 or sum(isinstance(child, COMPREHENSIONS) for child in ast.walk(node)) > 1

def is_pipeline(node):
    if called_name(node) not in PIPELINE_FUNCTIONS:
        return False

    return sum(called_name(child) in PIPELINE_FUNCTIONS for child in ast.walk(node)) >= MIN_PIPELINE_CALLS

CHECKS = [
    (is_regex_call, "regex"),
    (lambda node: called_name(node) == "reduce", "reduce"),
    (lambda node: isinstance(node, ast.IfExp) and isinstance(node.orelse, ast.IfExp), "chained_ternary"),
    (lambda node: isinstance(node, ast.Lambda) and sum(isinstance(n, ast.Lambda) for n in ast.walk(node)) > 1, "nested_closure"),
    (lambda node: isinstance(node, ast.BinOp) and isinstance(node.op, BIT_OPERATORS), "bit_tricks"),

    (lambda node: isinstance(node, ast.NamedExpr), "walrus"),
    (is_nested_comprehension, "nested_comprehension"),
    (is_pipeline, "long_chain"),
]

def python_clever(source):
    """(kind, line_number) for every clever construct."""
    found = []

    for node in ast.walk(parse_python(source)):
        for check, kind in CHECKS:
            if check(node):
                found.append((kind, node.lineno))

    return found
