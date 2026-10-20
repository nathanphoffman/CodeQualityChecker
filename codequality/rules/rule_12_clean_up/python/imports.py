import ast

from ..shared.limits import NOQA_MARKER

FUTURE_MODULE = "__future__"
EVERYTHING = "*"

def bound_names(node):
    """The names an import statement creates: `import a.b` binds a, `from m import x as y` binds y."""

    if isinstance(node, ast.ImportFrom) and node.module == FUTURE_MODULE:
        return []

    return [alias.asname or alias.name.split(".")[0] for alias in node.names if alias.name != EVERYTHING]

def mentioned_names(tree):
    """Variable names, plus every string (which catches __all__ and quoted type hints)."""
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}

    return names | {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}

def python_imports(tree, lines, is_package_init):
    """(imported names, line numbers of the unused ones). A package's __init__.py re-exports on purpose, so it is skipped."""
    mentioned, total, unused = mentioned_names(tree), 0, []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)) or is_package_init or NOQA_MARKER in lines[node.lineno - 1]:
            continue

        names = bound_names(node)
        total += len(names)
        unused += [node.lineno for name in names if name not in mentioned]

    return total, unused
