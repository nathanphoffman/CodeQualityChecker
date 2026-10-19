import ast
import io
import tokenize

from ...python_support.parse_python import parse_python
from .Spacing_Gaps import Spacing_Gaps

CONTROL_STATEMENTS = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Match, ast.Return,
                      ast.Raise, ast.Break, ast.Continue, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
BLOCK_FIELDS = ("body", "orelse", "finalbody")

def python_string_lines(source):
    """Line numbers inside multi-line strings. Their blank lines are text, not spacing, and can't be changed."""
    inside = set()

    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.STRING and token.end[0] > token.start[0]:
            inside |= set(range(token.start[0] + 1, token.end[0] + 1))

    return inside

def first_line(statement):
    """Where a statement starts, counting its decorators."""

    return min([decorator.lineno for decorator in getattr(statement, "decorator_list", [])] + [statement.lineno])

def attached_start(lines, start):
    """Comments directly above a statement belong to it, so a blank line goes above the comments."""

    while start >= 2 and lines[start - 2].strip().startswith("#"):
        start -= 1

    return start

def statement_groups(tree):
    """Every list of statements that sit side by side: bodies, else branches, finally blocks, and the cases of a match."""
    groups = []

    for node in ast.walk(tree):
        for field in BLOCK_FIELDS:
            statements = getattr(node, field, None)
            groups += [statements] if isinstance(statements, list) and statements and isinstance(statements[0], ast.stmt) else []

        groups += [node.cases] if isinstance(node, ast.Match) else []

    return groups

def span(item):
    """(first line, last line) of a statement or of one case of a match."""

    if isinstance(item, ast.match_case):
        return item.pattern.lineno, item.body[-1].end_lineno

    return first_line(item), item.end_lineno

def python_gaps(source):
    """A Spacing_Gaps for one Python file."""
    lines, control_missing, block_missing = source.splitlines(), [], []
    control_total = block_total = 0

    for group in statement_groups(parse_python(source)):
        for previous, item in zip(group, group[1:]):
            start, (previous_first, previous_last) = attached_start(lines, span(item)[0]), span(previous)

            if start <= previous_last:
                continue

            blank_above = not lines[start - 2].strip()

            if isinstance(item, CONTROL_STATEMENTS + (ast.match_case,)):
                control_total += 1
                control_missing += [] if blank_above else [start]

            if previous_last > previous_first or isinstance(previous, DEFINITIONS):  # multi-line, or a definition of any length
                block_total += 1
                block_missing += [] if blank_above else [start]

    return Spacing_Gaps(control_total, sorted(set(control_missing)), block_total, sorted(set(block_missing)))
