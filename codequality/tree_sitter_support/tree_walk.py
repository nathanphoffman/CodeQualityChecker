from .syntax_shapes import IDENTIFIER_TYPES

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


def squashed(text):
    """Source text with all whitespace removed, so `verify = False` and `verify=False` compare equal."""
    return "".join(text.split())


def names_in(node):
    """Lower-case variable, field and property names used anywhere inside this node."""
    return frozenset(descendant.text.decode().lower() for descendant in walk(node) if descendant.type in NAME_TYPES)
