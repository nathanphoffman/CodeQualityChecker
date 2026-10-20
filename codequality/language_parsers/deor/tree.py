from dataclasses import dataclass, field
from functools import lru_cache

from .lines import RUST_HEADER, read_lines
from .words import blank_strings

MAX_CACHED_FILES = 2048  # every rule reads every file, so each is parsed once per run

@dataclass(eq=False)
class Deor_Statement:
    """One statement: a single line, or several when brackets wrap it. Indented statements below it are its children."""
    first_line: int
    last_line: int  # where this statement's own text ends
    indent: int
    text: str  # the code of all its lines joined by single spaces, comments removed
    rust_lines: list = field(default_factory=list)  # the Deor_Lines of a `rust` block, which is not Deor
    children: list = field(default_factory=list)
    parent: object = None

    @property
    def keyword(self):
        words = self.text.split()

        return words[0] if words else ""

    @property
    def end_line(self):
        """The last line of the statement including everything indented under it."""
        ends = [self.last_line] + [child.end_line for child in self.children] + [line.number for line in self.rust_lines if line.code]

        return max(ends)

@dataclass(eq=False)
class Parsed_Deor:
    lines: list
    roots: list

def bracket_balance(code):
    outside_strings = blank_strings(code)

    return sum(outside_strings.count(open_) - outside_strings.count(close) for open_, close in ("()", "[]"))

def build_roots(lines):
    roots, stack, open_statement, depth, rust_header = [], [], None, 0, None

    for line in lines:
        if line.in_rust:
            if rust_header is not None and line.code:
                rust_header.rust_lines.append(line)

            continue

        if not line.code:
            continue

        if open_statement is not None:  # the middle or end of a statement that wraps inside brackets
            open_statement.text += " " + line.code
            open_statement.last_line = line.number
            depth += bracket_balance(line.code)
            open_statement = open_statement if depth > 0 else None

            continue

        statement = Deor_Statement(line.number, line.number, line.indent, line.code)

        while stack and stack[-1].indent >= statement.indent:
            stack.pop()

        statement.parent = stack[-1] if stack else None
        (statement.parent.children if statement.parent else roots).append(statement)
        stack.append(statement)
        rust_header = statement if line.code == RUST_HEADER else None
        depth = bracket_balance(line.code)
        open_statement = statement if depth > 0 else None

    return roots

@lru_cache(maxsize=MAX_CACHED_FILES)
def parse_deor(source):
    lines = read_lines(source)

    return Parsed_Deor(lines, build_roots(lines))

def walk_statements(roots):
    """Every statement under these, parents before children, in file order."""

    for statement in roots:
        yield statement
        yield from walk_statements(statement.children)