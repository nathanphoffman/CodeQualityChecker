import re
from collections import Counter

from ...models import MAX_LISTED_OFFENDERS, Result
from .limits import ALLOWED_ACRONYMS, MIN_NAME_LENGTH

# Clever on purpose: splits a name into words by casing, so both camelCase and Pascal_Snake work.
#   [A-Z]+(?![a-z])  an uppercase run that isn't the start of a Capitalized word (HTTP in parseHTTPResponse)
#   [A-Z]?[a-z]+     a normal word, optionally capitalized
#   [0-9]+           a number
WORD_PATTERN = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+")

def is_too_short(name):
    return len(name.strip("_")) < MIN_NAME_LENGTH

def has_unknown_acronym(name):
    if name.isupper():  # SCREAMING_SNAKE constants are all capitals on purpose
        return False

    words = WORD_PATTERN.findall(name)

    return any(len(word) > 1 and word.isupper() and word not in ALLOWED_ACRONYMS for word in words)

def describe_offenders(offenders, total, complaint):
    if not offenders:
        return ""

    listed = ", ".join(f"{name} ({count})" for name, count in offenders.most_common(MAX_LISTED_OFFENDERS))

    return f"{sum(offenders.values())} of {total} names {complaint}: {listed}"

def grade_names(names, is_offender, complaint):
    if not names:
        return Result.passed("no names found")

    offenders = Counter(name for name in names if is_offender(name))
    score = 1 - sum(offenders.values()) / len(names)

    return Result.scored(score, describe_offenders(offenders, len(names), complaint))
