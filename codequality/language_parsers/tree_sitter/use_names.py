from .tree_walk import squashed

# Node types named by one of their fields: `new X()` and Rust macros like println!.
NAMING_FIELDS = {"new_expression": "constructor", "macro_invocation": "macro", "object_creation_expression": "type"}

def dotted(text):
    """`a?.b`, `a::b` and `a->b` all become `a.b`, so one name works across languages."""

    return squashed(text).replace("?.", ".").replace("::", ".").replace("->", ".")

def assignment_name(node):
    """`element.innerHTML = x` is named `assign.innerHTML`. Plain variable assignments get no name."""
    left = node.child_by_field_name("left")

    if left.type != "member_expression":
        return None

    return "assign." + left.child_by_field_name("property").text.decode()

CALL_TYPES = {"call_expression", "call", "subroutine_call", "invocation_expression"}  # Mojo, Fortran (`call name(...)`) and C#
STATEMENT_NAMES = {"print_statement": "print", "write_statement": "write", "open_statement": "open", "read_statement": "read"}  # Fortran

def called_name(node):
    """The callee of a call. Hare's grammar calls the field `callee`, Fortran's `subroutine` or nothing, the others `function`."""
    named = node.child_by_field_name("function") or node.child_by_field_name("callee") or node.child_by_field_name("subroutine")

    return named or (node.named_children[0] if node.type == "call_expression" and node.named_children else None)

def is_fortran_call(node):
    """Fortran's grammar gives the callee of a call no field name."""

    return node.type == "subroutine_call" or (node.type == "call_expression" and node.child_by_field_name("function") is None
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

    return "unsafe" if node.type in ("unsafe_block", "unsafe_statement") else STATEMENT_NAMES.get(node.type)
