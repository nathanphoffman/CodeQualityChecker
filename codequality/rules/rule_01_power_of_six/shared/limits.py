MAX_ITEMS = 6
POWER_BASE = 6

# Going over 6 slides the credit down instead of failing. Distance is measured in powers of 6 above 6 (36 is 1 power over).
# Counts of items: 90% credit at 6 ** 0.5 times over (about 15), about 9% at 36.
ITEM_EDGE_POWER, ITEM_EDGE_CREDIT = 0.5, 0.90

# Function length: the 36 line hard cap (1 power over) keeps half credit.
LENGTH_EDGE_POWER, PARTIAL_CREDIT = 1.0, 0.5

# Call depth (main -> child -> child is 3): 6 levels is fine, and the credit slides to 90% at 8 levels, about 40% at 9 and
# under 20% at 10, since a chain much deeper than 6 is hard to hold in your head.
DEPTH_EDGE_POWER, DEPTH_EDGE_CREDIT = 1 / 6, 0.90

# The project's depth score is judged on the share of shortfall across entry points, with only 1 in 6 ** 4 (about 0.08%) free,
# so a single very deep chain among hundreds of shallow ones still hurts: one 15 deep chain among 121 scores about 43%.
DEPTH_FREE_SHARE = 1 / 6 ** 4
DEPTH_SHARE_EDGE_POWER, DEPTH_SHARE_EDGE_CREDIT = 1.0, 0.90

# Past the edge, every further edge power multiplies the credit by this, so being far over is punished hard.
FALLOFF_PER_STEP = 0.1

# Names that look like a function start to the patterns but are control flow.
CONTROL_KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "match", "loop", "else", "with"}

# Receivers don't count as arguments.
IGNORED_ARGUMENT_PREFIXES = ("self", "&self", "&mut self", "mut self", "this:")
