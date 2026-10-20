# Rule of 6s: 6 functions make a parent function, 6 of those a subfolder, 6 of those a folder.
# That is about 1296 lines, enough work that using a dependency instead of rewriting it starts to make sense.
LINES_PER_DEPENDENCY = 6 ** 4

# Each extra dependency per LINES_PER_DEPENDENCY lines multiplies the score by this, so one is a 75% (a C).
SCORE_PER_DEPENDENCY = 0.75

# Characters that can be part of a package name; a version, extra or marker starts at anything else.
PACKAGE_NAME_CHARACTERS = "-_."

# Packages from one family, like tree-sitter, tree-sitter-rust and tree-sitter-typescript, are one decision to use a library.
# Two names are related when at least this share of their words (split at - _ . / @) are in both.
RELATED_NAME_SHARE = 0.5

# A family of related packages counts as this power of its size: a family of 3 counts as 3 ** 0.5 = 1.7 dependencies.
FAMILY_SIZE_EXPONENT = 0.5
