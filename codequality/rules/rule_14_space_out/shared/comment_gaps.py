def comment_block_gaps(comment_lines, blank_lines, finished_lines):
    """(line numbers counted, line numbers missing a blank line above) for comments that sit on their own line.

    A run of comment lines is one comment, judged by its first line. It needs a blank line above only when the line above
    finishes a statement: the first comment in a block follows the line that opens it, and a comment inside a multi-line
    statement follows part of that statement, so neither is judged. Line numbers start at 1."""

    counted, missing = set(), []

    for number in sorted(comment_lines):
        if number < 2 or number - 1 in comment_lines:
            continue

        if number - 1 in blank_lines:
            counted.add(number)
        elif number - 1 in finished_lines:
            counted.add(number)
            missing.append(number)

    return counted, missing
