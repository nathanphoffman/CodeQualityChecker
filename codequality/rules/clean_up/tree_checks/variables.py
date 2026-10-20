from ....source_code import RUST
from ....language_parsers.tree_sitter.syntax_shapes import FUNCTION_TYPES
from ....language_parsers.tree_sitter.tree_walk import walk
from ..limits import PRIVATE_PREFIX
from .names import name_counts

def declared_variable(node, language):
    """The name node of `let x = ...` (Rust) or `const x = ...` (TypeScript), or None for other nodes."""

    if language == RUST and node.type == "let_declaration" and node.child_by_field_name("value") is not None:
        name = node.child_by_field_name("pattern")
    elif language != RUST and node.type == "variable_declarator" and node.child_by_field_name("value") is not None:
        name = node.child_by_field_name("name")
    else:
        return None

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
