from .parse_tree import parse_tree
from ...source_code import FORTRAN
from .syntax_shapes import BINDING_FIELDS, BODY_FIELD, BRANCH_OPERATORS, BRANCH_TYPES, FUNCTION_TYPES, NAME_FIELD, OPERATOR_FIELD
from .tree_walk import bound_nodes, declarator_name, identifiers_in, normalized, walk

# Fortran has no block around a body: the statements sit directly inside the function, between its header and its end line,
# mixed with declarations. These are the parts that are not statements of the body.
FRAME_TYPES = {"function_statement", "subroutine_statement", "program_statement", "variable_declaration", "use_statement",
               "implicit_statement", "do_statement", "internal_procedures", "contains_statement",
               "procedure_statement"}  # the last is Rexx's `procedure expose ...`, which only sets up the routine
HEADER_TYPES = {"function_statement", "subroutine_statement", "program_statement"}
BLOCK_ENDINGS = ("block", "_block", "compound_statement")

def fortran_name(function):
    """The name in a Fortran function, subroutine or program header."""

    for header in [child for child in function.children if child.type in HEADER_TYPES]:
        return header.child_by_field_name(NAME_FIELD) or next((child for child in header.named_children if child.type == "name"), None)

    return None

def function_body(function, language):
    """The node holding a function's statements, or None when it has no block body."""

    if language == FORTRAN:
        return function

    body = function.child_by_field_name(BODY_FIELD)

    return body if body is not None and body.type.endswith(BLOCK_ENDINGS) else None

def function_name(function):
    name = function.child_by_field_name(NAME_FIELD) or declarator_name(function.child_by_field_name("declarator")) or fortran_name(function)

    if name is None and function.parent.type == "variable_declarator":
        name = function.parent.child_by_field_name(NAME_FIELD)

    return normalized(name.text.decode(), FORTRAN if function.type in FUNCTION_TYPES[FORTRAN] else None) if name else "anonymous"

def local_names(function, language):
    """Parameters plus everything declared inside the function."""
    names = set()

    for node in walk(function):
        field = BINDING_FIELDS[language].get(node.type)

        for bound in bound_nodes(node, field) if field else []:
            names |= identifiers_in(bound, language)

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

    return [statement for statement in statements
            if "comment" not in statement.type and statement.type not in FRAME_TYPES and not statement.type.startswith("end_")]

def tree_bodies(source, language):
    """(name, line_number, statement_variables, branch_count, last_line, has_docstring) for every function with a block body."""
    bodies = []

    for function in walk(parse_tree(source, language)):
        body = function_body(function, language) if function.type in FUNCTION_TYPES[language] else None

        if body is None:
            continue

        locals_ = local_names(function, language)
        used = [identifiers_in(statement, language) & locals_ for statement in statements_of(body)]

        bodies.append((function_name(function), function.start_point.row + 1, used, branch_count(function, language),
                       function.end_point.row + 1, False))

    return bodies
