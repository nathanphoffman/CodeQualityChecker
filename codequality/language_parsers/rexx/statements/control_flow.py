from ....language_parsers.tree_sitter.syntax_shapes import IF_STATEMENT
from ..tokens import SYMBOL

class Control_Flow:
    """`if`, `do` and `select`, the instructions that hold other instructions."""

    def branch_body(self):
        """The one instruction after `then`, `else` or `when ... then`, which can be a `do` group."""
        self.skip_ends()

        return self.statement()

    def if_statement(self):
        start = self.advance().start
        condition = self.expression({"then"})
        self.skip_ends()
        self.eat_word("then")
        consequence = self.branch_body()
        position, end = self.index, self.last_end
        self.skip_ends()

        if self.word(self.peek()) == "else":
            self.advance()
            alternative = self.branch_body()

            return self.make(IF_STATEMENT, start, [condition, consequence, alternative],
                             {"condition": [condition], "consequence": [consequence], "alternative": [alternative]})

        self.index, self.last_end = position, end

        return self.make(IF_STATEMENT, start, [condition, consequence], {"condition": [condition], "consequence": [consequence]})

    def do_header(self):
        """(the control variable or None, the expressions after `do`, whether it is a loop). `do` alone just groups statements."""
        loop_words = {"to", "by", "for", "while", "until"}
        control, parts = None, []

        if self.peek().kind == SYMBOL and self.peek(1).text == "=":
            control = self.symbol_node(self.advance())
            self.advance()

        while not self.is_clause_end():
            if self.word(self.peek()) == "forever":
                self.advance()
                parts.append(None)
            elif self.word(self.peek()) in loop_words:
                self.advance()

            value = self.expression(loop_words)

            if value is None and not self.is_clause_end() and self.word(self.peek()) not in loop_words | {"forever"}:
                self.fail()
                self.advance()

            parts += [value] if value else []

        return control, [part for part in parts if part is not None], control is not None or bool(parts)

    def do(self):
        start = self.advance().start
        control, parts, is_loop = self.do_header()
        statements = self.statements({"end"}, in_routine=False)
        self.finish_end()
        block = self.make("block", start, statements)

        if not is_loop:
            return block

        fields = {"body": [block], "left": [control] if control else []}

        return self.make("for_statement", start, ([control] if control else []) + parts + [block], fields)

    def finish_end(self):
        """Consumes `end` and an optional name after it."""

        if self.word(self.peek()) == "end":
            self.advance()

            while self.peek().kind == SYMBOL and not self.is_clause_end():
                self.advance()
        else:
            self.fail()

    def select(self):
        start = self.advance().start
        clauses = []
        self.skip_ends()

        while self.word(self.peek()) in ("when", "otherwise"):
            clauses.append(self.when() if self.word(self.peek()) == "when" else self.otherwise())
            self.skip_ends()

        self.finish_end()

        return self.make("select_statement", start, clauses)

    def when(self):
        start = self.advance().start
        condition = self.expression({"then"})
        self.skip_ends()
        self.eat_word("then")
        body = self.branch_body()

        return self.make("when_clause", start, [condition, body], {"condition": [condition], "body": [body]})

    def otherwise(self):
        start = self.advance().start
        statements = self.statements({"end"}, in_routine=False)
        block = self.make("block", start, statements, end=statements[-1].end_byte if statements else self.last_end)

        return self.make("otherwise_clause", start, [block], {"body": [block]})
