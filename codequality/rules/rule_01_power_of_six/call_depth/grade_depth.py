from ....models import Result
from ..shared.limits import DEPTH_FREE_SHARE, DEPTH_SHARE_EDGE_CREDIT, DEPTH_SHARE_EDGE_POWER, MAX_ITEMS
from ..shared.scoring import degraded_credit, depth_credit, describe_offenders

def grade_depths(depths):
    """depths maps an entry point to its chain depth. Every chain's shortfall is averaged, and that share is judged steeply
    so a few very deep chains hurt a lot, however many shallow entry points sit beside them."""

    if not depths:
        return Result.passed("no functions found")

    share = sum(1 - depth_credit(depth) for depth in depths.values()) / len(depths)
    score = degraded_credit(share / DEPTH_FREE_SHARE * MAX_ITEMS, DEPTH_SHARE_EDGE_POWER, DEPTH_SHARE_EDGE_CREDIT)

    return Result.scored(score, describe_offenders(depths, "entry points"))
