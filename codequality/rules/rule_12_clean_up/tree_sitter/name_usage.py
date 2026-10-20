from ....source_code import RUST
from ....language_parsers.tree_sitter.tree_walk import walk
from ...rule_10_test_what_matters.count_tests import has_test_attribute
from ..shared.Cleanup_Findings import Name_Usage
from ..shared.limits import RUST_ENTRY_POINT
from .names import name_counts

def is_private_definition(node, language):
    """A Rust fn without `pub` (not main, not a test, not in a trait impl), or a TypeScript function that is not exported
    or a method marked `private`."""

    if language == RUST:
        in_trait_impl = node.parent.parent is not None and node.parent.parent.child_by_field_name("trait") is not None
        has_pub = any(child.type == "visibility_modifier" for child in node.children)
        name = node.child_by_field_name("name")

        return node.type == "function_item" and not has_pub and not in_trait_impl and not has_test_attribute(node) and name.text.decode() != RUST_ENTRY_POINT

    if node.type == "function_declaration":
        return node.parent.type == "program"

    return node.type == "method_definition" and any(child.type == "accessibility_modifier" and child.text == b"private" for child in node.children)

def tree_name_usage(root, language):
    private = [(node.child_by_field_name("name").text.decode(), node.start_point.row + 1)
               for node in walk(root) if node.parent is not None and is_private_definition(node, language)]

    return Name_Usage(private, name_counts(root))
