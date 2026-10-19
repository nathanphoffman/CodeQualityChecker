import math

# Project size is judged in powers of 6: a project of 6 ** x lines. Everything up to 6 ** 4 (1296 lines) is fine.
BASE = 6
FULL_CREDIT_POWER = 4
EDGE_POWER = 6

# The scores that anchor the curve: 90% at 6 ** 6 (46656 lines, where n ** n with n = 6 puts the "roughly 6" in rule 13),
# almost a failing grade at 6 ** 7, and nearly nothing at 6 ** 8.
SCORE_AT_EDGE = 0.90
SCORE_AT_EDGE_PLUS_ONE = 0.62
SCORE_AT_EDGE_PLUS_TWO = 0.03

# Past the edge the score is SCORE_AT_EDGE * exp(-DECAY * (power - EDGE_POWER) ** STEEPNESS). Both numbers come from fitting the
# curve through the two anchors above: DECAY is the loss over the first power past the edge, and STEEPNESS makes the second
# power lose far more than the first, so the score falls like a rock.
DECAY = -math.log(SCORE_AT_EDGE_PLUS_ONE / SCORE_AT_EDGE)
STEEPNESS = math.log2(-math.log(SCORE_AT_EDGE_PLUS_TWO / SCORE_AT_EDGE) / DECAY)
