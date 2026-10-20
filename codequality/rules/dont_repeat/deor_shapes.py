import re

from ...language_parsers.deor.declarations import FUNCTION_KINDS, declarations_in
from ...language_parsers.deor.tree import parse_deor
from ...language_parsers.deor.words import KEYWORDS, PRIMITIVE_TYPES, TOKEN_PATTERN

NODES_PER_TOKEN = 2  # a statement of n tokens is about 2n syntax nodes in the other languages, which is what the size limits are tuned for
IDENTIFIER = re.compile(r"[A-Za-z_]\w*$")
NUMBER = re.compile(r"\d")

def shape_token(token):
    """Names become "id", numbers "num" and strings "str", so renamed copies look the same. Keywords and operators stay."""

    if token.startswith('"'):
        return "str"

    if NUMBER.match(token):
        return "num"

    return token if token in KEYWORDS | PRIMITIVE_TYPES or not IDENTIFIER.match(token) else "id"

def shape_of(statement):
    """(text, size) for a statement, its header tokens first and then everything indented under it."""
    tokens = [shape_token(token) for token in TOKEN_PATTERN.findall(statement.text)]
    rust = [shape_token(token) for line in statement.rust_lines for token in TOKEN_PATTERN.findall(line.code)]
    children = [shape_of(child) for child in statement.children if child.keyword not in FUNCTION_KINDS]
    text = " ".join(tokens + rust) + "(" + ",".join(text for text, _ in children) + ")"

    return text, NODES_PER_TOKEN * len(tokens + rust) + sum(size for _, size in children)

def statement_shapes(statements):
    """[(shape text, size, first line, last line)] for a list of sibling statements."""
    shapes = []

    for statement in statements:
        text, size = shape_of(statement)
        shapes.append((text, size, statement.first_line, statement.end_line))

    return shapes

def blocks_within(function):
    """The body first, then every block indented inside it. Macros declared inside are left to their own entry."""
    blocks, pending = [], [function]

    while pending:
        node = pending.pop()
        blocks += [node.children] if node.children else []
        pending += [child for child in node.children if child.keyword not in FUNCTION_KINDS]

    return blocks

def deor_shapes(source):
    """(name, line_number, sequences) for every function and macro: the body's shapes first, then each nested block's."""
    found = []

    for declaration in declarations_in(parse_deor(source).roots, FUNCTION_KINDS):
        function = declaration.statement
        blocks = [block for block in blocks_within(function) if block]
        found.append((declaration.label, function.first_line, [statement_shapes(block) for block in blocks]))

    return found
