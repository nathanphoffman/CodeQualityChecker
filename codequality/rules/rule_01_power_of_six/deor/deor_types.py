from ....language_parsers.deor.declarations import declarations_in
from ....language_parsers.deor.tree import parse_deor
from ..tree_sitter.type_members.Type_Info import Type_Info

MEMBER_TYPES = ("struct", "enum")  # each indented line under one is a field or a variant

def deor_types(source):
    """A Type_Info for every struct and enum. Deor types have no methods."""

    return [Type_Info(declaration.name, declaration.statement.first_line, len(declaration.statement.children), 0)
            for declaration in declarations_in(parse_deor(source).roots, MEMBER_TYPES)]
