import re

from ....source_code import FORTRAN, MOJO, REXX

# How lines open and close blocks. Rust, TypeScript, C, Go and Hare use braces; Mojo uses indentation; Fortran uses `end` lines.
OPENERS = ("{", "(", "[", ":")
CLOSERS = ("}", ")", "]")
CONTINUATIONS = {MOJO: ("else", "elif", "except", "finally"), FORTRAN: ("end", "else", "case", "contains"), REXX: ("end", "else", "when", "otherwise")}
DEFAULT_CONTINUATIONS = ("else", "catch", "finally", ".", "while")

# Comment starts. `#` is left out for most languages because Rust attributes like #[derive] and C's #include begin with it.
COMMENT_STARTS = {MOJO: ("#",), FORTRAN: ("!",), REXX: ("/*", "*")}
DEFAULT_COMMENT_STARTS = ("//", "/*", "*")

# Clever on purpose: a Fortran line that opens a block, so the first statement inside it needs no blank line above.
#   do, else, case, select, program, module, contains, interface and `type :: name` (not a `type(name) :: x` declaration)
#   `if (...) then` and `else if (...) then`
#   a function or subroutine header, which may start with a type or `pure`/`recursive`, but is not an `end function` line
FORTRAN_OPENER = re.compile(r"^(?:do\b|else\b|case\b|select\b|program\b|module\b|contains\b|interface\b|type\b(?!\s*\()"
                            r"|(?:else\s*)?if\b.*\bthen$|(?!end\b).*\b(?:function|subroutine)\b)", re.I)
FORTRAN_CLOSER = re.compile(r"^end\s*(?:if|do|select|function|subroutine|module|program|type|interface|where)?\b", re.I)

# Clever on purpose: a Rexx line that opens a block, so the first statement inside it needs no blank line above.
#   an optional `if ... then` or `else` in front of `do`, or a `select` or `otherwise`
#   an `if ... then`, `when ... then` or `else` whose instruction is on the next line
#   a label (`name:`), which may be followed by `procedure`
REXX_OPENER = re.compile(r"^(?:(?:if|when)\b.*\bthen\s+|else\s+)?do\b|^(?:select|otherwise)\b|^(?:if|when)\b.*\bthen$|^else$|^\w+:(?:\s*procedure\b.*)?$", re.I)
REXX_CLOSER = re.compile(r"^end\b", re.I)

def comment_starts(language):
    return COMMENT_STARTS.get(language, DEFAULT_COMMENT_STARTS)

def continuations(language):
    """Words that start the line after a block without being a new paragraph: `else`, `except`, `end if`..."""

    return CONTINUATIONS.get(language, CLOSERS + DEFAULT_CONTINUATIONS)

def opens_block(text, language):
    """True when this line starts a block, so the line after it is first in its block."""

    if language == FORTRAN:
        return text.endswith(("{", "(", "[")) or bool(FORTRAN_OPENER.match(text))  # "{" stands for the start of the file

    if language == REXX:
        return text.endswith("{") or bool(REXX_OPENER.match(text))  # "{" stands for the start of the file

    return text.endswith(OPENERS)

def indent_of(line):
    return len(line) - len(line.lstrip())

def next_code_line(lines, index):
    for later in lines[index + 1:]:
        if later.strip() and not later.strip().startswith(comment_starts(MOJO)):
            return later

    return ""

def closes_block(lines, index, language):
    """True when this line is the last of a block: a closing brace, an `end` line, or the line before the indentation drops."""
    text = lines[index].strip()

    if language == FORTRAN:
        return bool(FORTRAN_CLOSER.match(text))

    if language == REXX:
        return bool(REXX_CLOSER.match(text))

    if language == MOJO:
        following = next_code_line(lines, index)

        return bool(following) and indent_of(following) < indent_of(lines[index])

    return text.startswith(CLOSERS) and not text.endswith(OPENERS + (",",))

def finishes_statement(text, language):
    """True when a line ends a statement, so a comment right below it needs a blank line above."""

    if language == FORTRAN:
        return not opens_block(text, language) and not text.endswith("&")

    if language == REXX:
        return not opens_block(text, language) and not text.endswith(",")

    if language == MOJO:
        return not text.endswith(OPENERS + (",", "\\"))

    return text.endswith((";", "}"))
