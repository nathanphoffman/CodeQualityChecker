from ..deor.deor_handlers import deor_handlers
from ....language_parsers.deor.rust_blocks import real_line, rust_blocks
from ....source_code import DEOR, RUST, TYPESCRIPT
from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.tree_walk import identifiers_in, squashed, walk
from ....language_parsers.tree_sitter.use_names import dotted
from ..shared.Error_Handler import Error_Handler
from ..shared.limits import SILENT_CALLBACK_BODIES
from ..python.python_handlers import is_loud_name

ERR_CONSTRUCTOR = "Err"
SILENT_RUST_BODIES = {"block", "unit_expression"}  # `{}` and `()`

def line_of(node):
    return node.start_point.row + 1

def rust_error_arm(arm):
    """An Error_Handler for a match arm that handles Err(...), or None for any other arm."""
    pattern = arm.child_by_field_name("pattern").named_children[0] if arm.child_by_field_name("pattern").named_children else None

    if pattern is None or pattern.type != "tuple_struct_pattern" or pattern.child_by_field_name("type").text.decode() != ERR_CONSTRUCTOR:
        return None

    body = arm.child_by_field_name("value")

    is_empty = body.type in SILENT_RUST_BODIES and not (body.type == "block" and body.named_children)

    return Error_Handler(line_of(arm), True, not is_empty, len(pattern.named_children) == 1)

def rust_handlers(root):
    found = []

    for node in walk(root):
        if node.type == "match_arm":
            arm = rust_error_arm(node)

            found += [arm] if arm else []
        elif node.type == "let_declaration" and squashed(node.text.decode()).startswith("let_="):
            found.append(Error_Handler(line_of(node), True, False, True))  # `let _ = might_fail();` throws the result away
        elif node.type == "try_expression" or (node.type == "call_expression" and node.child_by_field_name("function").text.decode() == ERR_CONSTRUCTOR):
            found.append(Error_Handler(line_of(node), False, True, False))

    return found

def catch_clause_is_loud(clause):
    body = clause.child_by_field_name("body")
    parameter = clause.child_by_field_name("parameter")
    throws = any(node.type == "throw_statement" for node in walk(body))
    speaks = any(node.type == "call_expression" and is_loud_name(dotted(node.child_by_field_name("function").text.decode())) for node in walk(body))

    return throws or speaks or (parameter is not None and parameter.text.decode() in identifiers_in(body, TYPESCRIPT))

def promise_catch_is_silent(call):
    """`.catch(() => {})` and friends: the callback does nothing with the error."""
    arguments = squashed(call.child_by_field_name("arguments").text.decode())

    return "=>" in arguments and arguments.split("=>")[-1] in SILENT_CALLBACK_BODIES

def typescript_handlers(root):
    found = []

    for node in walk(root):
        if node.type == "catch_clause":
            found.append(Error_Handler(line_of(node), True, catch_clause_is_loud(node), True))
        elif node.type == "throw_statement":
            found.append(Error_Handler(line_of(node), False, True, False))
        elif node.type == "call_expression" and node.child_by_field_name("function").text.decode().endswith(".catch"):
            found.append(Error_Handler(line_of(node), True, not promise_catch_is_silent(node), True))

    return found

def deor_error_handlers(source):
    """Deor crashes and failed-validity checks, plus the handlers in its `rust` blocks (read as Rust, lines moved back)."""
    found = [Error_Handler(*fields) for fields in deor_handlers(source)]

    for first_line, wrapped in rust_blocks(source):
        found += [Error_Handler(real_line(first_line, handler.line_number), *handler[1:])
                  for handler in rust_handlers(parse_tree(wrapped, RUST))]

    return found

def tree_handlers(source, language):
    if language == DEOR:
        return deor_error_handlers(source)

    root = parse_tree(source, language)

    return rust_handlers(root) if language == RUST else typescript_handlers(root)
