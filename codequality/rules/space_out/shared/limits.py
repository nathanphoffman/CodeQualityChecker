# Rule of 6s: a paragraph of code (a run of lines with no blank line in it) is one idea, so about 6 lines at most.
# Scoring reuses the function-length credit from rule 1: full credit up to 6 lines, partial up to 36, none past that.

# One blank line is a break between ideas. More than this in a row is wasted space.
MAX_BLANK_LINES_IN_A_ROW = 1

# A block of imports is one idea however long it is, so a paragraph starting with one of these is not judged.
IMPORT_STARTS = ("import ", "from ", "use ", "export ")
