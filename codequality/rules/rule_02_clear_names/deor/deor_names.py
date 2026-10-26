from ....language_parsers.deor.declarations import FUNCTION_KINDS, declaration_of, declared_variables
from ....language_parsers.deor.tree import parse_deor, walk_statements
from ....language_parsers.deor.words import identifiers
from ..shared.name_styles import FUNCTION, VARIABLE, VARIANT, TYPE

FIELD_PARENTS = {"struct"}
VARIANT_PARENTS = {"enum"}

def member_name(statement):
    """The field of a struct (`string name`) or the variant of an enum (`Blue`), or None for any other statement."""
    parent = statement.parent.keyword if statement.parent else ""
    words = statement.text.split()

    if parent in FIELD_PARENTS and len(words) >= 2:
        return words[-1]

    return words[0] if parent in VARIANT_PARENTS and words else None

def deor_kinded_names(source):
    """(name, kind) for every name a Deor file declares: functions, macros, parameters, types, fields, variants and variables."""
    names = []

    for statement in walk_statements(parse_deor(source).roots):
        declaration = declaration_of(statement)

        if declaration:
            kind = FUNCTION if declaration.kind in FUNCTION_KINDS else TYPE
            names += [(declaration.name, kind)] + [(parameter, VARIABLE) for parameter in declaration.parameter_names]

        names += [(variable, VARIABLE) for variable in declared_variables(statement)]
        member = member_name(statement)

        if member:
            is_variant = statement.parent.keyword in VARIANT_PARENTS  # a variant like `Blue` is an enum member, a field is a variable
            names.append((member, VARIANT if is_variant else VARIABLE))

    return [(name, kind) for name, kind in names if name != "_" and identifiers(name)]
