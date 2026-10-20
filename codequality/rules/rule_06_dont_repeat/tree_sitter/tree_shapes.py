from ..deor.deor_shapes import deor_shapes
from ....source_code import DEOR
from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.syntax_shapes import BODY_FIELD, FUNCTION_TYPES, IDENTIFIER_TYPES, OPERATOR_FIELD
from ....language_parsers.tree_sitter.tree_functions import function_name, statements_of
from ....language_parsers.tree_sitter.tree_walk import walk
from ..shared.Function_Shape import Function_Shape, Statement_Shape

BLOCK_TYPES = {"block", "statement_block"}
KEPT_NAME_TYPES = {"field_identifier", "property_identifier"}  # method and field names stay, like in Python

def label_of(node, language):
    """Variable names become "id". Operators and method names stay, so `a + b` differs from `a - b`."""

    if node.type in IDENTIFIER_TYPES[language]:
        return "id"

    operator = node.child_by_field_name(OPERATOR_FIELD)
    kept = node.text.decode() if node.type in KEPT_NAME_TYPES else (operator.text.decode() if operator else "")

    return f"{node.type}.{kept}" if kept else node.type

def shape_of(node, language):
    """(text, size) like python_shapes.shape_of."""
    children = [shape_of(child, language) for child in node.named_children if "comment" not in child.type]

    return f"{label_of(node, language)}({','.join(text for text, _ in children)})", 1 + sum(size for _, size in children)

def blocks_within(function, language):
    """The body block first, then every block nested in it. Nested functions are left to their own entry."""
    blocks, pending = [], [function.child_by_field_name(BODY_FIELD)]

    while pending:
        node = pending.pop()
        blocks += [node] if node.type in BLOCK_TYPES else []
        pending += [child for child in node.children if child.type not in FUNCTION_TYPES[language]]

    return blocks

def block_shapes(block, language):
    shapes = []

    for statement in statements_of(block):
        text, size = shape_of(statement, language)
        shapes.append(Statement_Shape(text, size, statement.start_point.row + 1, statement.end_point.row + 1))

    return shapes

def deor_function_shapes(source):
    return [Function_Shape(name, line, [[Statement_Shape(*shape) for shape in sequence] for sequence in sequences])
            for name, line, sequences in deor_shapes(source)]

def tree_shapes(source, language):
    if language == DEOR:
        return deor_function_shapes(source)

    found = []

    for node in walk(parse_tree(source, language)):
        body = node.child_by_field_name(BODY_FIELD)

        if node.type in FUNCTION_TYPES[language] and body is not None and body.type in BLOCK_TYPES:
            sequences = [block_shapes(block, language) for block in blocks_within(node, language)]
            found.append(Function_Shape(function_name(node), node.start_point.row + 1, sequences))

    return found
