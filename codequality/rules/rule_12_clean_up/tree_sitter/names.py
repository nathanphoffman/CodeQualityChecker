from collections import Counter

from ....language_parsers.tree_sitter.tree_walk import walk

NAME_NODE_TYPES = {"identifier", "type_identifier", "field_identifier", "property_identifier",
                   "shorthand_property_identifier", "shorthand_field_identifier"}

IMPORT_TYPES = {"import_statement", "use_declaration", "use_statement"}

def name_counts(node):
    """How many times each name is written inside this node."""

    return Counter(descendant.text.decode() for descendant in walk(node) if descendant.type in NAME_NODE_TYPES)

def counts_outside_imports(root):
    """Name counts for the whole file, not counting the import lines themselves."""
    counts = name_counts(root)

    for node in walk(root):
        if node.type in IMPORT_TYPES:
            counts.subtract(name_counts(node))

    return counts
