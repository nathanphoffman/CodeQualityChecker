from .syntax_shapes import IDENTIFIER_TYPES


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
