# Every sign that a comment says "what" the code does adds to a penalty, capped at 1.0. Weights are guesses to tune.
OVERLAP_WEIGHT = 0.8  # times the share of the comment's words that also appear in the code it sits above
SYMBOL_PENALTY = 0.3  # code symbols such as () or => outside backticks
KEYWORD_PENALTY = 0.2  # a code keyword such as if or for anywhere in the comment
OPENER_PENALTY = 0.4  # starts with a what-verb such as "increment" or "loop"
VAGUE_TODO_PENALTY = 0.8  # a TODO that says nothing more
NOISE_PENALTY = 1.0  # empty, or only punctuation
COMMENTED_CODE_PENALTY = 1.0  # the comment is code that was switched off

# A comment that gives a reason keeps only this share of its penalty.
WHY_DISCOUNT = 0.3

# Margin: a penalty up to this much is read as ordinary wording and costs nothing. Beyond it the cost grows from zero.
TOLERANCE = 0.3

# Comments below this confidence of being a "why" are listed as likely "what" comments.
LIKELY_WHAT_BELOW = 0.5
MIN_TODO_WORDS = 3
MIN_COMPLEXITY_NEEDING_COMMENT = 4  # paths through a function; at this many it should have some comment or docstring

TODO_MARKERS = ("todo", "fixme", "xxx")
PUNCTUATION_ONLY = "-=*#~_/!. "
CODE_SYMBOLS = ("()", "{}", "[]", " = ", "==", "!=", "->", "=>", "+=", "-=", ";", "&&", "||")
CODE_KEYWORDS = {"if", "else", "elif", "for", "while", "return", "def", "class", "try", "except", "finally", "raise",
                 "import", "continue", "break", "loop", "match", "switch", "case", "fn", "let", "const", "var",
                 "function", "struct", "enum", "impl", "async", "await", "yield", "lambda"}
WHAT_VERBS = {"increment", "decrement", "loop", "iterate", "initialize", "initialise", "init", "set", "get", "return",
              "create", "call", "check", "define", "declare", "import", "add", "remove", "delete", "print", "update",
              "assign", "convert", "append", "store", "open", "close", "read", "write", "calculate", "compute"}
WHY_PHRASES = ("because", "since", "so that", "to avoid", "otherwise", "workaround", "due to", "must", "needed",
               "need to", "why", "instead", "in case", "unless", "except", "prevents", "ensures", "ensure", "avoid",
               "assumes", "careful", "legacy", "rather than", "would", "might", "can't", "cannot", "won't", "not yet",
               "on purpose", "intentionally", "deliberately", "required")
# Common words that say nothing about overlap between a comment and code.
STOP_WORDS = {"a", "an", "the", "to", "of", "in", "on", "is", "are", "be", "this", "that", "it", "we", "for", "and",
              "or", "with", "as", "at", "by", "from", "if", "while", "so", "then", "all", "each", "any", "our", "us"}

# Comments that talk to tools, not people.
PRAGMA_PREFIXES = ("noqa", "type:", "fmt:", "pylint", "pragma", "isort", "ruff", "nosec", "eslint", "@ts-",
                   "prettier", "istanbul", "clippy", "region", "endregion", "-*-", "noinspection", "usr/bin")
