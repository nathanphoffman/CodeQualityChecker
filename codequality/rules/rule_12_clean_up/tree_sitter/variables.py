from ....source_code import C_LANG, CSHARP, FORTRAN, GO, HARE, MOJO, RUST, TYPESCRIPT
from ....language_parsers.tree_sitter.syntax_shapes import FUNCTION_TYPES
from ....language_parsers.tree_sitter.tree_walk import declarator_name, normalized, walk
from ..shared.limits import PRIVATE_PREFIX
from .names import name_counts

def with_value(node, field):
    """The name field of a declaration that gives the variable a value, or nothing when it is left empty."""
    name = node.child_by_field_name(field) if node.child_by_field_name("value") is not None else None

    return [name] if name is not None else []

def first_named(node):
    return node.named_children[:1] if node is not None else []

# Each language: the declaration node types that create variables -> how to find their name nodes.
# Hare and Go's `a, b := ...` only follow the first name; C and Fortran look inside wrappers like `*name` and `name(10)`.
# Mojo has no keyword on a first assignment (`x = 1`), so every assignment to a plain name counts.
VARIABLE_FINDERS = {
    RUST: {"let_declaration": lambda node: with_value(node, "pattern")},
    TYPESCRIPT: {"variable_declarator": lambda node: with_value(node, "name")},
    HARE: {"let_declaration": first_named},
    C_LANG: {"init_declarator": lambda node: [declarator_name(node.child_by_field_name("declarator"))]},
    GO: {"short_var_declaration": lambda node: first_named(node.child_by_field_name("left")),
         "var_spec": lambda node: with_value(node, "name")},
    MOJO: {"assignment": lambda node: first_named(node.child_by_field_name("left"))},
    CSHARP: {"variable_declarator": lambda node: [node.child_by_field_name("name")] if len(node.named_children) > 1 else []},  # only with a value
    FORTRAN: {"variable_declaration": lambda node: [declarator_name(declarator) for declarator in node.children_by_field_name("declarator")]},
}

def declared_variables(node, language):
    """The name nodes of `let x = ...` (Rust and Hare), `const x = ...` (TypeScript), `int x = ...` (C), `x := ...` (Go),
    `x = ...` (Mojo), `integer :: x` (Fortran) or `var x = ...` (C#). Empty for other nodes."""
    finder = VARIABLE_FINDERS[language].get(node.type)
    names = finder(node) if finder else []

    return [name for name in names if name is not None and name.type == "identifier"]

def tree_variables(root, language):
    """(declared variables, line numbers of the ones never mentioned again in their function)."""
    total, unused = 0, []

    for function in [node for node in walk(root) if node.type in FUNCTION_TYPES[language]]:
        counts = name_counts(function, language)

        for node in walk(function):
            for name in declared_variables(node, language):
                text = normalized(name.text.decode(), language)

                if text.startswith(PRIVATE_PREFIX):
                    continue

                total += 1
                unused += [name.start_point.row + 1] if counts[text] <= 1 else []

    return total, unused
