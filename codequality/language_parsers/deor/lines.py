from typing import NamedTuple

TAB_WIDTH = 4
RUST_HEADER = "rust"
COMMENT_MARKER = "#"

class Deor_Line(NamedTuple):
    number: int
    indent: int
    code: str  # stripped, with any comment cut off; empty for a blank line or a line that is only a comment
    comment: str | None  # the text after the #, or None
    in_rust: bool  # inside a `rust` block, where # and // mean Rust and the text is not Deor

def split_comment(text):
    """(code, comment) for a line: the # that starts a comment only counts outside a string."""
    in_string = escaped = False

    for index, char in enumerate(text):
        if in_string:
            escaped = not escaped and char == "\\"
            in_string = escaped or char != '"'
        elif char == '"':
            in_string = True
        elif char == COMMENT_MARKER:
            return text[:index].strip(), text[index + 1:]

    return text.strip(), None

def indent_of(text):
    return len(text[:len(text) - len(text.lstrip())].expandtabs(TAB_WIDTH))

def read_lines(source):
    """Every line of a Deor file as a Deor_Line. A `rust` header makes the deeper-indented lines under it Rust."""
    lines, rust_indent = [], None

    for number, text in enumerate(source.splitlines(), start=1):
        stripped, indent = text.strip(), indent_of(text)

        if rust_indent is not None and stripped and indent <= rust_indent:
            rust_indent = None

        if rust_indent is not None:
            lines.append(Deor_Line(number, indent, stripped, None, True))

            continue

        code, comment = split_comment(stripped)
        rust_indent = indent if code == RUST_HEADER else None
        lines.append(Deor_Line(number, indent, code, comment, False))

    return lines
