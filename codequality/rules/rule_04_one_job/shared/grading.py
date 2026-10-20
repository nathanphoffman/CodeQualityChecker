from ....models import MAX_LISTED_OFFENDERS, Result

def grade_bodies(bodies, is_offender, complaint):
    """bodies maps a label to a Function_Body. Score is the share of functions that are not offenders."""

    if not bodies:
        return Result.passed("no functions found")

    offenders = [label for label, body in bodies.items() if is_offender(body)]
    listed = ", ".join(offenders[:MAX_LISTED_OFFENDERS])

    message = f"{len(offenders)} of {len(bodies)} functions {complaint}: {listed}" if offenders else ""

    return Result.scored(1 - len(offenders) / len(bodies), message)
