import re

from ....language_parsers.deor.tree import parse_deor, walk_statements
from ....language_parsers.deor.words import blank_strings

RUST_COMMENT = "//"

# Clever on purpose: the forms of a single Deor statement, used to tell code that was switched off from ordinary words.
#   a typed declaration:  Type name = value
#   an as binding:        name as value
#   an assignment:        name = value, or list at index = value
#   a destructure:        (a, b) in source
#   a call:               name(...)
#   a macro call:         macro_run name
#   control flow:         if, else if, for or return followed by something, or a lone break or continue
STATEMENT_FORMS = [re.compile(pattern) for pattern in (
    r"^(?:const\s+)?[A-Za-z_]\w*\s+[a-z_]\w*\s*=\s*\S",
    r"^[a-z_]\w*\s+as\s+\S",
    r"^[a-z_]\w*(?:\s+at\s+\w+)?\s*=[^=]",
    r"^(?:move\s*)?\(\s*\w+(?:\s*,\s*\w+)*\s*\)\s+in\s+\S",
    r"^[a-z_]\w*\(.*\)$",
    r"^(?:unsafe_)?macro_run\s+\w+$",
    r"^(?:if|else if|for|return)\s+\S",
    r"^(?:break|continue)$",
)]

def deor_raw_comments(source):
    """(first_line, last_line, text, code before it on the line) for every # comment, and every // comment inside a `rust` block."""
    found = []

    for line in parse_deor(source).lines:
        if line.comment is not None:
            found.append((line.number, line.number, "#" + line.comment, line.code))
            continue

        start = blank_strings(line.code).find(RUST_COMMENT) if line.in_rust else -1

        if start >= 0:
            found.append((line.number, line.number, line.code[start:], line.code[:start].strip()))

    return found

def deor_ends(source):
    """{line a statement starts on: last line of the longest statement starting there}."""
    ends = {}

    for statement in walk_statements(parse_deor(source).roots):
        ends[statement.first_line] = max(ends.get(statement.first_line, 0), statement.end_line)

    return ends

def looks_like_deor(text):
    """True when the text is one Deor statement, as in a line of code that someone commented out."""

    return any(form.match(text.strip()) for form in STATEMENT_FORMS)
