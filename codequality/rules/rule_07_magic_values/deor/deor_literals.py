import re

from ....language_parsers.deor.tree import parse_deor, walk_statements
from ....language_parsers.deor.words import NUMBER_PATTERN, STRING_PATTERN, blank_strings

CONSTANT_KEYWORD = "const"
IMPORT_KEYWORD = "import"
NUMBER, STRING = "number", "string"

# Clever on purpose: a minus sign that belongs to a number rather than subtracting it.
#   the start of the statement, or an operator or bracket, then "-" and the digit it negates
NEGATIVE_NUMBER = re.compile(r"(?:^|[=(,\[<>+*/%-])\s*-\s*$")

def number_value(text):
    cleaned = text.replace("_", "")

    return float(cleaned) if "." in cleaned else int(cleaned)

def literals_of(statement):
    """[(kind, value, line)] for the strings and numbers in one statement."""
    text, line, found = statement.text, statement.first_line, []
    is_import = statement.keyword == IMPORT_KEYWORD

    for hit in ([] if is_import else STRING_PATTERN.finditer(text)):
        found.append((STRING, hit.group()[1:-1], line))

    for hit in NUMBER_PATTERN.finditer(blank_strings(text)):
        value = number_value(hit.group())
        negated = NEGATIVE_NUMBER.search(text[:hit.start()])
        found.append((NUMBER, -value if negated else value, line))

    return found

def deor_literals(source):
    """[(kind, value, line, in_constant)] for every string and number written in Deor code. `rust` blocks are not Deor."""
    found = []

    for statement in walk_statements(parse_deor(source).roots):
        in_constant = statement.keyword == CONSTANT_KEYWORD
        found += [(kind, value, line, in_constant) for kind, value, line in literals_of(statement)]

    return found
