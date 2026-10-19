from collections import Counter
from typing import NamedTuple


class Cleanup_Findings(NamedTuple):
    """What one file leaves lying around, with the line numbers of each leftover."""
    imports_total: int
    unused_imports: list
    variables_total: int
    unused_variables: list
    statements_total: int
    unreachable: list


class Name_Usage(NamedTuple):
    """Private definitions in one file, and how often every name is mentioned (a definition mentions its own name once)."""
    private_definitions: list  # (name, line number)
    references: Counter
