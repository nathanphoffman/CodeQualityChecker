from ....language_parsers.tree_sitter.syntax_shapes import IDENTIFIER
from ..nodes import Node
from ..tokens import END, STRING, SYMBOL, Token

# Words that end an expression wherever it is: `if a then b else c` runs the expressions together on one line.
CLAUSE_WORDS = {"then", "else"}
PLACEHOLDER = "."

class Token_Reader:
    """Steps through the tokens and builds the nodes every other part of the parser uses."""

    def peek(self, ahead=0):
        position = self.index + ahead

        return self.tokens[position] if position < len(self.tokens) else Token(END, "", len(self.map.source), len(self.map.source))

    def advance(self):
        token = self.peek()
        self.index += 1
        self.last_end = token.end

        return token

    def word(self, token):
        return token.text.lower() if token.kind == SYMBOL else ""

    def at_end(self):
        return self.index >= len(self.tokens)

    def is_clause_end(self):
        return self.at_end() or self.peek().kind == END

    def skip_ends(self):
        """Steps over line ends. They are not part of any node, so the end of the last real token is kept."""
        saved = self.last_end

        while not self.at_end() and self.peek().kind == END:
            self.index += 1

        self.last_end = saved

    def make(self, type_, start, children=(), fields=None, end=None):
        return Node(type_, start, self.last_end if end is None else end, self.map, children, fields)

    def fail(self):
        self.ok = False

    def eat_word(self, word):
        if self.word(self.peek()) == word:
            return self.advance()

        self.fail()

        return None

    def name_node(self, token):
        """An identifier node for a symbol (or a quoted label), with its text in lower case."""
        text = token.text.strip("'\"") if token.kind == STRING else token.text

        node = Node(IDENTIFIER, token.start, token.end, self.map)
        node.override = text.lower()

        return node

    def symbol_node(self, token):
        """A plain name is an identifier. A compound name like `stem.i.j` holds the stem and the variables used as tails."""
        stem, _, tail = token.text.partition(".")

        if not tail or not stem or stem[0].isdigit():
            return self.name_node(token) if token.text != PLACEHOLDER else Node("placeholder", token.start, token.end, self.map)

        parts, offset = [Token(SYMBOL, stem, token.start, token.start + len(stem))], token.start + len(stem) + 1

        for piece in tail.split("."):
            parts.append(Token(SYMBOL, piece, offset, offset + len(piece)))
            offset += len(piece) + 1

        names = [self.name_node(part) for part in parts if part.text and not part.text[0].isdigit()]

        return Node("compound_symbol", token.start, token.end, self.map, names, {"declarator": names[:1]})
