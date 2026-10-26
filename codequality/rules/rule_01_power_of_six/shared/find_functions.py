import re

from ....language_parsers.deor.declarations import FUNCTION_KINDS, declarations_in
from ....language_parsers.deor.tree import parse_deor
from ....source_code import CSHARP, DEOR, FORTRAN, MOJO, NAME_GROUP, PAREN_GROUP, PYTHON, REXX, blank_out_text, line_number_at, matching_close
from ..python.python_functions import python_functions
from ..tree_sitter.tree_function_infos import tree_function_infos
from .Function_Info import Function_Info
from .limits import CONTROL_KEYWORDS, IGNORED_ARGUMENT_PREFIXES, VOID_PARAMETERS

OPENERS = "([{<"
CLOSERS = ")]}>"

# Clever on purpose: finding a function start without a real parser.
# Each pattern captures the function name and the "(" that opens its arguments.
#   rust: `fn name<T>(`
#   hare: `fn name(`
#   go: `func name(` and methods like `func (s *Server) name(`
#   c: a name followed by "(" at the start of a line, with an optional return type in front (prototypes have no body, so they are dropped)
#   typescript: `function name(`, `name = (` / `name: Type = async (` for arrows,
#   and an indented `name(` for class methods (control keywords are filtered out later).
START_PATTERNS = {
    "rust": [re.compile(r"\bfn\s+(?P<name>\w+)\s*(?:<[^>]*>)?\s*(?P<paren>\()")],  # "fn", a name, optional <generics>, then the "(" opening the arguments

    "go": [re.compile(r"\bfunc\s+(?:\([^)]*\)\s*)?(?P<name>\w+)\s*(?:\[[^\]]*\]\s*)?(?P<paren>\()")],  # "func", an optional (receiver), a name, optional [type parameters], then the "(" opening the arguments
    "c": [re.compile(r"^(?:[A-Za-z_][\w \t\*]*?[ \t\*])?(?P<name>[A-Za-z_]\w*)[ \t]*(?P<paren>\()", re.M)],  # an optional return type, a name, then "(" with nothing indented before it
    "hare": [re.compile(r"\bfn\s+(?P<name>\w+)\s*(?P<paren>\()")],  # "fn", a name, then the "(" opening the arguments

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

    return len([piece for piece in pieces if piece and piece != VOID_PARAMETERS and not piece.startswith(IGNORED_ARGUMENT_PREFIXES)])

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

def deor_function_infos(source):
    """A Deor macro is measured like a function: lines from its header to its last body line."""
    declarations = declarations_in(parse_deor(source).roots, FUNCTION_KINDS)

    return [Function_Info(item.label, len(item.parameter_names), item.statement.end_line - item.statement.first_line + 1,
                          item.statement.first_line) for item in declarations]

def find_functions(source, language):
    if language == PYTHON:
        return [Function_Info(*fields) for fields in python_functions(source)]

    if language == DEOR:
        return deor_function_infos(source)

    if language in (MOJO, FORTRAN, CSHARP, REXX):
        return tree_function_infos(source, language)

    text = blank_out_text(source, language)
    found = {}

    for pattern in START_PATTERNS[language]:
        for match in pattern.finditer(text):
            info = describe_function(text, match)

            if info:
                found[match.start(PAREN_GROUP)] = info

    return list(found.values())
