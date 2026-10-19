import re

from ...source_code import line_number_at, matching_close
from .limits import CHAIN_METHODS, MAX_CHAIN_LENGTH, MAX_TERNARIES_PER_STATEMENT

CALL_PATTERN = re.compile(r"\.\s*(?P<name>\w+)\s*(?:::<[^>]*>)?\s*(?P<paren>\()")
CHAIN_GAP = re.compile(r"[\s?]*")  # whitespace and Rust's "?" between chained calls
# Rust closures start after "(", "," "=" or "move" as |args|. TypeScript arrows start at "=>".
CLOSURE_START = {"rust": re.compile(r"(?:[(,=]|\bmove)\s*\|[^|\n]*\|"), "typescript": re.compile(r"=>")}
TERNARY = re.compile(r"\s\?\s")  # spaced, so "?." and "??" don't match
STATEMENT = re.compile(r"[^;{}]+")


def method_calls(text):
    """(start, close_paren, name) for every .name(...) call."""
    calls = []
    for match in CALL_PATTERN.finditer(text):
        close = matching_close(text, match.start("paren"))
        if close is not None:
            calls.append((match.start(), close, match.group("name")))
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
    long_heads = [h for h in heads if sum(n in CHAIN_METHODS[language] for n in chain_names(h, by_start, next_start)) >= MAX_CHAIN_LENGTH]
    return [("long_chain", line_number_at(text, head)) for head in long_heads]


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
        start = match.end()
        first = CHAIN_GAP.match(text, start).end()
        braced = first < len(text) and text[first] == "{"
        end = matching_close(text, first) if braced else expression_end(text, start)
        bodies.append((start, end or len(text)))
    return bodies


def nested_closure_hits(text, language):
    bodies = closure_bodies(text, language)
    return [("nested_closure", line_number_at(text, s)) for s, e in bodies if any(s < other < e for other, _ in bodies)]


def ternary_hits(text):
    hits = []
    for statement in STATEMENT.finditer(text):
        found = list(TERNARY.finditer(statement.group()))
        if len(found) > MAX_TERNARIES_PER_STATEMENT:
            hits.append(("chained_ternary", line_number_at(text, statement.start() + found[1].start())))
    return hits
