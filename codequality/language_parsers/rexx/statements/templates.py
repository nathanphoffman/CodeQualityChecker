from ....language_parsers.tree_sitter.syntax_shapes import NAME_FIELD
from ..nodes import Node
from ..reading.reader import PLACEHOLDER
from ..tokens import SYMBOL

class Template_Statements:
    """`arg`, `pull` and `parse`, which fill variables from a template."""

    def template(self, upto=()):
        """The names a template fills in, one `parameter` per comma-separated part. Words in quotes, numbers and (variable) patterns are not names."""
        parts, names, depth = [], [], 0
        start = self.peek().start

        while not self.is_clause_end() and self.word(self.peek()) not in upto:
            token = self.advance()
            depth += (token.text == "(") - (token.text == ")")

            if token.text == "," and depth == 0:
                parts.append(self.parameter(start, names))
                names, start = [], self.peek().start
            elif token.kind == SYMBOL and depth == 0 and token.text != PLACEHOLDER and not token.text[0].isdigit():
                names.append(self.symbol_node(token))

        return parts + [self.parameter(start, names)] if names or not parts else parts

    def parameter(self, start, names):
        end = names[-1].end_byte if names else start

        return Node("parameter", start, end, self.map, names, {NAME_FIELD: names})

    def arg(self):
        start = self.advance().start
        parameters = self.template()

        return self.make("arg_statement", start, parameters)

    def pull(self):
        start = self.advance().start

        # the variable names of every comma-separated part of the template
        targets = [name for part in self.template() for name in part.children]

        return self.make("parse_statement", start, targets, {"target": targets})

    def parse(self):
        start = self.advance().start

        if self.word(self.peek()) == "upper":
            self.advance()

        source = self.word(self.advance())

        if source == "arg":
            return self.make("arg_statement", start, self.template())

        sources = self.parse_source(source)

        # the variable names of every comma-separated part of the template
        targets = [name for part in self.template() for name in part.children]

        return self.make("parse_statement", start, sources + targets, {"target": targets, "source": sources})

    def parse_source(self, source):
        """The value being taken apart: `parse var name`, `parse value expr with`, or nothing for `parse pull`/`parse source`."""

        if source == "var" and self.peek().kind == SYMBOL:
            return [self.symbol_node(self.advance())]

        if source == "value":
            value = self.expression({"with"})
            self.eat_word("with")

            return [value] if value else []

        return []
