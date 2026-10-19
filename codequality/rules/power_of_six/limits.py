MAX_ITEMS = 6
HARD_FUNCTION_LINES = 36
PARTIAL_CREDIT = 0.5

# Names that look like a function start to the patterns but are control flow.
CONTROL_KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "match", "loop", "else", "with"}

# Receivers don't count as arguments.
IGNORED_ARGUMENT_PREFIXES = ("self", "&self", "&mut self", "mut self", "this:")
