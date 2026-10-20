import re

from ....language_parsers.deor.tree import parse_deor, walk_statements
from ....language_parsers.deor.words import blank_strings

# a crash( call, but not one preceded by a word character or a dot, so x.crash( and no_crash( are skipped
CRASH_CALL = re.compile(r"(?<![\w.])crash\(")
# a print( or crash( call, with the same rule against a word character or dot before it
LOUD_CALL = re.compile(r"(?<![\w.])(?:print|crash)\(")
# the words 'is not valid' with any amount of whitespace between them
NOT_VALID_CHECK = re.compile(r"\bis\s+not\s+valid\b")

def is_loud(statement):
    """A failed check is loud when what is under it prints, crashes, or returns an answer."""

    for inner in walk_statements(statement.children):
        if inner.keyword == "return" or LOUD_CALL.search(blank_strings(inner.text)):
            return True

    return False

def deor_handlers(source):
    """(line_number, is_catch, is_loud, is_broad) for each crash and each `is not valid` check.

    Deor has no exceptions. A crash is the same as a raise, and a check for a value that is not valid is the closest thing to a catch."""
    found = []

    for statement in walk_statements(parse_deor(source).roots):
        text = blank_strings(statement.text)

        if CRASH_CALL.search(text):
            found.append((statement.first_line, False, True, False))

        if statement.keyword in ("if", "else") and NOT_VALID_CHECK.search(text):
            found.append((statement.first_line, True, is_loud(statement), False))

    return found
