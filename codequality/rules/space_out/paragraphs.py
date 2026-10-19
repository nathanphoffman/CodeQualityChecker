from ..comment_why.extract.line_helpers import COMMENT_MARKERS
from .limits import IMPORT_STARTS

def find_paragraphs(lines):
    """[(first line number, length)] for each run of non-blank lines."""
    found, start = [], None

    for number, line in enumerate(lines + [""], start=1):
        if line.strip() and start is None:
            start = number
        elif not line.strip() and start is not None:
            found.append((start, number - start))
            start = None

    return found

def is_judged(lines, first_line, length):
    """Import blocks and runs of comments are one idea each, however long, so they are left out."""
    paragraph = [line.strip() for line in lines[first_line - 1:first_line - 1 + length]]

    return not paragraph[0].startswith(IMPORT_STARTS) and not all(line.startswith(COMMENT_MARKERS) for line in paragraph)

def find_blank_runs(lines, protected=frozenset()):
    """[(first blank line number, length)] for each run of blank lines between code. The start and end of a file don't count.
    `protected` are lines inside multi-line strings, whose blank lines are text and so are not counted."""

    runs, length, seen_code = [], 0, False

    for number, line in enumerate(lines, start=1):
        if line.strip() or number in protected:
            runs += [(number - length, length)] if length and seen_code else []
            length, seen_code = 0, True
        else:
            length += 1

    return runs
