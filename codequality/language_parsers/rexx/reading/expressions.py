from ....language_parsers.tree_sitter.syntax_shapes import CALL_EXPRESSION
from ..nodes import Node
from ..tokens import NUMBER, OPERATOR, SPECIAL, STRING, SYMBOL
from .reader import CLAUSE_WORDS

COMPARISONS = {"=", "==", "\\=", "\\==", "¬=", "¬==", "<>", "><", "<", ">", "<=", ">=", "\\<", "\\>", "¬<", "¬>", "<<", ">>", "<<=", ">>=", "\\<<", "\\>>"}

# Operators by how tightly they bind, loosest first. Concatenation sits between comparing and adding.
LEVELS = [("boolean_operator", {"|", "&&"}), ("boolean_operator", {"&"}), ("binary_expression", COMPARISONS),
          ("concatenation_expression", {"||"}), ("binary_expression", {"+", "-"}), ("binary_expression", {"*", "/", "%", "//"}),
          ("binary_expression", {"**"})]

PREFIX_OPERATORS = {"\\", "¬", "+", "-"}
CONCAT_LEVEL = 3

class Expression_Reader:
    """Reads expressions: operators by how tightly they bind, calls, strings, numbers and names."""

    def starts_term(self, token):
        if token.kind in (STRING, NUMBER):
            return True

        return (token.kind == SYMBOL and token.text.lower() not in self.stops) or (token.kind == SPECIAL and token.text == "(")

    def expression(self, stops=()):
        """One expression, or None when there is none here. `stops` are extra words that end it (`to`, `by`, `while`...)."""
        saved, self.stops = self.stops, frozenset(CLAUSE_WORDS | set(stops))

        try:
            return self.level(0) if self.starts_operand(self.peek()) else None
        finally:
            self.stops = saved

    def starts_operand(self, token):
        return self.starts_term(token) or (token.kind == OPERATOR and token.text in PREFIX_OPERATORS)

    def level(self, depth):
        if depth == len(LEVELS):
            return self.prefix()

        type_, operators = LEVELS[depth]
        start = self.peek().start
        left = self.level(depth + 1)

        while True:
            token = self.peek()
            implicit = depth == CONCAT_LEVEL and self.starts_term(token)  # two terms side by side are joined

            if token.kind == OPERATOR and token.text in operators:
                self.advance()
            elif not implicit:
                return left

            right = self.level(depth + 1)
            fields = {"operator": [Node("operator", token.start, token.end, self.map)]} if not implicit and type_ != "concatenation_expression" else {}
            left = self.make(type_, start, [left, right], fields)

    def prefix(self):
        token = self.peek()

        if token.kind == OPERATOR and token.text in PREFIX_OPERATORS:
            self.advance()
            operand = self.prefix()

            return self.make("unary_expression", token.start, [operand], {"operator": [Node("operator", token.start, token.end, self.map)]})

        return self.term()

    def term(self):
        token = self.peek()

        if token.kind == SPECIAL and token.text == "(":
            return self.parenthesized()

        if token.kind not in (STRING, NUMBER, SYMBOL):
            self.fail()
            self.advance()

            return self.make("error", token.start)

        self.advance()
        following = self.peek()

        if following.kind == SPECIAL and following.text == "(" and following.start == token.end:
            return self.call_expression(token)

        return self.literal(token)

    def literal(self, token):
        if token.kind == NUMBER:
            return Node("number", token.start, token.end, self.map)

        if token.kind == STRING:
            is_hex = token.text[-1] in "xXbB"

            return Node("hex_string" if is_hex else "string", token.start, token.end, self.map)

        return self.symbol_node(token)

    def parenthesized(self):
        start = self.advance().start
        saved, self.stops = self.stops, frozenset()
        inner = self.level(0) if self.starts_operand(self.peek()) else None
        self.stops = saved

        if self.peek().text == ")":
            self.advance()
        else:
            self.fail()

        return self.make("parenthesized_expression", start, [inner] if inner else [])

    def call_expression(self, name_token):
        function = self.name_node(name_token)
        arguments = self.arguments(self.advance().start)

        return self.make(CALL_EXPRESSION, name_token.start, [function, arguments], {"function": [function], "arguments": [arguments]})

    def arguments(self, start):
        """The expressions between ( and ), up to the matching close."""
        found = []
        saved, self.stops = self.stops, frozenset()

        while not self.is_clause_end() and self.peek().text != ")":
            found += [self.level(0)] if self.starts_operand(self.peek()) else []

            if self.peek().text == ",":
                self.advance()
            elif self.peek().text != ")":
                self.fail()

                break

        self.stops = saved

        if self.peek().text == ")":
            self.advance()
        else:
            self.fail()

        return self.make("arguments", start, found)
