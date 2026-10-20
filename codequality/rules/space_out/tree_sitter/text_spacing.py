import re

from ....source_code import RUST
from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.tree_walk import walk
from ...comment_why.shared.extract.line_helpers import COMMENT_MARKERS
from ..shared.Spacing_Gaps import Spacing_Gaps

# Words that start a control statement or a definition. Python's classes are Rust's structs, enums, traits and impls.
CONTROL_WORDS = {"if", "for", "while", "switch", "match", "try", "return", "break", "continue", "throw", "loop", "do", "case",
                 "default", "fn", "function", "class", "struct", "enum", "trait", "impl", "mod", "interface", "macro_rules"}

# Clever on purpose: finds a function stored in a variable, like `const f = (a, b): number =>` or `export const f = async x =>`.
#   an optional "export", then const, let or var, then the name
#   "=" and then straight away the parameters, so `const x = items.map(i => i)` is a call, not a definition
ARROW_DEFINITION = re.compile(r"^(?:export\s+)?(?:const|let|var)\s+\w+[^=]*=\s*(?:async\s+)?(?:\([^()]*\)|\w+)\s*(?::[^=]+?)?=>")

# Node types that are statements, not the value a Rust block ends with.
NOT_A_VALUE = {"expression_statement", "let_declaration", "empty_statement", "attribute_item", "inner_attribute_item"}

MODIFIERS = {"pub", "export", "async", "unsafe", "const", "default", "static", "abstract", "public", "private", "protected"}
OPENERS = ("{", "(", "[", ":")
CLOSERS = ("}", ")", "]")
CONTINUATIONS = ("else", "catch", "finally", ".", "while")

def leading_word(text):
    word = ""

    for character in text:
        if not (character.isalnum() or character == "_"):
            break

        word += character

    return word

def starts_control(text):
    """True for lines like `if (x) {`, `return y;`, `pub async fn f() {`, `case 1:` and `const f = () => {`."""
    words = [word for word in text.split() if word not in MODIFIERS]

    return (bool(words) and leading_word(words[0]) in CONTROL_WORDS) or bool(ARROW_DEFINITION.match(text))

def rust_tail_lines(source):
    """Lines where a Rust block ends with a value, like `total` or `Ok(x)`. That is an implicit return."""
    lines = set()

    for node in walk(parse_tree(source, RUST)):
        values = [child for child in node.named_children if "comment" not in child.type] if node.type == "block" else []

        if values and values[-1].type not in NOT_A_VALUE and not values[-1].type.endswith("_item"):
            lines.add(values[-1].start_point.row + 1)

    return lines

def line_above(lines, index):
    """The text of the line above this one, after skipping the comments attached to it. Also where to put a blank line."""

    while index > 0 and lines[index - 1].strip().startswith(COMMENT_MARKERS):
        index -= 1

    return index, (lines[index - 1].strip() if index else "{")

def next_code(lines, index):
    for later in lines[index + 1:]:
        if later.strip():
            return later.strip()

    return ""

def text_gaps(source, language):
    """A Spacing_Gaps for a Rust or TypeScript file, read as text: braces and keywords instead of a syntax tree."""
    lines, control_missing, block_missing = source.splitlines(), [], []
    control_total = block_total = 0
    tails = rust_tail_lines(source) if language == RUST else set()

    for index, line in enumerate(lines):
        text = line.strip()

        if starts_control(text) or index + 1 in tails:
            above_index, above = line_above(lines, index)

            if not above.endswith(OPENERS):  # otherwise it is first in its block
                control_total += 1
                control_missing += [above_index + 1] if above else []

        if text.startswith(CLOSERS) and not text.endswith(OPENERS + (",",)):
            following = next_code(lines, index)

            if following and not following.startswith(CLOSERS + CONTINUATIONS):
                block_total += 1
                block_missing += [index + 2] if lines[index + 1].strip() else []

    return Spacing_Gaps(control_total, sorted(set(control_missing)), block_total, sorted(set(block_missing)))
