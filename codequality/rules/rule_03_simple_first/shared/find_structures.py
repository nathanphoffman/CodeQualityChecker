import re

from ....source_code import NAME_GROUP, PAREN_GROUP, line_number_at, matching_close
from .limits import CHAIN_METHODS, MAX_CHAIN_LENGTH, MAX_TERNARIES_PER_STATEMENT

CALL_PATTERN = re.compile(r"\.\s*(?P<name>\w+)\s*(?:::<[^>]*>)?\s*(?P<paren>\()")  # a ".", the method name, optional ::<generics>, then the "(" of its call
CHAIN_GAP = re.compile(r"[\s?]*")  # whitespace and Rust's "?" between chained calls

# Rust closures start after "(", "," "=" or "move" as |args|. TypeScript arrows start at "=>".
# where each language's closures start; a pattern that never matches, `(?!)`, means the language has none
CLOSURE_START = {"rust": re.compile(r"(?:[(,=]|\bmove)\s*\|[^|\n]*\|"), "typescript": re.compile(r"=>"), "csharp": re.compile(r"=>"), "hare": re.compile(r"(?!)"), "c": re.compile(r"(?!)"), "mojo": re.compile(r"(?!)"),  # these have no closures, so their patterns never match
                 "fortran": re.compile(r"(?!)"), "rexx": re.compile(r"(?!)"),  # never matches: no closures
                 "go": re.compile(r"(?:[=(,:]|\breturn|\bgo|\bdefer)\s*func\s*\([^)]*\)[^{;]*(?=\{)")}  # Go: a `func(args)` after one of those, stopping at its "{"  # Rust: `(`, `,`, `=` or `move` then |args|; TypeScript: the arrow

# React's built-in hooks take a callback by design, so an arrow handed straight to one is not clever
REACT_HOOKS = ("useState", "useReducer", "useEffect", "useLayoutEffect", "useInsertionEffect", "useMemo", "useCallback", "useImperativeHandle", "useSyncExternalStore")
HOOK_CALLBACK = re.compile(r"\b(?:" + "|".join(REACT_HOOKS) + r")\s*(?:<[^()]*>)?\s*\(\s*(?:async\s+)?(?:\([^()]*\)|\w+)\s*$")  # a hook's "(" then the arrow's parameters, ending where "=>" starts

TERNARY = re.compile(r"\s\?\s")  # spaced, so "?." and "??" don't match
STATEMENT = re.compile(r"[^;{}]+")  # one statement: everything up to the next ";" or brace

def method_calls(text):
    """(start, close_paren, name) for every .name(...) call."""
    calls = []

    for match in CALL_PATTERN.finditer(text):
        close = matching_close(text, match.start(PAREN_GROUP))

        if close is not None:
            calls.append((match.start(), close, match.group(NAME_GROUP)))

    return calls

def chain_names(start, by_start, next_start):
    names = []

    while start in by_start:
        names.append(by_start[start])
        start = next_start[start]

    return names

def long_chain_hits(text, language):
    calls = method_calls(text)
    by_start = {start: name for start, _, name in calls}
    next_start = {start: CHAIN_GAP.match(text, close + 1).end() for start, close, _ in calls}
    continued = set(next_start.values())
    heads = [start for start in by_start if start not in continued]

    hits = []

    for head in heads:
        names = chain_names(head, by_start, next_start)

        if len([name for name in names if name in CHAIN_METHODS[language]]) >= MAX_CHAIN_LENGTH:
            hits.append(("long_chain", line_number_at(text, head)))

    return hits

def expression_end(text, start):
    """Where a closure body without braces stops: an unmatched closer, or "," / ";" at the top level."""
    depth = 0

    for index in range(start, len(text)):
        depth += (text[index] in "([{") - (text[index] in ")]}")

        if depth < 0 or (depth == 0 and text[index] in ",;"):
            return index

    return len(text)

def closure_bodies(text, language):
    bodies = []

    for match in CLOSURE_START[language].finditer(text):
        if language == "typescript" and HOOK_CALLBACK.search(text, max(0, match.start() - 200), match.start()):
            continue

        start = match.end()
        first = CHAIN_GAP.match(text, start).end()
        braced = first < len(text) and text[first] == "{"
        end = matching_close(text, first) if braced else expression_end(text, start)
        bodies.append((start, end or len(text)))

    return bodies

def nested_closure_hits(text, language):
    bodies = closure_bodies(text, language)
    hits = []

    for start, end in bodies:
        starts_inside = [other for other, _ in bodies if start < other < end]

        if starts_inside:
            hits.append(("nested_closure", line_number_at(text, start)))

    return hits

def ternary_hits(text):
    hits = []

    for statement in STATEMENT.finditer(text):
        found = list(TERNARY.finditer(statement.group()))

        if len(found) > MAX_TERNARIES_PER_STATEMENT:
            hits.append(("chained_ternary", line_number_at(text, statement.start() + found[1].start())))

    return hits
