from .parse_tree import parse_tree
from .syntax_shapes import BINDING_FIELDS, BODY_FIELD, BRANCH_OPERATORS, BRANCH_TYPES, FUNCTION_TYPES, NAME_FIELD, OPERATOR_FIELD
from .tree_walk import bound_node, declarator_name, identifiers_in, walk

def function_name(function):
    name = function.child_by_field_name(NAME_FIELD) or declarator_name(function.child_by_field_name("declarator"))

    if name is None and function.parent.type == "variable_declarator":
        name = function.parent.child_by_field_name(NAME_FIELD)

    return name.text.decode() if name else "anonymous"

def local_names(function, language):
    """Parameters plus everything declared inside the function."""
    names = set()

    for node in walk(function):
        field = BINDING_FIELDS[language].get(node.type)
        bound = bound_node(node, field) if field else None
        names |= identifiers_in(bound, language) if bound else set()

    return names

def branch_count(function, language):
    count = 0

    for node in walk(function):
        operator = node.child_by_field_name(OPERATOR_FIELD)
        count += node.type in BRANCH_TYPES[language]
        count += node.type == "binary_expression" and operator.text.decode() in BRANCH_OPERATORS

    return count

def statements_of(body):
    """The statements in a block. Go wraps them in a statement_list node, which is looked through."""
    statements = []

    for child in body.named_children:
        statements += child.named_children if child.type == "statement_list" else [child]

    return [statement for statement in statements if "comment" not in statement.type]

def tree_bodies(source, language):
    """(name, line_number, statement_variables, branch_count, last_line, has_docstring) for every function with a block body."""
    bodies = []

    for function in walk(parse_tree(source, language)):
        body = function.child_by_field_name(BODY_FIELD)

        if function.type not in FUNCTION_TYPES[language] or body is None or not body.type.endswith(("block", "_block", "compound_statement")):
            continue

        locals_ = local_names(function, language)
        used = [identifiers_in(statement, language) & locals_ for statement in statements_of(body)]

        bodies.append((function_name(function), function.start_point.row + 1, used, branch_count(function, language),
                       function.end_point.row + 1, False))

    return bodies
