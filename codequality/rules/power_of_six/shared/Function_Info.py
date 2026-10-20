from dataclasses import dataclass

@dataclass(frozen=True)
class Function_Info:
    name: str
    argument_count: int
    line_count: int
    line_number: int
