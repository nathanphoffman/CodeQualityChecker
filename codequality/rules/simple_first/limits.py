MAX_CHAIN_LENGTH = 3
MAX_TERNARIES_PER_STATEMENT = 1
MAX_CLEVER_PER_100_LINES = 5
LINES_PER_DENSITY_UNIT = 100

# A comment on the same line, or starting the line above.
SAME_LINE_COMMENTS = {"python": ("#",), "rust": ("//", "/*"), "typescript": ("//", "/*")}
LINE_ABOVE_COMMENTS = {"python": ("#",), "rust": ("//", "/*", "*"), "typescript": ("//", "/*", "*")}

# Methods that take a function; three or more in one chain is a pipeline that's hard to read.
CHAIN_METHODS = {
    "rust": {"map", "filter", "filter_map", "flat_map", "flatten", "fold", "scan", "and_then",
             "map_err", "unwrap_or_else", "zip", "take_while", "skip_while", "find_map"},
    "typescript": {"map", "filter", "reduce", "reduceRight", "flatMap", "then", "catch", "finally"},
}
