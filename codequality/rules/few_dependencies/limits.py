# Rule of 6s: 6 functions make a parent function, 6 of those a subfolder, 6 of those a folder.
# That is about 1296 lines, enough work that using a dependency instead of rewriting it starts to make sense.
LINES_PER_DEPENDENCY = 6 ** 4

# Each extra dependency per LINES_PER_DEPENDENCY lines multiplies the score by this, so one is a 75% (a C).
SCORE_PER_DEPENDENCY = 0.75

# Characters that can be part of a package name; a version, extra or marker starts at anything else.
PACKAGE_NAME_CHARACTERS = "-_."
