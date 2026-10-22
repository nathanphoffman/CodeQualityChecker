import re
from typing import NamedTuple

STRING, NUMBER, SYMBOL, OPERATOR, SPECIAL, END, OTHER = "string", "number", "symbol", "operator", "special", "end", "other"
COMMENT = "comment"
SHEBANG = "#!"
COMMENT_OPEN, COMMENT_CLOSE = "/*", "*/"
TOKEN_BEFORE_COMMA = -2  # the comma at the end of a line is last in the list, so the token before it is second to last
CONTINUATION = ","  # a comma at the end of a line carries the clause onto the next line

class Token(NamedTuple):
    kind: str
    text: str
    start: int
    end: int

# Clever on purpose: one pattern that cuts Rexx source into tokens, tried in this order.
#   space: blanks and tabs (a newline is a token of its own, because it ends a clause)
#   string: 'text' or "text" with a doubled quote to put one inside, then an optional x or b for a hex or binary string
#   number: digits with an optional point and exponent, not followed by more symbol characters (`1st` is a symbol)
#   symbol: letters, digits and . _ ! ? $ @ #  (a name, a keyword, or a compound name like stem.i)
#   operator: the longest match first, so `\==` is not read as `\` and `==`
#   special: ( ) ; :
TOKEN_PATTERN = re.compile(r"""
    (?P<space>[ \t\r\f]+)
  | (?P<newline>\n)
  | (?P<string>"(?:""|[^"\n])*"|'(?:''|[^'\n])*')(?P<suffix>[xXbB](?![\w.!?$@#]))?
  | (?P<number>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?(?![\w.!?$@#]))
  | (?P<symbol>[\w.!?$@\#]+)
  | (?P<operator><>|><|\\?(?:==|<<=|>>=|<<|>>|<=|>=|=|<|>)|¬(?:==|=|<|>)|\|\||&&|\*\*|//|[-+*/%&|,\\¬])
  | (?P<special>[();:])
""", re.X)

def comment_end(source, start):
    """Where the comment opening at `start` ends. Rexx comments nest, so each /* inside needs its own */."""
    depth, index = 0, start

    while index < len(source):
        if source.startswith(COMMENT_OPEN, index):
            depth, index = depth + 1, index + len(COMMENT_OPEN)
        elif source.startswith(COMMENT_CLOSE, index):
            depth, index = depth - 1, index + len(COMMENT_CLOSE)

            if depth == 0:
                return index, True
        else:
            index += 1

    return len(source), False

def tokenize(source):
    """(tokens, comments, ok). Comments are tokens of kind COMMENT kept apart; `ok` is False for an unterminated comment or a stray character."""
    tokens, comments, ok, index = [], [], True, 0
    shebang = source.startswith(SHEBANG)

    while index < len(source):
        if shebang and index == 0:
            index = source.find("\n") if "\n" in source else len(source)
        elif source.startswith(COMMENT_OPEN, index):
            end, closed = comment_end(source, index)
            comments.append(Token(COMMENT, source[index:end], index, end))
            ok, index = ok and closed, end
        else:
            index, ok = take_token(source, index, tokens, ok)

    return tokens, comments, ok

def take_token(source, index, tokens, ok):
    """Reads the token at `index`, adds it to `tokens` and returns (the index after it, whether all is well so far)."""
    match = TOKEN_PATTERN.match(source, index)

    if match is None:
        tokens.append(Token(OTHER, source[index], index, index + 1))

        return index + 1, False

    kind = match.lastgroup if match.lastgroup != "suffix" else "string"

    if kind == "newline":
        kind = END
    elif kind == "special" and match.group() == ";":
        kind = END

    if kind != "space" and not (kind == END and ends_after_continuation(tokens, match.group())):
        tokens.append(Token(kind, match.group(), match.start(), match.end()))
    elif ends_after_continuation(tokens, match.group()) and len(tokens) > 1 and tokens[TOKEN_BEFORE_COMMA].kind == OPERATOR and tokens[TOKEN_BEFORE_COMMA].text != CONTINUATION:
        tokens.pop()  # `1 +,` then a new line: the comma only carries the clause over, it is not an argument separator

    return match.end(), ok

def ends_after_continuation(tokens, text):
    """A newline right after a comma does not end the clause."""

    return text == "\n" and bool(tokens) and tokens[-1].kind == OPERATOR and tokens[-1].text == CONTINUATION

def text_spans(source):
    """[(start, end)] of every comment and string, so other code can blank them out."""
    tokens, comments, _ = tokenize(source)

    return sorted([(token.start, token.end) for token in tokens if token.kind == STRING] + [(token.start, token.end) for token in comments])
