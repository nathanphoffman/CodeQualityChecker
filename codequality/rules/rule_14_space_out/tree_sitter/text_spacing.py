import re

from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.tree_walk import normalized, walk
from ....source_code import C_LANG, CSHARP, FORTRAN, MOJO, REXX, RUST
from ...rule_09_comment_why.shared.extract.line_helpers import COMMENT_MARKERS
from ..shared.comment_gaps import comment_block_gaps
from ..shared.Spacing_Gaps import Spacing_Gaps
from .block_syntax import closes_block, comment_starts, continuations, finishes_statement, opens_block

# Words that start a control statement or a definition. Python's classes are Rust's structs, enums, traits and impls.
CONTROL_WORDS = {"if", "for", "while", "switch", "match", "try", "return", "break", "continue", "throw", "loop", "do", "case",
                 "default", "yield", "fn", "function", "func", "select", "defer", "go", "goto", "typedef", "class", "struct", "enum", "trait", "impl", "mod", "interface", "macro_rules",
                 "def", "raise", "with", "foreach", "lock", "namespace"}  # the last six are not names in any other language, so sharing one set costs nothing: Mojo's def, raise and with, C#'s foreach, lock and namespace

# Clever on purpose: finds a function stored in a variable, like `const f = (a, b): number =>` or `export const f = async x =>`.
#   an optional "export", then const, let or var, then the name
#   "=" and then straight away the parameters, so `const x = items.map(i => i)` is a call, not a definition
ARROW_DEFINITION = re.compile(r"^(?:export\s+)?(?:const|let|var)\s+\w+[^=]*=\s*(?:async\s+)?(?:\([^()]*\)|\w+)\s*(?::[^=]+?)?=>")

# Node types that are statements, not the value a Rust block ends with.
NOT_A_VALUE = {"expression_statement", "let_declaration", "empty_statement", "attribute_item", "inner_attribute_item"}

# Fortran's words are matched in lower case. Its function and subroutine headers can start with a type, so they are found by search.
FORTRAN_CONTROL_WORDS = {"if", "do", "select", "case", "return", "stop", "error", "exit", "cycle", "goto", "program", "module", "interface"}
FORTRAN_PROCEDURE_HEADER = re.compile(r"^(?!end\b).*\b(?:function|subroutine)\b", re.I)  # any line with the word function or subroutine, except an `end` line

MODIFIERS = {"internal", "sealed", "override", "virtual", "readonly", "partial", "extern",  # C#
             "@test", "@init", "@fini", "@noreturn", "pub", "export", "async", "unsafe", "const", "default", "static", "abstract", "public", "private", "protected"}

def leading_word(text):
    word = ""

    for character in text:
        if not (character.isalnum() or character == "_"):
            break

        word += character

    return word

def starts_control(text, language=None):
    """True for lines like `if (x) {`, `return y;`, `pub async fn f() {`, `case 1:` and `const f = () => {`."""

    if language == REXX:
        return starts_rexx_control(text)

    if language == FORTRAN:
        words = text.lower().split()

        return (bool(words) and leading_word(words[0]) in FORTRAN_CONTROL_WORDS) or bool(FORTRAN_PROCEDURE_HEADER.match(text))

    words = [word for word in text.split() if word not in MODIFIERS]

    return (bool(words) and leading_word(words[0]) in CONTROL_WORDS) or bool(ARROW_DEFINITION.match(text))

# Rexx instructions that need a blank line above them, and a label (`name:`) which starts a routine. `if = 3` is an assignment, not an `if`.
REXX_CONTROL_WORDS = {"if", "do", "select", "return", "exit", "leave", "iterate", "signal"}
REXX_LABEL = re.compile(r"^\w+:")  # a word and a colon at the start of a line
REXX_ASSIGNMENT = re.compile(r"^\w+\s*=(?!=)")  # a name and a single `=` at the start of a line, not `==`

def starts_rexx_control(text):
    return bool(REXX_LABEL.match(text)) or (leading_word(text.lower()) in REXX_CONTROL_WORDS and not REXX_ASSIGNMENT.match(text))

def rust_tail_lines(source):
    """Lines where a Rust block ends with a value, like `total` or `Ok(x)`. That is an implicit return."""
    lines = set()

    for node in walk(parse_tree(source, RUST)):
        values = [child for child in node.named_children if "comment" not in child.type] if node.type == "block" else []

        if values and values[-1].type not in NOT_A_VALUE and not values[-1].type.endswith("_item"):
            lines.add(values[-1].start_point.row + 1)

    return lines

# C and C# start a function with a return type and a name, no keyword, so text patterns can't tell it from a call: the syntax tree finds them.
DECLARATION_NODES = {C_LANG: {"function_definition"}, CSHARP: {"method_declaration", "constructor_declaration", "local_function_statement"}}

def declaration_lines(source, language):
    """Lines where a C or C# function starts (an attribute like [Fact] above it counts as part of it)."""

    return {node.start_point.row + 1 for node in walk(parse_tree(source, language)) if node.type in DECLARATION_NODES[language]}

def tail_lines(source, language):
    """Lines the text patterns can't recognise as control statements but that need a blank line above them."""

    if language == RUST:
        return rust_tail_lines(source)

    return declaration_lines(source, language) if language in DECLARATION_NODES else set()

def is_attached(line, language):
    """A comment, a Mojo decorator like `@fieldwise_init` or a C# attribute like `[Fact]` belongs to the line below it."""
    text = line.strip()

    is_attribute = (language == MOJO and text.startswith("@")) or (language == CSHARP and text.startswith("[") and text.endswith("]"))

    return text.startswith(COMMENT_MARKERS) or is_attribute

def line_above(lines, index, language=None):
    """The text of the line above this one, after skipping the comments attached to it. Also where to put a blank line."""

    while index > 0 and is_attached(lines[index - 1], language):
        index -= 1

    return index, (lines[index - 1].strip() if index else "{")

def next_code(lines, index):
    for later in lines[index + 1:]:
        if later.strip():
            return later.strip()

    return ""

def comment_gaps(lines, language=None):
    """Comments on their own line follow the same rule as control statements: a blank line above, unless first in a block."""
    comment_lines, blank_lines, finished_lines = set(), set(), set()

    for number, line in enumerate(lines, start=1):
        text = line.strip()

        if text.startswith(comment_starts(language)) and (not text.startswith("*") or number - 1 in comment_lines):
            comment_lines.add(number)
        elif not text:
            blank_lines.add(number)
        elif finishes_statement(text, language):
            finished_lines.add(number)

    return comment_block_gaps(comment_lines, blank_lines, finished_lines)

def text_gaps(source, language):
    """A Spacing_Gaps for any language but Python and Deor, read as text: braces, indentation and keywords instead of a syntax tree."""
    lines, control_missing, block_missing = source.splitlines(), [], []
    control_seen, block_total = set(), 0
    tails = tail_lines(source, language)

    for index, line in enumerate(lines):
        text = line.strip()

        if starts_control(text, language) or index + 1 in tails:
            above_index, above = line_above(lines, index, language)

            if not opens_block(above, language):  # otherwise it is first in its block
                control_seen.add(above_index + 1)
                control_missing += [above_index + 1] if above else []

        if closes_block(lines, index, language):
            following = next_code(lines, index)

            if following and not normalized(following, language).startswith(continuations(language)):
                block_total += 1
                block_missing += [index + 2] if lines[index + 1].strip() else []

    comment_seen, comment_missing = comment_gaps(lines, language)
    control_seen |= comment_seen

    return Spacing_Gaps(len(control_seen), sorted(set(control_missing + comment_missing)), block_total, sorted(set(block_missing)))
