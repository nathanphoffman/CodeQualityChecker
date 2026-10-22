from ..deor.deor_handlers import deor_handlers
from ....language_parsers.deor.rust_blocks import real_line, rust_blocks
from ....source_code import C_LANG, CSHARP, DEOR, FORTRAN, GO, HARE, MOJO, REXX, RUST, TYPESCRIPT
from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.tree_functions import function_name
from ....language_parsers.tree_sitter.tree_walk import identifiers_in, squashed, walk
from ....language_parsers.tree_sitter.use_names import called_name, dotted
from ..shared.Error_Handler import Error_Handler
from ..shared.limits import SILENT_CALLBACK_BODIES
from ..python.python_handlers import is_loud_name

ERR_CONSTRUCTOR = "Err"
HARE_ERROR_TYPE = "error"
HARE_SPEAKING_NODES = {"call_expression", "return_statement", "error_assertion_expression", "try_expression"}
SPEAKING_NODES = {"call_expression", "return_statement", "goto_statement"}  # C and Go: a failed check that calls, returns or jumps does something
GO_RAISING_CALLS = {"panic", "errors.New", "fmt.Errorf"}
C_STOPPING_CALLS = {"abort", "exit"}
C_FAILURE_WORDS = ("NULL", "<0", "==-1", "errno")  # in a condition with its spaces removed
GO_ERROR_WORD = "err"
FORTRAN_STATUS_WORDS = ("iostat", "stat", "ios", "ierr", "err", "status", "info")  # what a Fortran status variable is usually called
FORTRAN_SPEAKING_NODES = {"stop_statement", "subroutine_call", "print_statement", "write_statement"}
FORTRAN_RETURN = b"return"
CSHARP_BROAD_EXCEPTIONS = {"Exception", "System.Exception", "SystemException"}
CSHARP_THROWING_NODES = {"throw_statement", "throw_expression"}
REXX_STATUS_VARIABLE = "rc"  # the return code Rexx sets after every command
REXX_SPEAKING_NODES = {"say_statement", "exit_statement", "call_statement", "goto_statement", "return_statement"}
REXX_NO_ERROR = b"0"
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

def hare_error_case(case):
    """An Error_Handler for a match case that receives an error, like `case let e: fs::error =>`, or None for any other case."""
    pattern = case.named_children[0] if case.named_children else None

    if pattern is None or pattern.type not in ("let_expression", "identifier", "scoped_type_identifier"):
        return None

    type_name = squashed(pattern.text.decode()).split(":")[-1] if pattern.type == "let_expression" else squashed(pattern.text.decode())

    if not type_name.endswith(HARE_ERROR_TYPE):
        return None

    body = case.named_children[1:]

    # the case speaks up when any statement in its body, at any depth, is one of the speaking nodes
    speaks = any(node.type in HARE_SPEAKING_NODES for statement in body for node in walk(statement))

    return Error_Handler(line_of(case), True, speaks, type_name == HARE_ERROR_TYPE)

def hare_handlers(root):
    """`!` (crash on an error) and `?` (pass it up) are loud. A match case on an error type is a catch."""
    found = []

    for node in walk(root):
        if node.type == "case":
            case = hare_error_case(node)

            found += [case] if case else []
        elif node.type in ("error_assertion_expression", "try_expression"):
            found.append(Error_Handler(line_of(node), False, True, False))

    return found

def go_error_check(node):
    """An Error_Handler for `if err != nil { ... }`, or None for any other `if`."""
    condition = node.child_by_field_name("condition")

    if condition is None or condition.type != "binary_expression" or condition.child_by_field_name("operator").text != b"!=":
        return None

    if condition.child_by_field_name("right").text != b"nil" or GO_ERROR_WORD not in condition.child_by_field_name("left").text.decode().lower():
        return None

    speaks = any(inner.type in SPEAKING_NODES for inner in walk(node.child_by_field_name("consequence")))

    return Error_Handler(line_of(node), True, speaks, True)

def go_handlers(root):
    """`if err != nil` is a catch. `_ = f()` throws a result away, and panic or a new error raises one."""
    found = []

    for node in walk(root):
        if node.type == "if_statement":
            check = go_error_check(node)

            found += [check] if check else []
        elif node.type == "assignment_statement" and set(squashed(node.child_by_field_name("left").text.decode())) <= {"_", ","}:
            found.append(Error_Handler(line_of(node), True, False, True))
        elif node.type == "call_expression" and dotted(called_name(node).text.decode()) in GO_RAISING_CALLS:
            found.append(Error_Handler(line_of(node), False, True, False))

    return found

def c_handlers(root):
    """C reports failure through return values: a check for NULL, a negative result or errno is a catch."""
    found = []

    for node in walk(root):
        if node.type == "if_statement":
            condition = squashed(node.child_by_field_name("condition").text.decode())
            speaks = any(inner.type in SPEAKING_NODES for inner in walk(node.child_by_field_name("consequence")))

            found += [Error_Handler(line_of(node), True, speaks, True)] if any(word in condition for word in C_FAILURE_WORDS) else []
        elif node.type == "call_expression" and called_name(node).text.decode() in C_STOPPING_CALLS:
            found.append(Error_Handler(line_of(node), False, True, False))

    return found

