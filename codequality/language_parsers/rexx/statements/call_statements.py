from ..tokens import STRING, SYMBOL

CONDITION_WORDS = {"error", "failure", "halt", "notready", "novalue", "syntax", "lostdigits", "nostring"}

class Call_Statements:
    """`call` and `signal`, including the `on`/`off` forms that set up a trap for a condition."""

    def trap(self, start, type_):
        """`signal on error name handler` and `call off halt`: the condition and the label it jumps to. With no `name`, the label is the condition's own name."""
        self.advance()
        condition = self.advance() if self.peek().kind == SYMBOL else None
        labels = [self.name_node(condition)] if condition and self.word(condition) in CONDITION_WORDS else []

        if self.word(self.peek()) == "name" and self.peek(1).kind in (SYMBOL, STRING):
            self.advance()
            labels = [self.name_node(self.advance())]

        return self.make(type_, start, labels)

    def call(self):
        start = self.advance().start

        if self.word(self.peek()) in ("on", "off") and self.peek(1).kind == SYMBOL and self.word(self.peek(1)) in CONDITION_WORDS:
            return self.trap(start, "trap_statement")

        if self.peek().kind not in (SYMBOL, STRING):
            self.fail()

            return self.make("call_statement", start)

        function = self.name_node(self.advance())
        arguments = self.call_arguments()

        return self.make("call_statement", start, [function, arguments], {"function": [function], "arguments": [arguments]})

    def call_arguments(self):
        """`call name a, b, c`: expressions separated by commas up to the end of the clause."""
        start, found = self.peek().start, []

        while not self.is_clause_end():
            found += [self.level(0)] if self.starts_operand(self.peek()) else []

            if self.peek().text == ",":
                self.advance()
            elif not self.is_clause_end():
                self.fail()
                self.advance()

        return self.make("arguments", start, found, end=self.last_end if found else start)

    def signal(self):
        start = self.advance().start

        if self.word(self.peek()) in ("on", "off"):
            return self.trap(start, "trap_statement")

        if self.word(self.peek()) == "value":
            self.advance()
            target = self.expression()

            return self.make("goto_statement", start, [target] if target else [])

        label = self.symbol_node(self.advance()) if self.peek().kind in (SYMBOL, STRING) else None

        return self.make("goto_statement", start, [label] if label else [])
