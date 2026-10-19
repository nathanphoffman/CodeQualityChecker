import re

# Clever on purpose: the start of a Deor function or macro, which is indentation based so it has no braces to find.
#   fn: "fn", the return type, the name, then "(" where the parameters start
#   macro: "macro" or "unsafe_macro", then the name (macros take no parameters)
FUNCTION_START = re.compile(r"^(?P<indent>[ \t]*)fn\s+\S+\s+(?P<name>\w+)\s*\((?P<rest>.*)$")
MACRO_START = re.compile(r"^(?P<indent>[ \t]*)(?:unsafe_macro|macro)\s+(?P<name>\w+)\s*$")

TAB_WIDTH = 4

def indent_of(line):
    return len(line[:len(line) - len(line.lstrip())].expandtabs(TAB_WIDTH))

def parameter_text(lines, index, rest):
    """(text between the parentheses of a function header, index of the line they end on). Parameters may wrap onto the next lines."""
    text, depth = "", 1

    while True:
        for char in rest:
            depth += (char == "(") - (char == ")")

            if depth == 0:
                return text, index

            text += char

        index += 1

        if index >= len(lines):
            return text, len(lines) - 1

        rest, text = lines[index], text + " "

def last_body_line(lines, index, header_end):
    """Index of the last line of the block whose header starts on line `index` and ends on `header_end`: deeper indented, ignoring trailing blank lines."""
    last, header_indent = header_end, indent_of(lines[index])

    for later in range(header_end + 1, len(lines)):
        if not lines[later].strip():
            continue

        if indent_of(lines[later]) <= header_indent:
            break

        last = later

    return last

def deor_functions(source, count_arguments):
    """(name, argument_count, line_count, line_number) for every Deor function and macro. A macro counts as a function."""
    lines, found = source.splitlines(), []

    for index, line in enumerate(lines):
        function, macro = FUNCTION_START.match(line), MACRO_START.match(line)
        match = function or macro

        if not match:
            continue

        text, header_end = parameter_text(lines, index, function.group("rest")) if function else ("", index)
        arguments = count_arguments(text)
        name = match.group("name") if function else "macro " + match.group("name")
        found.append((name, arguments, last_body_line(lines, index, header_end) - index + 1, index + 1))

    return found
