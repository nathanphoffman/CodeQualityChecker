from typing import NamedTuple

class Error_Handler(NamedTuple):
    """A place where code deals with an error: catches it, raises one, or passes it up."""
    line_number: int
    is_catch: bool  # a handler that receives an error, as opposed to code that raises or passes one up
    is_loud: bool  # re-raises, logs, prints, exits or uses the error; always true for code that raises
    is_broad: bool  # catches anything (bare except, Exception, any TypeScript catch), not one expected kind
