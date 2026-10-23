import warnings
from functools import partial

from .statements.call_statements import Call_Statements
from .statements.control_flow import Control_Flow
from .reading.expressions import Expression_Reader
from .nodes import Node, Source_Map
from .reading.reader import CLAUSE_WORDS, Token_Reader
from .statements.simple_statements import Simple_Statements
from .statements.templates import Template_Statements
from .tokens import COMMENT, OPERATOR, SYMBOL, tokenize
from ...language_parsers.tree_sitter.syntax_shapes import NAME_FIELD, PARAMETERS

LABEL_MARK = ":"

class Rexx_Parser(Token_Reader, Expression_Reader, Simple_Statements, Call_Statements, Template_Statements, Control_Flow):
    """Reads Rexx into a Node tree. Rexx has no grammar a tree-sitter parser can follow, so this is a small hand-written reader:
    labels start routines, `do`/`select` end at `end`, and anything it can't read as an instruction is a host command, as in Rexx itself."""

    def __init__(self, source):
        self.map = Source_Map(source)
        self.tokens, self.comments, self.ok = tokenize(source)
        self.index, self.last_end, self.stops = 0, 0, frozenset(CLAUSE_WORDS)
        self.keywords = self.keyword_table()

    def keyword_table(self):
        with_value = {"say": "say_statement", "return": "return_statement", "interpret": "interpret_statement", "push": "push_statement",
                      "queue": "push_statement", "numeric": "directive_statement", "trace": "directive_statement", "options": "directive_statement"}

        table = {word: partial(self.keyword_with_value, type_) for word, type_ in with_value.items()}

        return table | {"call": self.call, "if": self.if_statement, "do": self.do, "select": self.select, "exit": self.exit_statement,
                        "leave": self.leave, "iterate": self.iterate, "nop": self.nop, "arg": self.arg, "parse": self.parse, "pull": self.pull,
                        "procedure": self.procedure, "drop": self.drop, "address": self.address, "signal": self.signal}

    def is_label(self):
        return self.peek().kind == SYMBOL and self.peek(1).text == LABEL_MARK and self.peek(1).start == self.peek().end

    def is_assignment(self):
        return self.peek().kind == SYMBOL and self.peek(1).kind == OPERATOR and self.peek(1).text == "=" and not self.peek().text[0].isdigit()

    def assignment(self):
        start = self.peek().start
        left = self.symbol_node(self.advance())
        self.advance()
        right = self.expression()

        return self.make("assignment_statement", start, [left] + ([right] if right else []), {"left": [left], "right": [right] if right else []})

    def command(self):
        """Anything that is not an instruction is sent to the host system as a command, which is what Rexx does too."""
        start = self.peek().start
        value = self.expression()

        if value is None or not self.is_clause_end():
            self.fail()

            while not self.is_clause_end():
                self.advance()

        return self.make("command_statement", start, [value] if value else [], {"command": [value] if value else []})

    def statement(self):
        if self.is_label():
            return self.label_statement()

        if self.is_assignment():
            return self.assignment()

        handler = self.keywords.get(self.word(self.peek()))

        return handler() if handler else self.command()

    def label_statement(self):
        start = self.peek().start
        name = self.name_node(self.advance())
        self.advance()

        return self.make("label_statement", start, [name])

    def statements(self, stop_words, in_routine):
        """Statements until a stop word, the end of the file, or (in a routine) the next label."""
        found = []

        while True:
            self.skip_ends()

            if self.at_end() or self.word(self.peek()) in stop_words or (in_routine and self.is_label()):
                return found

            if self.word(self.peek()) in ("end", "then", "else", "when", "otherwise") and not self.is_assignment():
                self.fail()
                self.advance()

                continue

            found.append(self.statement())

    def routine(self):
        start = self.peek().start
        name = self.name_node(self.advance())
        self.advance()
        statements = self.statements(set(), in_routine=True)
        body = self.body_block(start, statements)
        parameters = self.parameters_of(statements, start)

        return self.make("routine_definition", start, [name, body], {NAME_FIELD: [name], "body": [body], PARAMETERS: parameters},
                         end=statements[-1].end_byte if statements else self.last_end)

    def body_block(self, start, statements):
        first = statements[0].start_byte if statements else start

        return Node("block", first, statements[-1].end_byte if statements else first, self.map, statements)

    def parameters_of(self, statements, start):
        """The `parameters` node for the first `arg` or `parse arg` of a routine, or none."""
        found = next((statement for statement in statements if statement.type == "arg_statement"), None)

        if found is None:
            return []

        node = Node(PARAMETERS, found.start_byte, found.end_byte, self.map)
        node.children = found.children

        return [node]

    def program(self):
        children, main = [], self.statements(set(), in_routine=True)

        if main:
            children.append(self.body_block(0, main))

        while not self.at_end():
            children.append(self.routine())

        root = Node("source_file", 0, len(self.map.source), self.map, sorted(children + self.comment_nodes(), key=lambda node: node.start_byte))
        root.has_error = not self.ok

        return root

    def comment_nodes(self):
        return [Node(COMMENT, token.start, token.end, self.map) for token in self.comments]

def parse_rexx(source):
    """Root node of the syntax tree. Like the other parsers, it warns when the source has errors."""
    root = Rexx_Parser(source).program()

    if root.has_error:
        warnings.warn("rexx source has syntax errors; its results may be incomplete")

    return root

def has_clean_rexx(source):
    """True when the text reads as Rexx instructions with no errors. Prose reads as host commands, so a command means it is not code."""
    root = Rexx_Parser(source).program()
    nodes = [root]
    found = []

    while nodes:
        node = nodes.pop()
        found.append(node.type)
        nodes += node.children

    return not root.has_error and "command_statement" not in found and len(found) > 2