def mojo_except_handler(clause):
    """An Error_Handler for `except e:`. Mojo has no error types in the clause, so every one catches anything."""
    block = clause.named_children[-1]
    bound = clause.named_children[0] if len(clause.named_children) > 1 else None
    uses_error = bound is not None and bound.text.decode() in identifiers_in(block, MOJO)
    speaks = any(node.type == "raise_statement" or (node.type == "call" and is_loud_name(dotted(called_name(node).text.decode())))
                 for node in walk(block))

    return Error_Handler(line_of(clause), True, speaks or uses_error, True)

def mojo_handlers(root):
    """`except` clauses are catches, and `raise` raises."""
    found = []

    for node in walk(root):
        if node.type == "except_clause":
            found.append(mojo_except_handler(node))
        elif node.type == "raise_statement":
            found.append(Error_Handler(line_of(node), False, True, False))

    return found

def fortran_status_check(node):
    """An Error_Handler for `if (ios /= 0) ...`: a check on a status variable like iostat= or stat=, or None for any other `if`."""
    condition = squashed(node.named_children[0].text.decode()).lower() if node.named_children else ""

    if not any(word in condition for word in FORTRAN_STATUS_WORDS):
        return None

    body = node.named_children[1:]

    # the check speaks up when anything in its body, at any depth, stops, prints, calls or returns
    speaks = any(inner.type in FORTRAN_SPEAKING_NODES or (inner.type == "keyword_statement" and inner.text.lower().startswith(FORTRAN_RETURN))
                 for statement in body for inner in walk(statement))

    return Error_Handler(line_of(node), True, speaks, True)

def fortran_handlers(root):
    """`stop` and `error stop` end the program loudly. A check on a status variable is a catch."""
    found = []

    for node in walk(root):
        if node.type == "if_statement":
            check = fortran_status_check(node)

            found += [check] if check else []
        elif node.type == "stop_statement":
            found.append(Error_Handler(line_of(node), False, True, False))

    return found

def csharp_catch(clause):
    """An Error_Handler for a `catch`. One with no type, or catching Exception itself, catches anything."""
    declaration = next((child for child in clause.children if child.type == "catch_declaration"), None)
    caught_type = declaration.child_by_field_name("type") if declaration is not None else None
    bound = declaration.child_by_field_name("name") if declaration is not None else None
    body = clause.child_by_field_name("body")
    uses_error = bound is not None and bound.text.decode() in identifiers_in(body, CSHARP)

    # Console.WriteLine and _logger.LogError speak up: names are lower-cased and lose their leading underscore to match the shared list
    speaks = any(node.type in CSHARP_THROWING_NODES or (node.type == "invocation_expression"
                 and is_loud_name(dotted(called_name(node).text.decode()).lower().lstrip("_"))) for node in walk(body))

    return Error_Handler(line_of(clause), True, speaks or uses_error, caught_type is None or caught_type.text.decode() in CSHARP_BROAD_EXCEPTIONS)

def csharp_handlers(root):
    """`catch` clauses are catches, and `throw` raises."""
    found = []

    for node in walk(root):
        if node.type == "catch_clause":
            found.append(csharp_catch(node))
        elif node.type in CSHARP_THROWING_NODES:
            found.append(Error_Handler(line_of(node), False, True, False))

    return found

def rexx_status_check(node):
    """An Error_Handler for `if rc <> 0 then ...`: a check on the return code, or None for any other `if`."""
    condition, consequence = node.child_by_field_name("condition"), node.child_by_field_name("consequence")

    if condition is None or REXX_STATUS_VARIABLE not in identifiers_in(condition, REXX):
        return None

    return Error_Handler(line_of(node), True, any(inner.type in REXX_SPEAKING_NODES for inner in walk(consequence)), True)

def rexx_trap(node, routines):
    """`signal on error` and `call on halt` catch a condition and run the label named, which is loud when it speaks up."""
    labels = {label.text.decode() for label in node.children}
    handler = next((routine for routine in routines if function_name(routine) in labels), None)
    speaks = handler is not None and any(inner.type in REXX_SPEAKING_NODES for inner in walk(handler))

    return Error_Handler(line_of(node), True, speaks, True)

def rexx_handlers(root):
    """A check on `rc` and a trap are catches. `exit` with a value other than 0 raises."""
    routines = [node for node in walk(root) if node.type == "routine_definition"]
    found = []

    for node in walk(root):
        value = node.child_by_field_name("value") if node.type == "exit_statement" else None

        if node.type == "if_statement":
            check = rexx_status_check(node)

            found += [check] if check else []
        elif node.type == "trap_statement" and node.text.lower().split()[1] == b"on":
            found.append(rexx_trap(node, routines))
        elif value is not None and value.text != REXX_NO_ERROR:
            found.append(Error_Handler(line_of(node), False, True, False))

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

    handlers = {RUST: rust_handlers, HARE: hare_handlers, C_LANG: c_handlers, GO: go_handlers, MOJO: mojo_handlers,
                FORTRAN: fortran_handlers, CSHARP: csharp_handlers, REXX: rexx_handlers}

    return handlers.get(language, typescript_handlers)(root)
