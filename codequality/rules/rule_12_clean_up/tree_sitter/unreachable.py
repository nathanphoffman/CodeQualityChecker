from ....language_parsers.tree_sitter.tree_functions import statements_of
from ....language_parsers.tree_sitter.tree_walk import walk

BLOCK_TYPES = {"block", "statement_block", "compound_statement"}
TERMINATOR_TYPES = {"return_statement", "throw_statement", "break_statement", "continue_statement", "yield_statement", "goto_statement"}
HARE_CONTINUE = b"continue"
RUST_TERMINATOR_EXPRESSIONS = {"return_expression", "break_expression", "continue_expression"}

def ends_the_block(statement):
    if statement.type in TERMINATOR_TYPES or statement.type in RUST_TERMINATOR_EXPRESSIONS:
        return True

    if statement.type == "expression_statement" and statement.named_children and statement.named_children[0].text == HARE_CONTINUE:
        return True  # Hare's grammar reads `continue` as a plain name

    # Hare wraps `return;` and `break;` in an expression statement, like Rust does for its terminator expressions
    return statement.type == "expression_statement" and any(child.type in RUST_TERMINATOR_EXPRESSIONS | TERMINATOR_TYPES for child in statement.named_children)

def tree_unreachable(root):
    """(statements in the file, line numbers of statements after a return, throw, break or continue in the same block)."""
    total, unreachable = 0, []

    for block in [node for node in walk(root) if node.type in BLOCK_TYPES]:
        statements = statements_of(block)
        total += len(statements)
        ends = [index for index, statement in enumerate(statements) if ends_the_block(statement)]
        unreachable += [statement.start_point.row + 1 for statement in statements[ends[0] + 1:]] if ends else []

    return total, unreachable
