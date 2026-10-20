from ...language_parsers.deor.declarations import declaration_of, declared_variables
from ...language_parsers.deor.tree import parse_deor, walk_statements
from ...language_parsers.deor.words import identifiers

FIELD_PARENTS = {"struct"}
VARIANT_PARENTS = {"enum"}

def member_name(statement):
    """The field of a struct (`string name`) or the variant of an enum (`Blue`), or None for any other statement."""
    parent = statement.parent.keyword if statement.parent else ""
    words = statement.text.split()

    if parent in FIELD_PARENTS and len(words) >= 2:
        return words[-1]

    return words[0] if parent in VARIANT_PARENTS and words else None

def deor_names(source):
    """Every name a Deor file declares: functions, macros, parameters, types, fields, variants and variables."""
    names = []

    for statement in walk_statements(parse_deor(source).roots):
        declaration = declaration_of(statement)
        names += [declaration.name] + declaration.parameter_names if declaration else []
        names += declared_variables(statement)
        member = member_name(statement)
        names += [member] if member else []

    return [name for name in names if name != "_" and identifiers(name)]
