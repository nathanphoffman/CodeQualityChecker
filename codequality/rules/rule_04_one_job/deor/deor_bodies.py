from ....language_parsers.deor.declarations import FUNCTION_KINDS, declarations_in, used_names, variables_in
from ....language_parsers.deor.tree import parse_deor, walk_statements
from ....language_parsers.deor.words import identifiers

BRANCH_STATEMENTS = {"if", "for"}
BRANCH_WORDS = {"and", "or"}

def is_branch(statement):
    """An `if`, an `else if` or a `for` adds a path through the function."""

    return statement.keyword in BRANCH_STATEMENTS or statement.text.startswith("else if")

def branch_count(function):
    count = 0

    for statement in walk_statements([function]):
        count += is_branch(statement)
        count += sum(word in BRANCH_WORDS for word in statement.text.split())

    return count

def deor_bodies(source):
    """(name, line_number, statement_variables, branch_count, last_line, has_docstring) for every function and macro."""
    bodies = []

    for declaration in declarations_in(parse_deor(source).roots, FUNCTION_KINDS):
        function = declaration.statement
        local_names = set(declaration.parameter_names) | set(variables_in(function))
        used = [set(used_names(child)) & local_names for child in function.children]

        bodies.append((declaration.label, function.first_line, used, branch_count(function), function.end_line, False))

    return bodies
