from ....tree_sitter_support.tree_walk import walk
from .Code_Use import Code_Use
from ....tree_sitter_support.syntax_shapes import OPERATOR_FIELD

STRING_TEXT_TYPES = {"string_fragment", "string_content"}


def literal_text(node):
    """The text pieces of the string literals inside a node, in source order."""
    pieces = sorted((n for n in walk(node) if n.type in STRING_TEXT_TYPES), key=lambda n: n.start_byte)
    return " ".join(piece.text.decode() for piece in pieces)


def is_built_from_parts(node):
    """Template strings with ${}, "a" + b, and Rust format!."""
    if node.type == "template_string":
        return any(child.type == "template_substitution" for child in node.children)
    if node.type == "binary_expression":
        return node.child_by_field_name(OPERATOR_FIELD).text == b"+"
    macro = node.child_by_field_name("macro")
    return node.type == "macro_invocation" and macro.text == b"format"


def string_use(node, names, lines):
    """A "dynamic_string" use for a string built from parts, or None."""
    text = literal_text(node).strip().upper() if is_built_from_parts(node) else ""
    row = node.start_point.row
    return Code_Use("dynamic_string", row + 1, text, names, lines[row].lower()) if text else None
