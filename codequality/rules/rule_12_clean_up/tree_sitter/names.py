from collections import Counter

from ....language_parsers.tree_sitter.syntax_shapes import IDENTIFIER, NAME_FIELD
from ....language_parsers.tree_sitter.tree_walk import normalized, walk

NAME_NODE_TYPES = {IDENTIFIER, "type_identifier", "field_identifier", "property_identifier",
                   "shorthand_property_identifier", "shorthand_field_identifier", "package_identifier", NAME_FIELD}

IMPORT_TYPES = {"import_statement", "use_declaration", "use_statement", "import_spec", "import_from_statement", "using_directive"}
END_STATEMENT_PREFIX = "end_"  # Fortran repeats a name on its closing line (`end function area`), which is not a use

def is_counted(node):
    return node.type in NAME_NODE_TYPES and not (node.type == "name" and node.parent.type.startswith(END_STATEMENT_PREFIX))

def name_counts(node, language=None):
    """How many times each name is written inside this node."""

    return Counter(normalized(descendant.text.decode(), language) for descendant in walk(node) if is_counted(descendant))

def counts_outside_imports(root, language=None):
    """Name counts for the whole file, not counting the import lines themselves."""
    counts = name_counts(root, language)

    for node in walk(root):
        if node.type in IMPORT_TYPES:
            counts.subtract(name_counts(node, language))

    return counts
