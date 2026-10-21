import re

# Words that mean something to Deor itself, so they are never a variable's name.
KEYWORDS = {"fn", "if", "else", "for", "in", "return", "break", "continue", "block", "macro", "unsafe_macro", "macro_run",
            "unsafe_macro_run", "avow", "move", "const", "and", "or", "not", "is", "as", "with", "at", "end", "of", "to",
            "true", "false", "empty", "list", "func", "struct", "shape", "enum", "type", "rust", "valid", "none", "import"}

PRIMITIVE_TYPES = {"int", "float", "bool", "string", "raw", "void"}
BUILTINS = {"print", "crash", "len", "range", "args", "input"}

# Statements that start with one of these are control flow, never a declaration like `Type name = value`.
CONTROL_KEYWORDS = {"if", "else", "for", "return", "break", "continue", "block", "macro_run", "unsafe_macro_run"}

# a double-quoted string; (?:\\.|[^"\\])* reads an escaped character or any character that isn't a quote or backslash
STRING_PATTERN = re.compile(r'"(?:\\.|[^"\\])*"')

# a number: digits and underscores, optionally a dot and more digits, not part of a longer word or name
NUMBER_PATTERN = re.compile(r"(?<![\w.])\d[\d_]*(?:\.\d[\d_]*)?")

# Clever on purpose: one token of a statement, for comparing the shapes of statements.
#   a string, a number, a word, or any other single character (an operator or a bracket)
TOKEN_PATTERN = re.compile(r'"(?:\\.|[^"\\])*"|(?<![\w.])\d[\d_]*(?:\.\d[\d_]*)?|[A-Za-z_]\w*|\S')

# a name: a letter or underscore, then word characters, not part of a longer word or after a dot
IDENTIFIER_PATTERN = re.compile(r"(?<![\w.])[A-Za-z_]\w*")

def blank_strings(text):
    """The text with everything between the quotes of each string turned into spaces, so words inside strings are ignored."""

    return STRING_PATTERN.sub(lambda hit: '"' + " " * (len(hit.group()) - 2) + '"', text)

def identifiers(text):
    """The names a statement mentions, in order, without keywords, type words and built-in functions."""
    reserved = KEYWORDS | PRIMITIVE_TYPES

    return [name for name in IDENTIFIER_PATTERN.findall(blank_strings(text)) if name not in reserved]

def split_top_level(text):
    """Splits at commas that are not inside brackets: `Type one, Type two` -> two pieces."""
    pieces, depth, current = [], 0, ""

    for char in text:
        depth += (char in "([") - (char in ")]")

        if char == "," and depth == 0:
            pieces.append(current)
            current = ""
        else:
            current += char

    return [piece.strip() for piece in pieces + [current] if piece.strip()]
