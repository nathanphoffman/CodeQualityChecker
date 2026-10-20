from dataclasses import replace

from .deor_uses import deor_calls
from ....language_parsers.deor.rust_blocks import real_line, rust_blocks
from ....source_code import DEOR, RUST
from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.tree_walk import names_in, squashed, walk
from ....language_parsers.tree_sitter.use_names import use_name
from .Code_Use import Code_Use
from .tree_strings import string_use

def named_use(node, name, lines):
    row = node.start_point.row

    return Code_Use(name, row + 1, squashed(node.text.decode()), names_in(node), lines[row].lower())

def deor_uses(source):
    """Deor calls, plus whatever the `rust` blocks do, read as Rust with their line numbers moved back to the Deor file."""
    lines = source.splitlines()
    uses = [Code_Use(name, line, text, names, lines[line - 1].lower()) for name, line, text, names in deor_calls(source)]

    for first_line, wrapped in rust_blocks(source):
        uses += [replace(use, line_number=real_line(first_line, use.line_number)) for use in tree_uses(wrapped, RUST)]

    return uses

def tree_uses(source, language):
    if language == DEOR:
        return deor_uses(source)

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
