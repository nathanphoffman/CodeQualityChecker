import re

from ....source_code import FORTRAN, blank_out_text
from ..call_depth.text_scan import CALL_PATTERN, calls_in_spans
from ..shared.find_functions import find_functions

FORTRAN_CALL_PATTERN = re.compile(r"\bcall\s+(\w+)")  # `call name` with no "(" when it takes no arguments

def text_calls(source, language):
    """[(name, line_number, called_names)] for the languages that are not parsed into a call graph by their own parser."""
    text = blank_out_text(source, language)
    patterns = [CALL_PATTERN]

    if language == FORTRAN:
        text, patterns = text.lower(), patterns + [FORTRAN_CALL_PATTERN]  # Fortran names ignore case

    return calls_in_spans(find_functions(source, language), text, patterns, lambda name: name)
