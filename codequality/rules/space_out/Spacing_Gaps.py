from typing import NamedTuple

class Spacing_Gaps(NamedTuple):
    """Where one file is missing a blank line. Each `missing` list holds the line numbers a blank line belongs above."""
    before_control_total: int  # control statements, returns and definitions that are not first in their block
    before_control_missing: list
    after_block_total: int  # statements that follow a multi-line statement in the same block
    after_block_missing: list
