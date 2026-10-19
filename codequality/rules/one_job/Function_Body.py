from dataclasses import dataclass


@dataclass(frozen=True)
class Function_Body:
    name: str
    line_number: int
    statement_variables: list  # per top-level statement: the local variables it uses
    branch_count: int

    last_line: int
    has_docstring: bool  # a Python docstring, which counts as the function's explanation
