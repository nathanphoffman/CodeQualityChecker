from dataclasses import dataclass
from typing import NamedTuple

class Statement_Shape(NamedTuple):
    """One statement with its variable names and literal values removed, so renamed copies look identical."""
    shape: str
    size: int  # how many syntax nodes it has
    first_line: int
    last_line: int

@dataclass(frozen=True)
class Function_Shape:
    name: str
    line_number: int
    sequences: list  # lists of Statement_Shape: the function body first, then each nested block
