# Functions with fewer statements than this can't meaningfully split into separate jobs.
MIN_STATEMENTS_TO_CHECK = 4
MAX_JOB_GROUPS = 1

# Rule of 6s: at most 6 paths through a function. Complexity is 1 plus the number of branches.
MAX_COMPLEXITY = 6

# A function name containing one of these as a word says it does more than one thing.
JOINING_WORDS = {"and", "or", "then"}

# Blocks (if, loops, try, switch) inside one another: more than 3 deep is hard to follow.
MAX_NESTING = 3
