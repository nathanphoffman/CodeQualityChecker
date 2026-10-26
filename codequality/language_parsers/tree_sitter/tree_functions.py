import re

from .parse_tree import parse_tree
from ...source_code import FORTRAN
from .syntax_shapes import (BINDING_FIELDS, BODY_FIELD, BOOLEAN_TYPED_LANGUAGES, BRANCH_OPERATORS, BRANCH_TYPES, FUNCTION_TYPES, IF_STATEMENT,
                            NAME_FIELD, NESTING_TYPES, OPERATOR_FIELD, PARAMETERS)
from .tree_walk import bound_nodes, declarator_name, identifiers_in, normalized, walk

# Fortran has no block around a body: the statements sit directly inside the function, between its header and its end line,
# mixed with declarations. These are the parts that are not statements of the body.
FRAME_TYPES = {"function_statement", "subroutine_statement", "program_statement", "variable_declaration", "use_statement",
               "implicit_statement", "do_statement", "internal_procedures", "contains_statement",
               "procedure_statement"}  # the last is Rexx's `procedure expose ...`, which only sets up the routine

HEADER_TYPES = {"function_statement", "subroutine_statement", "program_statement"}
BLOCK_ENDINGS = ("block", "_block", "compound_statement")

RECEIVERS = {"self", "&self", "&mut self", "mut self", "this"}

# Clever on purpose: a parameter is a boolean when it names the type `bool`, `boolean` or `Bool` on its own (not inside `Vec<bool>` or
# `boolean[]`), or when it defaults to true or false.
BOOLEAN_PARAMETER = re.compile(r"(?<![<\[\w])(?:bool|boolean|Bool)\b(?![\[<])|=\s*(?:true|false|True|False)\b")

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

def is_else_if(node):
    """An `if` that is the else branch of another `if` is one more path, not one more level."""
    parent = node.parent

    return parent is not None and (parent.type.endswith("else_clause") or parent.type == "else_statement"
                                   or (parent.type == IF_STATEMENT and parent.child_by_field_name("alternative") == node))

def max_nesting(function, language):
    """How many blocks sit inside one another at the deepest point. Functions inside this one are measured on their own."""
    deepest, pending = 0, [(function, 0)]

    while pending:
        node, depth = pending.pop()
        deepest = max(deepest, depth)

        for child in node.named_children:
            if child.type not in FUNCTION_TYPES[language]:
                pending.append((child, depth + (child.type in NESTING_TYPES[language] and not is_else_if(child))))

    return deepest

def parameter_nodes(function):
    """The parameters in the function's header. C wraps its parameter list in the declarator."""
    node = function

    while node is not None and node.child_by_field_name(PARAMETERS) is None:
        node = node.child_by_field_name("declarator")

    parameters = node.child_by_field_name(PARAMETERS).named_children if node is not None else []

    return [parameter for parameter in parameters if "comment" not in parameter.type and parameter.text.decode().strip() not in RECEIVERS]

def boolean_parameters(parameters, language):
    """How many parameters are booleans. An object or array pattern (React props) is one parameter, whatever is inside."""

    if language not in BOOLEAN_TYPED_LANGUAGES:
        return 0

    texts = [parameter.text.decode() for parameter in parameters]

    return len([text for text in texts if not text.startswith(("{", "[")) and BOOLEAN_PARAMETER.search(text)])

def tree_bodies(source, language):
    """(name, line_number, statement_variables, branch_count, last_line, has_docstring, max_nesting, boolean_parameters, parameter_count)
    for every function with a block body."""
    bodies = []

    for function in walk(parse_tree(source, language)):
        body = function_body(function, language) if function.type in FUNCTION_TYPES[language] else None

        if body is None:
            continue

        locals_ = local_names(function, language)
        used = [identifiers_in(statement, language) & locals_ for statement in statements_of(body)]

        parameters = parameter_nodes(function)

        bodies.append((function_name(function), function.start_point.row + 1, used, branch_count(function, language), function.end_point.row + 1,
                       False, max_nesting(function, language), boolean_parameters(parameters, language), len(parameters)))

    return bodies
