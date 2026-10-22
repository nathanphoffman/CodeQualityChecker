from ....language_parsers.tree_sitter.tree_walk import walk
from ..shared.Code_Use import Code_Use
from ....language_parsers.tree_sitter.syntax_shapes import OPERATOR_FIELD
from ....language_parsers.tree_sitter.use_names import called_name, dotted

STRING_TEXT_TYPES = {"string_fragment", "string_content", "interpreted_string_literal_content", "raw_string_literal_content",
                     "string_literal_content"}
# calls that put values into a string: Hare, C, Go and C#
STRING_BUILDERS = {"fmt.asprintf", "fmt.bsprintf", "strings.concat", "strings.join", "sprintf", "snprintf", "asprintf", "strcat", "fmt.Sprintf", "string.Format", "string.Concat"}

LEAF_STRING_TYPES = {"string", "string_literal", "verbatim_string_literal"}  # Mojo f-strings, Fortran strings and C# @"..." have no inner content node
STRING_PREFIXES = "fFrRbB@$"  # Mojo writes f"..." for a string with values put into it, and C# writes @"..."

def is_text_piece(node):
    return node.type in STRING_TEXT_TYPES or (node.type in LEAF_STRING_TYPES and node.child_count == 0)

def piece_text(node):
    """The words in a string piece, without the quotes and the f in front that a whole-string node has."""
    text = node.text.decode()

    return text.lstrip(STRING_PREFIXES).strip("\"'") if node.type in LEAF_STRING_TYPES else text

def literal_text(node):
    """The text pieces of the string literals inside a node, in source order."""
    pieces = sorted((child for child in walk(node) if is_text_piece(child)), key=lambda child: child.start_byte)

    return " ".join(piece_text(piece) for piece in pieces)

def operator_text(node):
    """The operator of a binary expression: a field in most grammars, but a bare token in Mojo's."""
    operator = node.child_by_field_name(OPERATOR_FIELD)

    return operator.text if operator is not None else next((child.text for child in node.children if not child.is_named), b"")

def is_built_from_parts(node):
    """Template strings with ${}, "a" + b, Rust format!, and calls like Hare's strings::concat, C's sprintf and Go's fmt.Sprintf."""

    if node.type == "template_string":
        return any(child.type == "template_substitution" for child in node.children)

    if node.type in ("binary_expression", "binary_operator"):
        return operator_text(node) == b"+"

    if node.type in ("concatenation_expression", "interpolated_string_expression"):
        return True  # Fortran's // and C#'s $"..."

    if node.type == "string" and node.child_count == 0:
        return node.text.decode().startswith(("f", "F")) and "{" in node.text.decode()  # a Mojo f-string

    if node.type == "call_expression":
        return dotted(called_name(node).text.decode()) in STRING_BUILDERS

    macro = node.child_by_field_name("macro")

    return node.type == "macro_invocation" and macro.text == b"format"

def string_use(node, names, lines):
    """A "dynamic_string" use for a string built from parts, or None."""
    text = literal_text(node).strip().upper() if is_built_from_parts(node) else ""
    row = node.start_point.row

    return Code_Use("dynamic_string", row + 1, text, names, lines[row].lower()) if text else None
