from ....language_parsers.deor.declarations import FUNCTION_KINDS, declarations_in, used_names, variables_in
from ....language_parsers.deor.tree import parse_deor, walk_statements

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

def max_nesting(function):
    """How many `if` and `for` statements sit inside one another at the deepest point. An `else if` is not one more level."""
    deepest, pending = 0, [(function, 0)]

    while pending:
        statement, depth = pending.pop()
        deepest = max(deepest, depth)

        for child in statement.children:
            pending.append((child, depth + (child.keyword in BRANCH_STATEMENTS and not child.text.startswith("else if"))))

    return deepest

def deor_bodies(source):
    """(name, line_number, statement_variables, branch_count, last_line, has_docstring, max_nesting) for every function and macro."""
    bodies = []

    for declaration in declarations_in(parse_deor(source).roots, FUNCTION_KINDS):
        function = declaration.statement
        local_names = set(declaration.parameter_names) | set(variables_in(function))
        used = [set(used_names(child)) & local_names for child in function.children]

        bodies.append((declaration.label, function.first_line, used, branch_count(function), function.end_line, False, max_nesting(function)))

    return bodies
