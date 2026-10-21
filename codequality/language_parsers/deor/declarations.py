import re
from typing import NamedTuple

from .tree import walk_statements
from .words import CONTROL_KEYWORDS, KEYWORDS, identifiers, split_top_level

FUNCTION_KINDS = ("fn", "macro", "unsafe_macro")
MACRO_PREFIX = "macro "  # a macro is shown as "macro name" so it is not mistaken for a function

# Clever on purpose: the header lines of the declarations that have a name, matched against the joined text of the statement.
#   fn:    "fn", the return type, the name, then the parameters between the brackets
#   macro: "macro" or "unsafe_macro", then the name
#   type:  "type", the name, then the validator's parameter between the brackets
FUNCTION_HEADER = re.compile(r"^fn\s+\S+\s+(?P<name>\w+)\s*\((?P<parameters>.*)\)$")

# `macro name` or `unsafe_macro name`, capturing the name
MACRO_HEADER = re.compile(r"^(?:unsafe_macro|macro)\s+(?P<name>\w+)$")

# `type name(parameters)`, capturing the name and the parameters between the brackets
TYPE_HEADER = re.compile(r"^type\s+(?P<name>\w+)\s*\((?P<parameters>.*)\)$")

# `struct`, `enum` or `shape` followed by the name
NAMED_HEADER = re.compile(r"^(?:struct|enum|shape)\s+(?P<name>\w+)")

# Clever on purpose: ways a statement declares variables.
#   typed: an optional "const", a type, a name, then "=" or the end of the line (a validator type without a value)
#   as:    a name then "as"
#   group: "(a, b) in" or "move (a, b) in", which pulls fields out of a struct
#   loop:  "for name in" or "for move (name in", but not "for in range" or "for if"
TYPED_DECLARATION = re.compile(r"^(?:const\s+)?(?P<type>[A-Za-z_]\w*)\s+(?P<name>[A-Za-z_]\w*)\s*(?:=|$)")

# a name followed by `as`
AS_BINDING = re.compile(r"^(?P<name>[A-Za-z_]\w*)\s+as\b")

# `(a, b) in` or `move (a, b) in`, capturing the names between the brackets
GROUP_BINDING = re.compile(r"^(?:move\s*)?\((?P<names>[^)]*)\)\s+in\b")

# `for name in` or `for move (name in`, capturing the name
LOOP_VARIABLE = re.compile(r"^for\s+(?:move\s*\(\s*)?(?P<name>[A-Za-z_]\w*)\s+in\b")

class Declaration(NamedTuple):
    kind: str  # fn, macro, unsafe_macro, struct, enum, type, shape
    name: str
    parameter_names: list
    statement: object

    @property
    def label(self):
        return MACRO_PREFIX + self.name if self.kind != "fn" else self.name

def parameter_names_of(text):
    """The names in `Type one, Type two`: the last word of each piece."""

    return [piece.split()[-1] for piece in split_top_level(text) if piece.split()]

def declaration_of(statement):
    """A Declaration for a fn, macro, unsafe_macro, struct, enum, type or shape statement, or None."""
    kind = statement.keyword

    # := assigns the match inside the condition, so the body can use it
    if kind == "fn" and (match := FUNCTION_HEADER.match(statement.text)):
        return Declaration(kind, match.group("name"), parameter_names_of(match.group("parameters")), statement)

    # := assigns the match inside the condition, so the body can use it
    if kind in ("macro", "unsafe_macro") and (match := MACRO_HEADER.match(statement.text)):
        return Declaration(kind, match.group("name"), [], statement)

    # := assigns the match inside the condition, so the body can use it
    if kind == "type" and (match := TYPE_HEADER.match(statement.text)):
        return Declaration("type", match.group("name"), parameter_names_of(match.group("parameters")), statement)

    match = NAMED_HEADER.match(statement.text)

    return Declaration(kind, match.group("name"), [], statement) if match else None

def declarations_in(roots, kinds=None):
    """Every declaration in file order, including macros declared inside functions."""
    found = [declaration_of(statement) for statement in walk_statements(roots)]

    return [declaration for declaration in found if declaration and (kinds is None or declaration.kind in kinds)]

def declared_variables(statement):
    """The names a statement creates: `Type name = x`, `name as x`, `(a, b) in x` and `for name in x`."""
    text = statement.text

    # := assigns the match inside the condition, so the body can use it
    if match := GROUP_BINDING.match(text):
        return [name.strip() for name in match.group("names").split(",") if name.strip()]

    # := assigns the match inside the condition, so the body can use it
    if match := LOOP_VARIABLE.match(text):
        return [match.group("name")]

    if statement.keyword in CONTROL_KEYWORDS | KEYWORDS - {"const"}:
        return []

    # := assigns the match inside the condition, so the body can use it
    if match := AS_BINDING.match(text):
        return [match.group("name")]

    match = TYPED_DECLARATION.match(text)

    return [match.group("name")] if match and match.group("name") not in KEYWORDS else []

def variables_in(statement):
    """Names declared by this statement and everything indented under it."""

    # two loops: every variable declared by every statement indented under this one
    return [name for inner in walk_statements([statement]) for name in declared_variables(inner)]

def used_names(statement):
    """Every name mentioned by a statement and everything under it, `rust` blocks included, once per mention."""
    mentioned = []

    for inner in walk_statements([statement]):
        mentioned += identifiers(inner.text)

        # two loops: every name in every line of Rust code in the statement
        mentioned += [name for line in inner.rust_lines for name in identifiers(line.code)]

    return mentioned
