import re

from ....language_parsers.deor.tree import parse_deor, walk_statements
from ....language_parsers.deor.words import blank_strings
from ...rule_14_space_out.deor.deor_spacing import sibling_lists

# a crash( call, but not one preceded by a word character or a dot, so x.crash( and no_crash( are skipped
CRASH_CALL = re.compile(r"(?<![\w.])crash\(")

# a print( or crash( call, with the same rule against a word character or dot before it
LOUD_CALL = re.compile(r"(?<![\w.])(?:print|crash)\(")

# a validity check: 'is valid' or 'is not valid', with any amount of whitespace between the words
VALID_CHECK = re.compile(r"\bis\s+(?:not\s+)?valid\b")
NEGATED_VALID_CHECK = re.compile(r"\bis\s+not\s+valid\b")  # `is not valid` only

def is_loud(statement):
    """A failed check is loud when what is under it prints, crashes, or returns an answer."""

    for inner in walk_statements(statement.children):
        if inner.keyword == "return" or LOUD_CALL.search(blank_strings(inner.text)):
            return True

    return False

def validity_entry(statement, following):
    """(line_number, is_catch, is_loud, is_broad) for an `if` or `else` that checks validity.

    `is not valid` puts the failure under the check itself. `is valid` puts it under the `else` that follows, since the body
    is the working case. With no `else` there is no failure path to judge, so it only counts as an error check, not a catch."""

    if NEGATED_VALID_CHECK.search(blank_strings(statement.text)):
        return (statement.first_line, True, is_loud(statement), False)

    failure = following[0] if following and following[0].keyword == "else" else None

    return (statement.first_line, failure is not None, is_loud(failure) if failure else True, False)

def deor_handlers(source):
    """(line_number, is_catch, is_loud, is_broad) for each crash and each `is valid` or `is not valid` check.

    Deor has no exceptions. A crash is the same as a raise, and a validity check is the closest thing to a catch. Both forms
    count because the code under a valid check may be either the working case or the failure."""

    found = []

    for siblings in sibling_lists(parse_deor(source).roots):
        for index, statement in enumerate(siblings):
            text = blank_strings(statement.text)

            if CRASH_CALL.search(text):
                found.append((statement.first_line, False, True, False))

            if statement.keyword in ("if", "else") and VALID_CHECK.search(text):
                found.append(validity_entry(statement, siblings[index + 1:index + 2]))

    return found
