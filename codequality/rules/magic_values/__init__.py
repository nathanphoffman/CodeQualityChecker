"""Rule 7: No magic numbers. Numbers and repeated strings should be named constants."""
from collections import Counter

from ...models import MAX_LISTED_OFFENDERS, Result
from ...registry import rule
from .find_literals import literals_in_project
from .limits import ALLOWED_NUMBERS, MIN_REPEATS_FOR_CONSTANT, MIN_STRING_LENGTH
from .Literal_Use import KIND_NUMBER, KIND_STRING


@rule("RULE-07-MAGIC-NUMBERS", "Numbers are named constants")
def check_magic_numbers(project):
    numbers = [(label, use) for label, use in literals_in_project(project) if use.kind == KIND_NUMBER]
    if not numbers:
        return Result.passed("no numbers found")
    magic = [(label, use) for label, use in numbers if not use.in_constant and use.value not in ALLOWED_NUMBERS]

    listed = ", ".join(f"{label}:{use.line_number} ({use.value})" for label, use in magic[:MAX_LISTED_OFFENDERS])
    message = f"{len(magic)} of {len(numbers)} numbers are not named: {listed}" if magic else ""
    return Result.scored(1 - len(magic) / len(numbers), message)


@rule("RULE-07-REPEATED-STRINGS", "Strings used again and again are named constants")
def check_repeated_strings(project):
    strings = [use.value for _, use in literals_in_project(project)
               if use.kind == KIND_STRING and not use.in_constant and len(use.value) >= MIN_STRING_LENGTH]
    if not strings:
        return Result.passed("no strings found")

    counts = Counter(strings)
    repeated = {text: count for text, count in counts.items() if count >= MIN_REPEATS_FOR_CONSTANT}
    listed = ", ".join(f'"{text}" ({count}x)' for text, count in Counter(repeated).most_common(MAX_LISTED_OFFENDERS))
    message = f"{len(repeated)} strings repeat {MIN_REPEATS_FOR_CONSTANT}+ times: {listed}" if repeated else ""
    return Result.scored(1 - sum(repeated.values()) / len(strings), message)
