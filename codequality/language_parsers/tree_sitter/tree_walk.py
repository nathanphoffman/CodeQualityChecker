from .syntax_shapes import CASE_INSENSITIVE_LANGUAGES, FIRST_CHILD, IDENTIFIER_TYPES, WHOLE_NODE

NAME_TYPES = {"identifier", "property_identifier", "field_identifier", "shorthand_property_identifier"}

def walk(node):
    """Every named node under (and including) this one. Tokens like the `function` keyword are skipped: Fortran names its
    function nodes `function` and `subroutine` too, so the keywords would be mistaken for the real thing."""
    pending = [node]

    while pending:
        current = pending.pop()

        if current.is_named:
            yield current

        pending.extend(current.children)

def normalized(text, language):
    """A name as the language sees it: lower-cased where case does not matter."""

    return text.lower() if language in CASE_INSENSITIVE_LANGUAGES else text

def identifiers_in(node, language):
    """The variable names used anywhere inside this node."""

    return {normalized(descendant.text.decode(), language) for descendant in walk(node) if descendant.type in IDENTIFIER_TYPES[language]}

def bound_nodes(node, field):
    """The parts of a declaration that hold the new names. A field can repeat (`int a, b;`), so there may be several."""

    if field == WHOLE_NODE:
        return [node]

    if field == FIRST_CHILD:
        return node.named_children[:1]

    return node.children_by_field_name(field)

DECLARED_NAME_TYPES = {"identifier", "type_identifier", "field_identifier", "name"}

def inner_declarator(node):
    """What a wrapper like C's `*name`, `name[8]`, Fortran's `name = 5` or `name(10)` wraps."""
    inner = node.child_by_field_name("declarator") or node.child_by_field_name("left")

    return inner or (node.named_children[0] if node.type == "sized_declarator" and node.named_children else None)

def declarator_name(node):
    """The name at the bottom of a declarator. Go names are already at the bottom."""

    while node is not None and node.type not in DECLARED_NAME_TYPES:
        node = inner_declarator(node)

    return node

def squashed(text):
    """Source text with all whitespace removed, so `verify = False` and `verify=False` compare equal."""

    return "".join(text.split())

def names_in(node):
    """Lower-case variable, field and property names used anywhere inside this node."""

    return frozenset(descendant.text.decode().lower() for descendant in walk(node) if descendant.type in NAME_TYPES)
