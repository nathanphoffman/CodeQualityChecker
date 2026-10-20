import re

# Clever on purpose: finds a call without a real parser.
#   a name, optional spaces, then "(" (the "(" is not part of the name)
CALL_PATTERN = re.compile(r"\b([A-Za-z_]\w*)\s*\(")

def last_line_of(info):
    return info.line_number + info.line_count - 1

def nested_spans(info, infos):
    """Line ranges of the functions written inside this one, whose calls belong to them and not to it."""

    return [(other.line_number, last_line_of(other)) for other in infos
            if other.line_number > info.line_number and last_line_of(other) <= last_line_of(info)]

def calls_on_lines(info, infos, lines, patterns, bare_name):
    """Names called on the lines that belong to this function itself. Its own name on its header line is the definition."""
    nested = nested_spans(info, infos)
    called = set()

    for number in range(info.line_number, last_line_of(info) + 1):
        if any(first <= number <= last for first, last in nested):
            continue

        for pattern in patterns:
            called.update(name for name in pattern.findall(lines[number - 1]) if number != info.line_number or name != bare_name)

    return called

def calls_in_spans(infos, text, patterns, bare_name_of):
    """[(name, line_number, called_names)] for each function, reading the text between its first and last line."""
    lines = text.split("\n")

    return [(bare_name_of(info.name), info.line_number,
             frozenset(calls_on_lines(info, infos, lines, patterns, bare_name_of(info.name)))) for info in infos]
