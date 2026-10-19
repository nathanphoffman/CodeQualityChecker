from ...deor_support.judging.deor_literals import deor_literals
from ...source_code import DEOR
from ...tree_sitter_support.parse_tree import parse_tree
from .Literal_Use import KIND_NUMBER, KIND_STRING, Literal_Use
from ...tree_sitter_support.syntax_shapes import NAME_FIELD

NUMBER_TYPES = {"number", "integer_literal", "float_literal"}
STRING_TYPES = {"string", "string_literal"}
# Code that already names or defines its values: Rust consts, statics, enum values and attributes.
NAMED_TYPES = {"const_item", "static_item", "enum_variant", "attribute_item", "enum_assignment"}
# Strings that are module paths or types, not values: imports, and `"a" | "b"` types.
NOT_VALUE_PARENTS = {"import_statement", "export_statement", "use_declaration", "literal_type", "jsx_attribute"}

RUST_NUMBER_SUFFIXES = ("usize", "isize", "u128", "i128", "u16", "u32", "u64", "i16", "i32", "i64", "f32", "f64", "u8", "i8")

def number_value(text):
    """The number written in the source, or None when it can't be read. Handles 1_000, 0xFF, 2u32 and 10n."""
    cleaned = text.replace("_", "").lower()

    if not cleaned.startswith("0x"):
        cleaned = cleaned.removesuffix("n")

        for suffix in RUST_NUMBER_SUFFIXES:
            cleaned = cleaned.removesuffix(suffix)

    try:
        return int(cleaned, 0)
    except ValueError:
        return float(cleaned) if cleaned.replace(".", "", 1).replace("e", "", 1).lstrip("-").isdigit() else None

def is_constant_declarator(node):
    """`const MAX_RETRIES = 5` in TypeScript."""
    name = node.child_by_field_name(NAME_FIELD) if node.type == "variable_declarator" else None

    return name is not None and name.text.decode().isupper()

def literal_of(node, in_constant):
    line = node.start_point.row + 1
    text = node.text.decode()

    if node.type in NUMBER_TYPES:
        value = number_value(text)

        return Literal_Use(KIND_NUMBER, value, line, in_constant) if value is not None else None

    if node.type in STRING_TYPES and node.parent.type not in NOT_VALUE_PARENTS:
        return Literal_Use(KIND_STRING, text[1:-1], line, in_constant)

    return None

def tree_literals(source, language):
    if language == DEOR:
        return [Literal_Use(*fields) for fields in deor_literals(source)]

    found, pending = [], [(parse_tree(source, language), False)]

    while pending:
        node, in_constant = pending.pop()
        in_constant = in_constant or node.type in NAMED_TYPES or is_constant_declarator(node)
        literal = literal_of(node, in_constant)

        if literal:
            found.append(literal)

        pending += [(child, in_constant) for child in node.children]

    return found
