import re

from ....language_parsers.deor.tree import parse_deor, walk_statements
from ....language_parsers.deor.words import blank_strings

# Clever on purpose: a call is a name followed straight away by "(". Words like `if (x)` and `return (a, b)` are not calls.
CALL_START = re.compile(r"(?<![\w.])(?P<name>[A-Za-z_]\w*)\(")
NOT_CALLS = {"if", "return", "for", "in", "and", "or", "not", "is", "with", "avow", "move", "else"}
JOIN_FUNCTIONS = {"s_join", "s_join_with"}

def closing_bracket(text, open_index):
    depth = 0

    for index in range(open_index, len(text)):
        depth += (text[index] == "(") - (text[index] == ")")

        if depth == 0:
            return index

    return len(text)

def names_in(text):
    # every word that looks like a name (a letter or underscore, then word characters), with string contents blanked first
    return frozenset(word.lower() for word in re.findall(r"[A-Za-z_]\w*", blank_strings(text)))

def deor_calls(source):
    """[(name, line, squashed text, lower-case names used inside)] for every call in Deor code, and the pieces of built strings."""
    found = []

    for statement in walk_statements(parse_deor(source).roots):
        text = statement.text
        masked = blank_strings(text)

        for hit in CALL_START.finditer(masked):
            if hit.group("name") in NOT_CALLS:
                continue

            end = closing_bracket(masked, hit.end() - 1)
            call = text[hit.start():end + 1]
            found.append((hit.group("name"), statement.first_line, "".join(call.split()), names_in(call)))

            if hit.group("name") in JOIN_FUNCTIONS:
                found.append(("dynamic_string", statement.first_line, built_text(call), names_in(call)))

    return found

def built_text(call):
    """The text pieces of the string literals inside an s_join(...) call, upper-case, when a variable is joined in too."""
    # the text inside each double-quoted string; (?:\\.|[^"\\])* reads an escaped character or any character that isn't a quote or backslash
    pieces = re.findall(r'"((?:\\.|[^"\\])*)"', call)
    # true when a name is left after removing the strings and the s_join helper names, meaning a variable is part of the call
    has_variable = bool(re.search(r"[A-Za-z_]\w*", re.sub(r'"(?:\\.|[^"\\])*"', "", call).replace("s_join_with", "").replace("s_join", "")))

    return " ".join(pieces).strip().upper() if has_variable else ""
