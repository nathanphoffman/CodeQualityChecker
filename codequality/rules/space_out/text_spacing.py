from ..comment_why.extract.line_helpers import COMMENT_MARKERS
from .Spacing_Gaps import Spacing_Gaps

CONTROL_WORDS = {"if", "for", "while", "switch", "match", "try", "return", "break", "continue", "throw", "loop", "do", "case",
                 "default", "fn", "function", "class"}

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
    """True for lines like `if (x) {`, `return y;`, `pub async fn f() {` and `case 1:`."""
    words = [word for word in text.split() if word not in MODIFIERS]

    return bool(words) and leading_word(words[0]) in CONTROL_WORDS

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

def text_gaps(source):
    """A Spacing_Gaps for a Rust or TypeScript file, read as text: braces and keywords instead of a syntax tree."""
    lines, control_missing, block_missing = source.splitlines(), [], []
    control_total = block_total = 0

    for index, line in enumerate(lines):
        text = line.strip()

        if starts_control(text):
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
