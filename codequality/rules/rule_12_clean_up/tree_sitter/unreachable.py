from ....language_parsers.tree_sitter.tree_functions import statements_of
from ....language_parsers.tree_sitter.tree_walk import walk

BLOCK_TYPES = {"block", "statement_block", "compound_statement", "function", "subroutine", "program", "do_loop"}  # the last four are Fortran
TERMINATOR_TYPES = {"return_statement", "throw_statement", "break_statement", "continue_statement", "goto_statement", "raise_statement", "stop_statement"}
HARE_CONTINUE = b"continue"
FORTRAN_JUMPS = {"return", "exit", "cycle"}  # `goto` is left out: code after it can be reached through a label
RUST_TERMINATOR_EXPRESSIONS = {"return_expression", "break_expression", "continue_expression"}

def is_fortran_jump(statement):
    words = statement.text.decode().lower().split()

    return statement.type == "keyword_statement" and bool(words) and words[0] in FORTRAN_JUMPS

def is_block(node):
    """TypeScript's whole file is also a node called `program`, but only Fortran's has a parent."""

    return node.type in BLOCK_TYPES and not (node.type == "program" and node.parent is None)

def is_yield_that_ends(statement):
    """Hare's `yield` ends the block, and so does C#'s `yield break`. C#'s `yield return` hands back one value and carries on."""

    return statement.type == "yield_statement" and not statement.text.startswith(b"yield return")

def ends_the_block(statement):
    if statement.type in TERMINATOR_TYPES or statement.type in RUST_TERMINATOR_EXPRESSIONS:
        return True

    if statement.type == "expression_statement" and statement.named_children and statement.named_children[0].text == HARE_CONTINUE:
        return True  # Hare's grammar reads `continue` as a plain name

    if is_fortran_jump(statement) or is_yield_that_ends(statement):
        return True

    # Hare wraps `return;` and `break;` in an expression statement, like Rust does for its terminator expressions
    return statement.type == "expression_statement" and any(child.type in RUST_TERMINATOR_EXPRESSIONS | TERMINATOR_TYPES for child in statement.named_children)

def tree_unreachable(root):
    """(statements in the file, line numbers of statements after a return, throw, break or continue in the same block)."""
    total, unreachable = 0, []

    for block in [node for node in walk(root) if is_block(node)]:
        statements = statements_of(block)
        total += len(statements)
        ends = [index for index, statement in enumerate(statements) if ends_the_block(statement)]
        unreachable += [statement.start_point.row + 1 for statement in statements[ends[0] + 1:]] if ends else []

    return total, unreachable
