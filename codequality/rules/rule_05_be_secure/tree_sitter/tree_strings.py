from ....language_parsers.tree_sitter.tree_walk import walk
from ..shared.Code_Use import Code_Use
from ....language_parsers.tree_sitter.syntax_shapes import OPERATOR_FIELD
from ....language_parsers.tree_sitter.use_names import dotted

STRING_TEXT_TYPES = {"string_fragment", "string_content"}
HARE_STRING_BUILDERS = {"fmt.asprintf", "fmt.bsprintf", "strings.concat", "strings.join"}

def literal_text(node):
    """The text pieces of the string literals inside a node, in source order."""
    pieces = sorted((child for child in walk(node) if child.type in STRING_TEXT_TYPES), key=lambda child: child.start_byte)

    return " ".join(piece.text.decode() for piece in pieces)

def is_built_from_parts(node):
    """Template strings with ${}, "a" + b, Rust format!, and Hare's fmt::asprintf and strings::concat."""

    if node.type == "template_string":
        return any(child.type == "template_substitution" for child in node.children)

    if node.type == "binary_expression":
        return node.child_by_field_name(OPERATOR_FIELD).text == b"+"

    if node.type == "call_expression" and node.child_by_field_name("callee") is not None:
        return dotted(node.child_by_field_name("callee").text.decode()) in HARE_STRING_BUILDERS

    macro = node.child_by_field_name("macro")

    return node.type == "macro_invocation" and macro.text == b"format"

def string_use(node, names, lines):
    """A "dynamic_string" use for a string built from parts, or None."""
    text = literal_text(node).strip().upper() if is_built_from_parts(node) else ""
    row = node.start_point.row

    return Code_Use("dynamic_string", row + 1, text, names, lines[row].lower()) if text else None
