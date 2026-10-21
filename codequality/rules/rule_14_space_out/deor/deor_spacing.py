from ....language_parsers.deor.tree import parse_deor, walk_statements
from ..shared.comment_gaps import comment_block_gaps

CONTROL_KEYWORDS = {"if", "for", "return", "break", "continue", "fn", "macro", "unsafe_macro", "struct", "enum", "type",
                    "shape", "block", "rust"}

CONTINUATIONS = ("else",)

def sibling_lists(roots):
    """Every list of statements that sit side by side: the file's top level, and the children of each statement."""
    lists = [roots]

    for statement in walk_statements(roots):
        lists += [statement.children] if statement.children else []

    return lists

def attached_start(lines, start):
    """Comments directly above a statement belong to it, so a blank line goes above the comments."""

    while start > 1 and lines[start - 2].comment is not None and not lines[start - 2].code:
        start -= 1

    return start

def comment_gaps(lines, roots):
    """Comments on their own line follow the same rule as control statements: a blank line above, unless first in a block."""
    comment_lines = {line.number for line in lines if line.comment is not None and not line.code}
    blank_lines = {line.number for line in lines if line.comment is None and not line.code}
    finished_lines = {statement.end_line for statement in walk_statements(roots)}

    return comment_block_gaps(comment_lines, blank_lines, finished_lines)

def deor_gaps(source):
    """(before_control_total, before_control_missing, after_block_total, after_block_missing) for one Deor file.

    Same two checks as the other languages: a blank line above control flow and definitions, and a blank line after
    a statement that spans several lines or has a block under it. `else` and `else if` continue the `if` above them."""

    parsed = parse_deor(source)
    lines, block_total = parsed.lines, 0
    control_seen, control_missing, block_missing = set(), [], []

    for siblings in sibling_lists(parsed.roots):
        for previous, item in zip(siblings, siblings[1:]):
            if item.keyword in CONTINUATIONS:
                continue

            start = attached_start(lines, item.first_line)
            blank_above = start == 1 or not lines[start - 2].code and lines[start - 2].comment is None
            leading = previous

            if item.keyword in CONTROL_KEYWORDS:
                control_seen.add(start)
                control_missing += [] if blank_above else [start]

            if leading.end_line > leading.first_line or leading.keyword in CONTROL_KEYWORDS - {"return", "break", "continue"}:
                block_total += 1
                block_missing += [] if blank_above else [start]

    comment_seen, comment_missing = comment_gaps(lines, parsed.roots)
    control_seen |= comment_seen

    return len(control_seen), sorted(set(control_missing + comment_missing)), block_total, sorted(set(block_missing))
