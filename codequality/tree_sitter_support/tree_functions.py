from .parse_tree import parse_tree
from .syntax_shapes import BINDING_FIELDS, BRANCH_OPERATORS, BRANCH_TYPES, FUNCTION_TYPES
from .tree_walk import identifiers_in, walk


def function_name(function):
    name = function.child_by_field_name("name")
    if name is None and function.parent.type == "variable_declarator":
        name = function.parent.child_by_field_name("name")
    return name.text.decode() if name else "anonymous"


def local_names(function, language):
    """Parameters plus everything declared inside the function."""
    names = set()
    for node in walk(function):
        field = BINDING_FIELDS[language].get(node.type)
        bound = node.child_by_field_name(field) if field else None
        names |= identifiers_in(bound, language) if bound else set()
    return names


def branch_count(function, language):
    count = 0
    for node in walk(function):
        operator = node.child_by_field_name("operator")
        count += node.type in BRANCH_TYPES[language]
        count += node.type == "binary_expression" and operator.text.decode() in BRANCH_OPERATORS
    return count


def statements_of(body):
    return [child for child in body.named_children if "comment" not in child.type]


def tree_bodies(source, language):
    """(name, line_number, statement_variables, branch_count) for every function with a block body."""
    bodies = []
    for function in walk(parse_tree(source, language)):
        body = function.child_by_field_name("body")
        if function.type not in FUNCTION_TYPES[language] or body is None or not body.type.endswith(("block", "_block")):
            continue
        locals_ = local_names(function, language)
        used = [identifiers_in(statement, language) & locals_ for statement in statements_of(body)]
        bodies.append((function_name(function), function.start_point.row + 1, used, branch_count(function, language)))
    return bodies
