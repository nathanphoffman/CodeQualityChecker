# Rule of 6s: one clever line hides about as much as 6 normal lines, so it is penalized 6 times over.
CLEVER_LINE_WEIGHT = 6
MAX_CHAIN_LENGTH = 3
MAX_TERNARIES_PER_STATEMENT = 1

# A comment on the same line, or starting the line above.
SAME_LINE_COMMENTS = {"python": ("#",), "rust": ("//", "/*"), "typescript": ("//", "/*"), "hare": ("//",), "c": ("//", "/*"),
                      "go": ("//", "/*"), "deor": ("#", "//")}
LINE_ABOVE_COMMENTS = {"python": ("#",), "rust": ("//", "/*", "*"), "typescript": ("//", "/*", "*"), "hare": ("//",), "c": ("//", "/*", "*"),
                      "go": ("//", "/*", "*"), "deor": ("#", "//")}

# Methods that take a function; three or more in one chain is a pipeline that's hard to read.
CHAIN_METHODS = {
    "rust": {"map", "filter", "filter_map", "flat_map", "flatten", "fold", "scan", "and_then",
             "map_err", "unwrap_or_else", "zip", "take_while", "skip_while", "find_map"},
    "typescript": {"map", "filter", "reduce", "reduceRight", "flatMap", "then", "catch", "finally"},
    "hare": set(),  # Hare, C and Go have no method chains to speak of
    "c": set(),
    "go": set(),
}
