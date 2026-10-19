from typing import NamedTuple


class Literal_Use(NamedTuple):
    kind: str  # "number" or "string"
    value: object  # the number, or the text between the quotes
    line_number: int
    in_constant: bool  # already named: inside a SCREAMING_SNAKE definition, a docstring or an f-string
