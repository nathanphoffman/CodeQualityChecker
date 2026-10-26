from ....language_parsers.tree_sitter.syntax_shapes import VALUE_FIELD
from ..tokens import SYMBOL

class Simple_Statements:
    """Instructions that are a word and a few names or one expression: say, return, exit, leave, drop, procedure, address."""

    def keyword_with_value(self, type_):
        """An instruction word and the optional expression after it: `say`, `return`, `interpret`, `push` and the like."""
        start = self.advance().start
        value = self.expression()

        return self.make(type_, start, [value] if value else [])

    def exit_statement(self):
        start = self.advance().start
        value = self.expression()

        return self.make("exit_statement", start, [value] if value else [], {VALUE_FIELD: [value] if value else []})

    def nop(self):
        start = self.advance().start

        return self.make("nop_statement", start)

    def named_jump(self, type_):
        start = self.advance().start
        names = [self.name_node(self.advance())] if self.peek().kind == SYMBOL else []

        return self.make(type_, start, names)

    def leave(self):
        return self.named_jump("break_statement")

    def iterate(self):
        return self.named_jump("continue_statement")

    def drop(self):
        start = self.advance().start
        names = []

        while self.peek().kind == SYMBOL:
            names.append(self.symbol_node(self.advance()))

        return self.make("drop_statement", start, names)

    def procedure(self):
        start = self.advance().start
        names = []

        if self.word(self.peek()) == "expose":
            self.advance()

            while not self.is_clause_end():
                token = self.advance()
                names += [self.symbol_node(token)] if token.kind == SYMBOL else []

        return self.make("procedure_statement", start, names, {"exposed": names})

    def address(self):
        start = self.advance().start
        environment = [self.name_node(self.advance())] if self.peek().kind == SYMBOL and self.word(self.peek()) != "with" else []
        command = self.expression()

        return self.make("address_statement", start, environment + ([command] if command else []), {"command": [command] if command else []})
