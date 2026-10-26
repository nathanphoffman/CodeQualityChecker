import math

from ....models import MAX_LISTED_OFFENDERS, Result
from .limits import DEPTH_EDGE_CREDIT, DEPTH_EDGE_POWER, FALLOFF_PER_STEP, ITEM_EDGE_CREDIT, ITEM_EDGE_POWER, LENGTH_EDGE_POWER, MAX_ITEMS, PARTIAL_CREDIT, POWER_BASE

def degraded_credit(value, edge_power, edge_credit):
    """Full credit up to 6, then a slide down on a scale of powers of 6: a 7 barely hurts, an 8 a little more.
    edge_credit is the credit at 6 * 6 ** edge_power. Past that, each further edge_power multiplies the credit by FALLOFF_PER_STEP."""

    if value <= MAX_ITEMS:
        return 1.0

    steps = math.log(value / MAX_ITEMS, POWER_BASE) / edge_power

    if steps <= 1:
        return 1 - (1 - edge_credit) * steps

    return edge_credit * FALLOFF_PER_STEP ** (steps - 1)

def strict_credit(value):
    """For counts of items: 90% at 15, 9% at 36, under 1% at 100."""

    return degraded_credit(value, ITEM_EDGE_POWER, ITEM_EDGE_CREDIT)

def function_length_credit(value):
    """Functions may run past 6 lines, but the credit slides: 50% at the 36 line hard cap and about 13% at 100."""

    return degraded_credit(value, LENGTH_EDGE_POWER, PARTIAL_CREDIT)

def depth_credit(value):
    """For call depth: full credit to 6 levels, 90% at 8, about 40% at 9 and under 20% at 10."""

    return degraded_credit(value, DEPTH_EDGE_POWER, DEPTH_EDGE_CREDIT)

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
