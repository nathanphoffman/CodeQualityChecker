from dataclasses import dataclass

@dataclass(frozen=True)
class Function_Body:
    name: str
    line_number: int
    statement_variables: list  # per top-level statement: the local variables it uses
    branch_count: int

    last_line: int
    has_docstring: bool  # a Python docstring, which counts as the function's explanation
    max_nesting: int = 0  # the most blocks (if, loop, try, switch) inside one another in the function
    boolean_parameters: int = 0
    parameter_count: int = 0
