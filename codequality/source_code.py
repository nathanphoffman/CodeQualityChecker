import re

SUFFIX_LANGUAGE = {".py": "python", ".rs": "rust", ".ts": "typescript", ".tsx": "typescript"}
BRACKET_PAIRS = {"(": ")", "{": "}", "[": "]"}

# Clever on purpose: matches comments and string literals so we can blank them out.
# Otherwise braces inside text would confuse the brace counting.
TEXT_PATTERN = re.compile(r"//[^\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`", re.S)


def blank_out_text(source):
    """Replace comments and strings with spaces, keeping newlines so line numbers still match."""
    return TEXT_PATTERN.sub(lambda hit: re.sub(r"[^\n]", " ", hit.group()), source)


def matching_close(text, open_index):
    open_char = text[open_index]
    close_char = BRACKET_PAIRS[open_char]
    depth = 0
    for index in range(open_index, len(text)):
        depth += (text[index] == open_char) - (text[index] == close_char)
        if depth == 0:
            return index
    return None


def line_number_at(text, index):
    return text.count("\n", 0, index) + 1
