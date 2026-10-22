import warnings
from functools import partial

from .nodes import Node, Source_Map
from .tokens import COMMENT, END, NUMBER, OPERATOR, SPECIAL, STRING, SYMBOL, Token, tokenize

# Words that end an expression wherever it is: `if a then b else c` runs the expressions together on one line.
CLAUSE_WORDS = {"then", "else"}
CONDITION_WORDS = {"error", "failure", "halt", "notready", "novalue", "syntax", "lostdigits", "nostring"}
COMPARISONS = {"=", "==", "\\=", "\\==", "¬=", "¬==", "<>", "><", "<", ">", "<=", ">=", "\\<", "\\>", "¬<", "¬>", "<<", ">>", "<<=", ">>=", "\\<<", "\\>>"}
PLACEHOLDER = "."
LABEL_MARK = ":"

# Operators by how tightly they bind, loosest first. Concatenation sits between comparing and adding.
LEVELS = [("boolean_operator", {"|", "&&"}), ("boolean_operator", {"&"}), ("binary_expression", COMPARISONS),
          ("concatenation_expression", {"||"}), ("binary_expression", {"+", "-"}), ("binary_expression", {"*", "/", "%", "//"}),
          ("binary_expression", {"**"})]

PREFIX_OPERATORS = {"\\", "¬", "+", "-"}
CONCAT_LEVEL = 3

class Rexx_Parser:
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

    # --- reading tokens

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

    # --- names

    def name_node(self, token):
        """An identifier node for a symbol (or a quoted label), with its text in lower case."""
        text = token.text.strip("'\"") if token.kind == STRING else token.text

        return Node("identifier", token.start, token.end, self.map, text=text.lower())

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

    # --- expressions

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

        return self.make("call_expression", name_token.start, [function, arguments], {"function": [function], "arguments": [arguments]})

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

    # --- simple instructions

    def keyword_with_value(self, type_):
        """An instruction word and the optional expression after it: `say`, `return`, `interpret`, `push` and the like."""
        start = self.advance().start
        value = self.expression()

        return self.make(type_, start, [value] if value else [])

    def exit_statement(self):
        start = self.advance().start
        value = self.expression()

        return self.make("exit_statement", start, [value] if value else [], {"value": [value] if value else []})

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

    # --- calls and traps

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

    # --- templates: arg, parse and pull

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

        return Node("parameter", start, end, self.map, names, {"name": names})

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

    # --- control flow

    def statement_or_block(self):
        """The one instruction after `then`, `else` or `when ... then`, which can be a `do` group."""
        self.skip_ends()

        return self.statement()

    def if_statement(self):
        start = self.advance().start
        condition = self.expression({"then"})
        self.skip_ends()
        self.eat_word("then")
        consequence = self.statement_or_block()
        position, end = self.index, self.last_end
        self.skip_ends()

        if self.word(self.peek()) == "else":
            self.advance()
            alternative = self.statement_or_block()

            return self.make("if_statement", start, [condition, consequence, alternative],
                             {"condition": [condition], "consequence": [consequence], "alternative": [alternative]})

        self.index, self.last_end = position, end

        return self.make("if_statement", start, [condition, consequence], {"condition": [condition], "consequence": [consequence]})

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

    def block_until_end(self, start, stop_words=("end",)):
        """The statements up to `end` (or another stop word), then the `end` and the name some programmers write after it."""
        statements = self.statements(set(stop_words), in_routine=False)

        return statements

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
        body = self.statement_or_block()

        return self.make("when_clause", start, [condition, body], {"condition": [condition], "body": [body]})

    def otherwise(self):
        start = self.advance().start
        statements = self.statements({"end"}, in_routine=False)
        block = self.make("block", start, statements, end=statements[-1].end_byte if statements else self.last_end)

        return self.make("otherwise_clause", start, [block], {"body": [block]})

    # --- statements, routines and the whole file

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

        return self.make("routine_definition", start, [name, body], {"name": [name], "body": [body], "parameters": parameters},
                         end=statements[-1].end_byte if statements else self.last_end)

    def body_block(self, start, statements):
        first = statements[0].start_byte if statements else start

        return Node("block", first, statements[-1].end_byte if statements else first, self.map, statements)

    def parameters_of(self, statements, start):
        """The `parameters` node for the first `arg` or `parse arg` of a routine, or none."""
        found = next((statement for statement in statements if statement.type == "arg_statement"), None)

        if found is None:
            return []

        node = Node("parameters", found.start_byte, found.end_byte, self.map)
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
