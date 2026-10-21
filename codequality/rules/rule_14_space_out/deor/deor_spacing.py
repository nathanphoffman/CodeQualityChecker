from ....language_parsers.deor.tree import parse_deor, walk_statements

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

def deor_gaps(source):
    """(before_control_total, before_control_missing, after_block_total, after_block_missing) for one Deor file.

    Same two checks as the other languages: a blank line above control flow and definitions, and a blank line after
    a statement that spans several lines or has a block under it. `else` and `else if` continue the `if` above them."""

    lines = parse_deor(source).lines
    control_total = block_total = 0
    control_missing, block_missing = [], []

    for siblings in sibling_lists(parse_deor(source).roots):
        for previous, item in zip(siblings, siblings[1:]):
            if item.keyword in CONTINUATIONS:
                continue

            start = attached_start(lines, item.first_line)
            blank_above = start == 1 or not lines[start - 2].code and lines[start - 2].comment is None
            leading = previous

            if item.keyword in CONTROL_KEYWORDS:
                control_total += 1
                control_missing += [] if blank_above else [start]

            if leading.end_line > leading.first_line or leading.keyword in CONTROL_KEYWORDS - {"return", "break", "continue"}:
                block_total += 1
                block_missing += [] if blank_above else [start]

    return control_total, sorted(set(control_missing)), block_total, sorted(set(block_missing))
