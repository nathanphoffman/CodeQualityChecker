from ...models import MAX_LISTED_OFFENDERS, Result
from .limits import HARD_FUNCTION_LINES, MAX_ITEMS, PARTIAL_CREDIT


def strict_credit(value):
    return 1.0 if value <= MAX_ITEMS else 0.0


def function_length_credit(value):
    """Functions may run past 6 lines up to the hard cap, but only for partial credit."""
    if value <= MAX_ITEMS:
        return 1.0
    return PARTIAL_CREDIT if value <= HARD_FUNCTION_LINES else 0.0


def describe_offenders(measurements, noun):
    over = {label: value for label, value in measurements.items() if value > MAX_ITEMS}
    worst = sorted(over, key=over.get, reverse=True)[:MAX_LISTED_OFFENDERS]
    listed = ", ".join(f"{label} ({over[label]})" for label in worst)
    return f"{len(over)} of {len(measurements)} {noun} over {MAX_ITEMS}: {listed}" if over else ""


def grade(measurements, credit_for, noun):
    """measurements maps a label (file, function, folder) to its count."""
    if not measurements:
        return Result.passed(f"no {noun} found")
    score = sum(credit_for(value) for value in measurements.values()) / len(measurements)
    return Result.scored(score, describe_offenders(measurements, noun))
