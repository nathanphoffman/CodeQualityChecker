from ....tree_sitter_support.parse_tree import parse_tree
from ....tree_sitter_support.tree_walk import names_in, squashed, walk
from ....tree_sitter_support.use_names import use_name
from .Code_Use import Code_Use
from .tree_strings import string_use


def named_use(node, name, lines):
    row = node.start_point.row
    return Code_Use(name, row + 1, squashed(node.text.decode()), names_in(node), lines[row].lower())


def tree_uses(source, language):
    lines = source.splitlines()
    uses = []

    for node in walk(parse_tree(source, language)):
        name = use_name(node)
        if name:
            uses.append(named_use(node, name, lines))
        built = string_use(node, frozenset(), lines)

        if built:
            uses.append(built)

    return uses
