# Numbers that need no name: zero, one, minus one, and two (halving, pairs, and the like).
ALLOWED_NUMBERS = (-1, 0, 1, 2)

# A string repeated this many times, or more, should be a named constant.
MIN_REPEATS_FOR_CONSTANT = 3

# Shorter strings are separators and punctuation, like ", " and "\n".
MIN_STRING_LENGTH = 4

# A number used in this many files, or more, is a candidate for one shared constant.
MIN_FILES_FOR_SHARED_NUMBER = 2

# Too common to be worth sharing: the allowed numbers, plus 100 (percent).
TRIVIAL_SHARED_NUMBERS = ALLOWED_NUMBERS + (100,)
