from ...language_parsers.tree_sitter.syntax_shapes import CALL_EXPRESSION, FUNCTION_FIELD, LEFT_FIELD
from .tree_walk import squashed, walk

# Node types named by one of their fields: `new X()` and Rust macros like println!.
NAMING_FIELDS = {"new_expression": "constructor", "macro_invocation": "macro", "object_creation_expression": "type"}

def dotted(text):
    """`a?.b`, `a::b` and `a->b` all become `a.b`, so one name works across languages."""

    return squashed(text).replace("?.", ".").replace("::", ".").replace("->", ".")

def assignment_name(node):
    """`element.innerHTML = x` is named `assign.innerHTML`. Plain variable assignments get no name."""
    left = node.child_by_field_name(LEFT_FIELD)

    if left.type != "member_expression":
        return None

    return "assign." + left.child_by_field_name("property").text.decode()

CALL_TYPES = {"call_expression", "call", "subroutine_call", "invocation_expression", "call_statement"}  # Mojo, Fortran (`call name(...)`), C# and Rexx
STATEMENT_NAMES = {"print_statement": "print", "write_statement": "write", "open_statement": "open", "read_statement": "read",  # Fortran
                   "say_statement": "say", "interpret_statement": "interpret"}  # Rexx

HOST_COMMANDS = {"command_statement", "address_statement"}  # Rexx sends these to the operating system

def runs_host_command(node):
    """A Rexx command that has a variable in it is built from parts, which is how shell injection happens. A fixed string is fine."""
    command = node.child_by_field_name("command")

    return command is not None and any(inner.type == "identifier" and inner.parent.type != "call_expression" for inner in walk(command))

def called_name(node):
    """The callee of a call. Hare's grammar calls the field `callee`, Fortran's `subroutine` or nothing, the others `function`."""
    named = node.child_by_field_name(FUNCTION_FIELD) or node.child_by_field_name("callee") or node.child_by_field_name("subroutine")

    return named or (node.named_children[0] if node.type == CALL_EXPRESSION and node.named_children else None)

def is_fortran_call(node):
    """Fortran's grammar gives the callee of a call no field name."""

    return node.type == "subroutine_call" or (node.type == CALL_EXPRESSION and node.child_by_field_name(FUNCTION_FIELD) is None
                                              and node.child_by_field_name("callee") is None)

def use_name(node):
    """The dotted name of a call, assignment, JSX attribute or unsafe block, or None for other nodes."""

    if node.type in CALL_TYPES:
        name = dotted(called_name(node).text.decode())

        return name.lower() if is_fortran_call(node) else name  # Fortran ignores case

    if node.type in NAMING_FIELDS:
        return dotted(node.child_by_field_name(NAMING_FIELDS[node.type]).text.decode())

    if node.type == "assignment_expression":
        return assignment_name(node)

    if node.type == "jsx_attribute":
        return "jsx." + node.named_children[0].text.decode()

    if node.type in HOST_COMMANDS:
        return "command" if runs_host_command(node) else None

    return "unsafe" if node.type in ("unsafe_block", "unsafe_statement") else STATEMENT_NAMES.get(node.type)
