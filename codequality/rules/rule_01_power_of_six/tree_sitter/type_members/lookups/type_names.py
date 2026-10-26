from ......language_parsers.tree_sitter.syntax_shapes import NAME_FIELD
from ......language_parsers.tree_sitter.tree_walk import walk

# Each of these takes a type's syntax node and returns the node holding its name, or None.

def named(node):
    return node.child_by_field_name(NAME_FIELD)

def own_type_name(node):
    """Rust's `impl Name { ... }` holds the name in its `type` field."""

    return node.child_by_field_name("type")

def type_declaration_name(node):
    """Hare names a struct or enum on the `type name = ...` declaration around it."""
    ancestor = node.parent

    while ancestor is not None and ancestor.type != "type_declaration":
        ancestor = ancestor.parent

    return ancestor.named_children[0] if ancestor is not None else None

def fortran_type_name(node):
    return next((part.named_children[0] for part in node.named_children if part.type == "derived_type_statement"), None)

def go_receiver_name(node):
    """The type a Go method belongs to: `func (a *Name) Method()`."""
    receiver = node.child_by_field_name("receiver")

    return next((part for part in walk(receiver) if part.type == "type_identifier"), None) if receiver is not None else None
