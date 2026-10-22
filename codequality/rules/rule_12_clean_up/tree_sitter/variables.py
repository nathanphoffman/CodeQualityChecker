from ....source_code import C_LANG, CSHARP, FORTRAN, GO, HARE, MOJO, REXX, RUST, TYPESCRIPT
from ....language_parsers.tree_sitter.syntax_shapes import BODY_FIELD, FUNCTION_TYPES, LEFT_FIELD, NAME_FIELD
from ....language_parsers.tree_sitter.tree_walk import declarator_name, normalized, walk
from ..shared.limits import PRIVATE_PREFIX
from .names import name_counts

def with_value(node, field):
    """The name field of a declaration that gives the variable a value, or nothing when it is left empty."""
    name = node.child_by_field_name(field) if node.child_by_field_name("value") is not None else None

    return [name] if name is not None else []

def first_named(node):
    return node.named_children[:1] if node is not None else []

def rexx_variable(node):
    """An assignment in a routine that has its own variables (`procedure`), unless the name is exposed to the caller. Without `procedure`
    every variable is shared by the whole program, so one that nothing in the routine reads may be read somewhere else."""

    routine = node

    while routine is not None and routine.type != "routine_definition":
        routine = routine.parent

    procedures = [] if routine is None else [statement for statement in routine.child_by_field_name(BODY_FIELD).children if statement.type == "procedure_statement"]
    left = node.child_by_field_name(LEFT_FIELD)
    name = left.child_by_field_name("declarator") or left  # a compound name like `stem.i` is judged by its stem

    # every name any `procedure expose` in this routine shares with its caller
    exposed = {shared.text for procedure in procedures for shared in procedure.children_by_field_name("exposed")}

    return [name] if procedures and name.text not in exposed else []

# Each language: the declaration node types that create variables -> how to find their name nodes.
# Hare and Go's `a, b := ...` only follow the first name; C and Fortran look inside wrappers like `*name` and `name(10)`.
# Mojo has no keyword on a first assignment (`x = 1`), so every assignment to a plain name counts.
VARIABLE_FINDERS = {
    RUST: {"let_declaration": lambda node: with_value(node, "pattern")},
    TYPESCRIPT: {"variable_declarator": lambda node: with_value(node, "name")},
    HARE: {"let_declaration": first_named},
    C_LANG: {"init_declarator": lambda node: [declarator_name(node.child_by_field_name("declarator"))]},
    GO: {"short_var_declaration": lambda node: first_named(node.child_by_field_name(LEFT_FIELD)),
         "var_spec": lambda node: with_value(node, "name")},
    MOJO: {"assignment": lambda node: first_named(node.child_by_field_name(LEFT_FIELD))},
    CSHARP: {"variable_declarator": lambda node: [node.child_by_field_name(NAME_FIELD)] if len(node.named_children) > 1 else []},  # only with a value
    REXX: {"assignment_statement": rexx_variable},
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
