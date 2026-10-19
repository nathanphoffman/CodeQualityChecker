import ast

TERMINATORS = (ast.Return, ast.Raise, ast.Break, ast.Continue)
BLOCK_FIELDS = ("body", "orelse", "finalbody")


def statement_lists(tree):
    """Every list of statements in the file: bodies, else branches and finally blocks."""
    lists = []
    for node in ast.walk(tree):
        for field in BLOCK_FIELDS:
            statements = getattr(node, field, None)
            lists += [statements] if isinstance(statements, list) and statements and isinstance(statements[0], ast.stmt) else []
    return lists


def python_unreachable(tree):
    """(statements in the file, line numbers of statements that follow a return, raise, break or continue)."""
    total = len([node for node in ast.walk(tree) if isinstance(node, ast.stmt)])
    unreachable = []
    for statements in statement_lists(tree):
        ends = [index for index, statement in enumerate(statements) if isinstance(statement, TERMINATORS)]
        unreachable += [statement.lineno for statement in statements[ends[0] + 1:]] if ends else []
    return total, unreachable
