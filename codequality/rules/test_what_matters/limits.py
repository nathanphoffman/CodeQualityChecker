# Lines of code per test. 6 ** 2 is one test per large function and 6 ** 3 is one per module; either is a little off (90%)
# and the ideal is the middle of the two on a scale of powers of 6: 6 ** 2.5, about one test per 88 lines.
# Rule 10 asks for tests of what matters, not of everything, so this is an expected count rather than full coverage.
LINES_PER_TEST = 6 ** 2.5
