import ast

from ..shared.limits import PRIVATE_PREFIX

FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
SCOPE_BREAKS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
DYNAMIC_LOOKUPS = {"locals", "vars", "eval", "exec"}

def scope_nodes(function):
    """Nodes in the function's own scope: nested functions and classes are left to their own turn."""
    found, pending = [], list(ast.iter_child_nodes(function))

    while pending:
        node = pending.pop()
        found.append(node)
        pending += [child for child in ast.iter_child_nodes(node) if not isinstance(child, SCOPE_BREAKS)]

    return found

def assigned_names(function):
    """{name: line} for plain assignments, annotated assignments, := and `except ... as name`."""
    assigned = {}

    for node in scope_nodes(function):
        targets = node.targets if isinstance(node, ast.Assign) else [getattr(node, "target", None)]

        if isinstance(node, (ast.Assign, ast.NamedExpr)) or (isinstance(node, ast.AnnAssign) and node.value is not None):
            assigned.update({t.id: node.lineno for t in targets if isinstance(t, ast.Name)})
        elif isinstance(node, ast.ExceptHandler) and node.name:
            assigned[node.name] = node.lineno

    return {name: line for name, line in assigned.items() if not name.startswith(PRIVATE_PREFIX)}

def read_names(function):
    """Names read anywhere in the function, nested functions included. `x += 1` and global/nonlocal count as use."""
    names = {node.id for node in ast.walk(function) if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Store)}
    names |= {node.target.id for node in ast.walk(function) if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name)}

    for node in ast.walk(function):
        names |= set(node.names) if isinstance(node, (ast.Global, ast.Nonlocal)) else set()

    return names

def python_variables(tree):
    """(assigned variables, line numbers of the ones never read)."""
    total, unused = 0, []

    for function in [node for node in ast.walk(tree) if isinstance(node, FUNCTIONS)]:
        if DYNAMIC_LOOKUPS & read_names(function):
            continue

        assigned, read = assigned_names(function), read_names(function)
        total += len(assigned)
        unused += [line for name, line in assigned.items() if name not in read]

    return total, unused
