MAX_ITEMS = 6
POWER_BASE = 6

# Going over 6 slides the credit down instead of failing. Distance is measured in powers of 6 above 6 (36 is 1 power over).
# Counts of items: 90% credit at 6 ** 0.5 times over (about 15), about 9% at 36.
ITEM_EDGE_POWER, ITEM_EDGE_CREDIT = 0.5, 0.90

# Function length: the 36 line hard cap (1 power over) keeps half credit.
LENGTH_EDGE_POWER, PARTIAL_CREDIT = 1.0, 0.5

# Past the edge, every further edge power multiplies the credit by this, so being far over is punished hard.
FALLOFF_PER_STEP = 0.1

# Names that look like a function start to the patterns but are control flow.
CONTROL_KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "match", "loop", "else", "with"}

# Receivers don't count as arguments.
IGNORED_ARGUMENT_PREFIXES = ("self", "&self", "&mut self", "mut self", "this:")
