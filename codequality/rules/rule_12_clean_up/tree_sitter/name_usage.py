from ....language_parsers.tree_sitter.syntax_shapes import BODY_FIELD
from ....language_parsers.tree_sitter.tree_functions import function_name
from ....language_parsers.tree_sitter.tree_walk import walk
from ....source_code import C_LANG, CSHARP, FORTRAN, GO, HARE, MOJO, REXX, RUST, TYPESCRIPT
from ...rule_10_test_what_matters.count_tests import has_test_attribute
from ..shared.Cleanup_Findings import Name_Usage
from ..shared.limits import CSHARP_ENTRY_POINT, CSHARP_VISIBLE_MODIFIERS, GO_RUNTIME_FUNCTIONS, PRIVATE_PREFIX, RUST_ENTRY_POINT
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

def is_private_csharp(node):
    """A method with no access modifier is private, and so is one marked `private`. Interface methods are public, and a method that
    overrides or implements something is called through the base type."""

    if node.type != "method_declaration" or node.parent.parent.type == "interface_declaration":
        return False

    modifiers = {child.text.decode() for child in node.children if child.type == "modifier"}

    return not modifiers & CSHARP_VISIBLE_MODIFIERS and function_name(node) != CSHARP_ENTRY_POINT

def is_private_mojo(node):
    """A function whose name starts with one underscore. Names with two, like `__init__`, are called by the language."""
    name = function_name(node) if node.type == "function_definition" else ""

    return name.startswith(PRIVATE_PREFIX) and not name.startswith(PRIVATE_PREFIX * 2)

def is_private_fortran(node):
    """A procedure written after `contains` inside a program or another procedure can only be called from there."""

    if node.type not in ("function", "subroutine"):
        return False

    ancestors = []
    parent = node.parent

    while parent is not None:
        ancestors.append(parent.type)
        parent = parent.parent

    return bool(set(ancestors) & {"program", "function", "subroutine"})

def is_private_rexx(node):
    """A routine that starts with `procedure` keeps its variables to itself, which is how Rexx marks a helper. Other labels can be called from other programs."""

    return node.type == "routine_definition" and any(statement.type == "procedure_statement" for statement in node.child_by_field_name(BODY_FIELD).children)

PRIVATE_CHECKS = {RUST: is_private_rust, HARE: is_private_hare, TYPESCRIPT: is_private_typescript, C_LANG: is_private_c, GO: is_private_go,
                  MOJO: is_private_mojo, FORTRAN: is_private_fortran, CSHARP: is_private_csharp, REXX: is_private_rexx}

def is_private_definition(node, language):
    """A Rust fn without `pub` (not main, not a test, not in a trait impl), a Hare fn without `export` (not main or an attribute
    like @test), a C function marked `static`, a Go function with a lower-case name, a Mojo function starting with `_`, a Fortran
    procedure inside a program or another procedure, a C# method that is not public, protected or internal, or a TypeScript function that is not exported or a method marked `private`."""

    return PRIVATE_CHECKS[language](node)

def tree_name_usage(root, language):
    private = [(function_name(node), node.start_point.row + 1)
               for node in walk(root) if node.parent is not None and is_private_definition(node, language)]

    return Name_Usage(private, name_counts(root, language))
