from dataclasses import dataclass


@dataclass(frozen=True)
class Code_Use:
    """A call, or another construct worth checking, such as an assignment or a string built from parts."""
    name: str  # dotted, like "os.system", "Command.new" or "assign.innerHTML"; "dynamic_string" for built strings
    line_number: int
    text: str  # source with whitespace removed; for "dynamic_string" the upper-case literal parts instead

    names: frozenset  # lower-case variable and attribute names used inside
    line_text: str  # the whole source line, lower-case
