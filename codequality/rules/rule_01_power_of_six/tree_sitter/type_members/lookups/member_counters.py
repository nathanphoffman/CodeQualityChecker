from ......language_parsers.tree_sitter.syntax_shapes import NAME_FIELD
from ......language_parsers.tree_sitter.tree_walk import walk

CONSTRUCTORS = {"constructor", "__init__"}  # a constructor is not counted as one of the type's methods

def one(node):
    return 1

def declarators(node):
    """`int a, b;` declares two members in one node."""

    return max(1, len(node.children_by_field_name("declarator")))

def names_listed(node):
    """Go's `x, y int` declares two fields in one node."""

    return max(1, len(node.children_by_field_name(NAME_FIELD)))

def variable_declarators(node):
    return max(1, sum(part.type == "variable_declarator" for part in walk(node)))

def unless_constructor(node):
    name = node.child_by_field_name(NAME_FIELD)

    return 0 if name is not None and name.text.decode() in CONSTRUCTORS else 1

def procedures(node):
    return sum(child.type == "procedure_statement" for child in node.named_children)
