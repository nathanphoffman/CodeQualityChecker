from bisect import bisect_right
from typing import NamedTuple

class Point(NamedTuple):
    row: int
    column: int

class Source_Map:
    """Turns a character offset into a (row, column), and keeps the text the nodes slice their own text from."""

    def __init__(self, source):
        self.source = source
        self.line_starts = [0] + [index + 1 for index, character in enumerate(source) if character == "\n"]

    def point(self, offset):
        row = bisect_right(self.line_starts, offset) - 1

        return Point(row, offset - self.line_starts[row])

class Node:
    """A syntax tree node shaped like tree-sitter's, so the rules that walk trees can read Rexx without knowing the difference.
    Every node is named. Identifiers keep their text in lower case, because Rexx ignores the case of names."""

    is_named = True
    has_error = False

    def __init__(self, type_, start, end, source_map, children=(), fields=None, text=None):
        self.type = type_
        self.start_byte, self.end_byte = start, end
        self.source_map = source_map
        self.children = list(children)
        self.fields = {name: list(nodes) for name, nodes in (fields or {}).items()}
        self.parent = None
        self.override = text

        for child in self.children:
            child.parent = self

    @property
    def text(self):
        return (self.override if self.override is not None else self.source_map.source[self.start_byte:self.end_byte]).encode()

    @property
    def named_children(self):
        return self.children

    @property
    def child_count(self):
        return len(self.children)

    @property
    def start_point(self):
        return self.source_map.point(self.start_byte)

    @property
    def end_point(self):
        return self.source_map.point(self.end_byte)

    def child_by_field_name(self, name):
        return self.fields[name][0] if self.fields.get(name) else None

    def children_by_field_name(self, name):
        return list(self.fields.get(name, []))
