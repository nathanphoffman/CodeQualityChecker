from .syntax_shapes import FIRST_CHILD, IDENTIFIER_TYPES

NAME_TYPES = {"identifier", "property_identifier", "field_identifier", "shorthand_property_identifier"}

def walk(node):
    """Every node under (and including) this one."""
    pending = [node]

    while pending:
        current = pending.pop()
        yield current
        pending.extend(current.children)

def identifiers_in(node, language):
    """The variable names used anywhere inside this node."""

    return {descendant.text.decode() for descendant in walk(node) if descendant.type in IDENTIFIER_TYPES[language]}

def bound_node(node, field):
    """The part of a declaration that holds the new names, or None when it has none."""

    if field == FIRST_CHILD:
        return node.named_children[0] if node.named_children else None

    return node.child_by_field_name(field)

DECLARED_NAME_TYPES = {"identifier", "type_identifier", "field_identifier"}

def declarator_name(node):
    """The name at the bottom of a C declarator like `*name`, `name[8]` or `name(int a)`. Go names are already at the bottom."""

    while node is not None and node.type not in DECLARED_NAME_TYPES:
        node = node.child_by_field_name("declarator")

    return node

def squashed(text):
    """Source text with all whitespace removed, so `verify = False` and `verify=False` compare equal."""

    return "".join(text.split())

def names_in(node):
    """Lower-case variable, field and property names used anywhere inside this node."""

    return frozenset(descendant.text.decode().lower() for descendant in walk(node) if descendant.type in NAME_TYPES)
