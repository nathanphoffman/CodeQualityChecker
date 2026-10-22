from ....source_code import C_LANG, GO, HARE, RUST, TYPESCRIPT
from ....language_parsers.tree_sitter.syntax_shapes import FUNCTION_TYPES
from ....language_parsers.tree_sitter.tree_walk import declarator_name, walk
from ..shared.limits import PRIVATE_PREFIX
from .names import name_counts

def with_value(node, field):
    """The name field of a declaration that gives the variable a value, or None when it is left empty."""

    return node.child_by_field_name(field) if node.child_by_field_name("value") is not None else None

def first_named(node):
    return node.named_children[0] if node.named_children else None

# Each language: the declaration node types that create a variable -> how to find the name node.
# Hare and Go's `a, b := ...` only follow the first name; C looks inside wrappers like `*name`.
VARIABLE_FINDERS = {
    RUST: {"let_declaration": lambda node: with_value(node, "pattern")},
    TYPESCRIPT: {"variable_declarator": lambda node: with_value(node, "name")},
    HARE: {"let_declaration": first_named},
    C_LANG: {"init_declarator": lambda node: declarator_name(node.child_by_field_name("declarator"))},
    GO: {"short_var_declaration": lambda node: first_named(node.child_by_field_name("left")),
         "var_spec": lambda node: with_value(node, "name")},
}

def declared_variable(node, language):
    """The name node of `let x = ...` (Rust and Hare), `const x = ...` (TypeScript), `int x = ...` (C) or `x := ...` (Go), or None for other nodes."""
    finder = VARIABLE_FINDERS[language].get(node.type)
    name = finder(node) if finder else None

    return name if name is not None and name.type == "identifier" else None

def tree_variables(root, language):
    """(declared variables, line numbers of the ones never mentioned again in their function)."""
    total, unused = 0, []

    for function in [node for node in walk(root) if node.type in FUNCTION_TYPES[language]]:
        counts = name_counts(function)

        for node in walk(function):
            name = declared_variable(node, language)

            if name is None or name.text.decode().startswith(PRIVATE_PREFIX):
                continue

            total += 1
            unused += [name.start_point.row + 1] if counts[name.text.decode()] <= 1 else []

    return total, unused
