import re
from collections import Counter

from ....language_parsers.deor.declarations import FUNCTION_KINDS, declarations_in, declared_variables, used_names
from ....language_parsers.deor.tree import parse_deor, walk_statements

PRIVATE_PREFIX = "_"
TERMINATORS = {"return", "break", "continue"}
# a line like `macro_run name` or `unsafe_macro_run name`, capturing the name
MACRO_CALL = re.compile(r"^(?:unsafe_)?macro_run\s+(?P<name>\w+)$")

def own_statements(function):
    """The statements of a function or macro, leaving out macros declared inside it: those are checked on their own."""
    statements, pending = [], list(function.children)

    while pending:
        statement = pending.pop(0)

        if statement.keyword in FUNCTION_KINDS:
            continue

        statements.append(statement)
        pending += statement.children

    return statements

def name_counts(function, macros):
    """How often each name is written in the function, counting the macros it runs. None when it runs a macro from another file."""
    counts = Counter(used_names(function))

    for statement in walk_statements([function]):
        call = MACRO_CALL.match(statement.text)

        if call and call.group("name") not in macros:
            return None

        counts += Counter(used_names(macros[call.group("name")])) if call else Counter()

    return counts

def unused_variables_of(function, macros):
    """(variables declared, line numbers of the ones nothing reads) in one function or macro."""
    counts = name_counts(function, macros)
    # two loops: every variable declared by every statement that isn't a `for`, skipping private names
    declared = [(name, statement.first_line) for statement in own_statements(function) if statement.keyword != "for"
                for name in declared_variables(statement) if not name.startswith(PRIVATE_PREFIX)]

    if counts is None:
        return 0, []

    return len(declared), [line for name, line in declared if counts[name] <= 1]

def unreachable_in(statements):
    """Lines of the statements after a return, break or continue in the same list."""
    ends = [index for index, statement in enumerate(statements) if statement.keyword in TERMINATORS]

    return [statement.first_line for statement in statements[ends[0] + 1:]] if ends else []

def deor_cleanup(source):
    """(variables_total, unused variable lines, statements_total, unreachable lines) for one Deor file.

    Imports are global in Deor and there are no private functions, so those parts of the clean up rule have nothing to find."""
    parsed = parse_deor(source)
    declarations = declarations_in(parsed.roots, FUNCTION_KINDS)
    macros = {item.name: item.statement for item in declarations if item.kind != "fn"}
    totals = {"variables": 0, "statements": 0}
    unused, unreachable = [], []

    for declaration in declarations:
        total, lines = unused_variables_of(declaration.statement, macros)
        totals["variables"] += total
        unused += lines
        unreachable += unreachable_in(declaration.statement.children)
        totals["statements"] += len(own_statements(declaration.statement))

        for statement in own_statements(declaration.statement):
            unreachable += unreachable_in(statement.children)

    return totals["variables"], sorted(unused), totals["statements"], sorted(unreachable)
