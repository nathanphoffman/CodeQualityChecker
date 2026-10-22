from .tree_walk import squashed

# Node types named by one of their fields: `new X()` and Rust macros like println!.
NAMING_FIELDS = {"new_expression": "constructor", "macro_invocation": "macro"}

def dotted(text):
    """`a?.b` and `a::b` both become `a.b`, so one name works across languages."""

    return squashed(text).replace("?.", ".").replace("::", ".")

def assignment_name(node):
    """`element.innerHTML = x` is named `assign.innerHTML`. Plain variable assignments get no name."""
    left = node.child_by_field_name("left")

    if left.type != "member_expression":
        return None

    return "assign." + left.child_by_field_name("property").text.decode()

def called_name(node):
    """The callee of a call. Hare's grammar calls the field `callee`, the others `function`."""

    return node.child_by_field_name("function") or node.child_by_field_name("callee")

def use_name(node):
    """The dotted name of a call, assignment, JSX attribute or unsafe block, or None for other nodes."""

    if node.type == "call_expression":
        return dotted(called_name(node).text.decode())

    if node.type in NAMING_FIELDS:
        return dotted(node.child_by_field_name(NAMING_FIELDS[node.type]).text.decode())

    if node.type == "assignment_expression":
        return assignment_name(node)

    if node.type == "jsx_attribute":
        return "jsx." + node.named_children[0].text.decode()

    return "unsafe" if node.type == "unsafe_block" else None
