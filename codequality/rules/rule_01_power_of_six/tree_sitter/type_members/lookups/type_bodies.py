# Each of these takes a type's syntax node and returns the node whose children are its members, or None when there are none to count.

def body_field(node):
    return node.child_by_field_name("body")

def whole_node(node):
    return node

def nothing(node):
    return None

def go_body(node):
    """A Go struct's fields sit in a list inside `struct_type`; an interface's methods sit in `interface_type` itself."""
    kind = node.child_by_field_name("type")

    if kind is not None and kind.type == "struct_type":
        return kind.named_children[0] if kind.named_children else None

    return kind if kind is not None and kind.type == "interface_type" else None

def object_type_body(node):
    """A TypeScript `type Name = { ... }`: only an object type has members."""
    value = node.child_by_field_name("value")

    return value if value is not None and value.type == "object_type" else None
