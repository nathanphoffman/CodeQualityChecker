import re

from .deor_functions import deor_functions
from .Function_Info import Function_Info
from ...python_support.python_functions import python_functions
from ...source_code import DEOR, NAME_GROUP, PAREN_GROUP, PYTHON, blank_out_text, line_number_at, matching_close
from .limits import CONTROL_KEYWORDS, IGNORED_ARGUMENT_PREFIXES

OPENERS = "([{<"
CLOSERS = ")]}>"

# Clever on purpose: finding a function start without a real parser.
# Each pattern captures the function name and the "(" that opens its arguments.
#   rust: `fn name<T>(`
#   typescript: `function name(`, `name = (` / `name: Type = async (` for arrows,
#   and an indented `name(` for class methods (control keywords are filtered out later).
START_PATTERNS = {
    "rust": [re.compile(r"\bfn\s+(?P<name>\w+)\s*(?:<[^>]*>)?\s*(?P<paren>\()")],  # "fn", a name, optional <generics>, then the "(" opening the arguments

    "typescript": [
        re.compile(r"\bfunction\s*\*?\s*(?P<name>\w+)\s*(?:<[^>]*>)?\s*(?P<paren>\()"),  # "function", optional "*" for generators, a name, optional <generics>, then "("
        re.compile(r"\b(?P<name>\w+)(?:\s*:\s*[^=;(){}]+)?\s*=\s*(?:async\s*)?(?P<paren>\()"),  # arrow functions: a name, optional ": Type", "=", optional "async", then "("
        re.compile(r"^[ \t]+(?:(?:public|private|protected|static|async)\s+)*(?P<name>\w+)\s*(?P<paren>\()", re.M),  # class methods: an indented name with optional modifiers in front, then "("
    ],
}

def split_top_level(text):
    pieces, depth, current = [], 0, ""

    for char in text:
        depth += (char in OPENERS) - (char in CLOSERS)

        if char == "," and depth == 0:
            pieces.append(current)
            current = ""
        else:
            current += char

    return pieces + [current]

def count_arguments(argument_text):
    # Arrows contain ">" which would look like a closing generic.
    cleaned = argument_text.replace("=>", "  ").replace("->", "  ")
    pieces = [piece.strip() for piece in split_top_level(cleaned)]

    return len([p for p in pieces if p and not p.startswith(IGNORED_ARGUMENT_PREFIXES)])

def body_start(text, close_paren):
    """Index of the "{" opening the body, or None for bodiless declarations and expression arrows."""

    for index in range(close_paren + 1, len(text)):
        if text[index] == "{":
            return index

        if text[index] == ";":
            return None

    return None

def describe_function(text, match):
    if match.group(NAME_GROUP) in CONTROL_KEYWORDS:
        return None

    open_paren = match.start(PAREN_GROUP)
    close_paren = matching_close(text, open_paren)
    body_open = close_paren and body_start(text, close_paren)

    body_close = body_open and matching_close(text, body_open)

    if not body_close:
        return None

    first_line = line_number_at(text, match.start())
    last_line = line_number_at(text, body_close)
    arguments = count_arguments(text[open_paren + 1:close_paren])

    return Function_Info(match.group(NAME_GROUP), arguments, last_line - first_line + 1, first_line)

def find_functions(source, language):
    if language == PYTHON:
        return [Function_Info(*fields) for fields in python_functions(source)]

    if language == DEOR:
        return [Function_Info(*fields) for fields in deor_functions(source, count_arguments)]

    text = blank_out_text(source)
    found = {}

    for pattern in START_PATTERNS[language]:
        for match in pattern.finditer(text):
            info = describe_function(text, match)

            if info:
                found[match.start(PAREN_GROUP)] = info

    return list(found.values())
