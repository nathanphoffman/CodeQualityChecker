import ast

from .Code_Use import Code_Use

BUILDING_OPERATORS = (ast.Add, ast.Mod)
VARIABLE_PARTS = (ast.Name, ast.Attribute, ast.Call, ast.Subscript)


def literal_parts(node):
    """The text pieces of a string being built, in source order."""
    constants = [n for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    constants.sort(key=lambda n: (n.lineno, n.col_offset))
    return " ".join(constant.value for constant in constants)


def is_format_call(node):
    """"a {}".format(b)"""
    if not isinstance(node, ast.Call):
        return False
    return getattr(node.func, "attr", None) == "format" and isinstance(node.func.value, ast.Constant)


def is_built_from_parts(node):
    """f-strings, "a" + b, "a %s" % b and "a {}".format(b)."""
    if isinstance(node, ast.JoinedStr):
        return any(isinstance(part, ast.FormattedValue) for part in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, BUILDING_OPERATORS):
        return any(isinstance(n, VARIABLE_PARTS) for n in ast.walk(node))
    return is_format_call(node)


def string_use(node, lines):
    """A "dynamic_string" use for a string built from parts, or None."""
    if not is_built_from_parts(node):
        return None
    text = literal_parts(node).strip().upper()
    return Code_Use("dynamic_string", node.lineno, text, frozenset(), lines[node.lineno - 1].lower()) if text else None
