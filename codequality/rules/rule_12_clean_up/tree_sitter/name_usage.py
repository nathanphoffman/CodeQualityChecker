from ....source_code import C_LANG, GO, HARE, RUST, TYPESCRIPT
from ....language_parsers.tree_sitter.tree_functions import function_name
from ....language_parsers.tree_sitter.tree_walk import walk
from ...rule_10_test_what_matters.count_tests import has_test_attribute
from ..shared.Cleanup_Findings import Name_Usage
from ..shared.limits import GO_RUNTIME_FUNCTIONS, RUST_ENTRY_POINT
from .names import name_counts

def is_private_rust(node):
    in_trait_impl = node.parent.parent is not None and node.parent.parent.child_by_field_name("trait") is not None
    has_pub = any(child.type == "visibility_modifier" for child in node.children)

    return node.type == "function_item" and not has_pub and not in_trait_impl and not has_test_attribute(node) and function_name(node) != RUST_ENTRY_POINT

def is_private_hare(node):
    is_exported = node.prev_sibling is not None and node.prev_sibling.type == "export"
    is_special = any(child.type == "function_attribute" for child in node.children)  # @test, @init and @fini are called by the runtime

    return node.type == "function_declaration" and not is_exported and not is_special and function_name(node) != RUST_ENTRY_POINT

def is_private_typescript(node):
    if node.type == "function_declaration":
        return node.parent.type == "program"

    return node.type == "method_definition" and any(child.type == "accessibility_modifier" and child.text == b"private" for child in node.children)

def is_private_c(node):
    """A function marked `static` is private to its file."""

    return node.type == "function_definition" and any(child.type == "storage_class_specifier" and child.text == b"static" for child in node.children)

def is_private_go(node):
    """Go makes a name private by starting it with a lower-case letter. main, init and tests are called from outside."""
    if node.type not in ("function_declaration", "method_declaration"):
        return False

    name = function_name(node)

    return name[0].islower() and name not in GO_RUNTIME_FUNCTIONS

PRIVATE_CHECKS = {RUST: is_private_rust, HARE: is_private_hare, TYPESCRIPT: is_private_typescript, C_LANG: is_private_c, GO: is_private_go}

def is_private_definition(node, language):
    """A Rust fn without `pub` (not main, not a test, not in a trait impl), a Hare fn without `export` (not main or an attribute
    like @test), a C function marked `static`, a Go function with a lower-case name, or a TypeScript function that is not exported
    or a method marked `private`."""

    return PRIVATE_CHECKS[language](node)

def tree_name_usage(root, language):
    private = [(function_name(node), node.start_point.row + 1)
               for node in walk(root) if node.parent is not None and is_private_definition(node, language)]

    return Name_Usage(private, name_counts(root))
