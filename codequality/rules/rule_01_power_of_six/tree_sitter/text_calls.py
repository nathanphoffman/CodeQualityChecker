from ....source_code import blank_out_text
from ..call_depth.text_scan import CALL_PATTERN, calls_in_spans
from ..shared.find_functions import find_functions

def text_calls(source, language):
    """[(name, line_number, called_names)] for Rust and TypeScript, found by pattern since they are not parsed here."""

    return calls_in_spans(find_functions(source, language), blank_out_text(source), [CALL_PATTERN], lambda name: name)
