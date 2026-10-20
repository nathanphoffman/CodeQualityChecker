import re

from ....source_code import DEOR, blank_out_text
from ..call_depth.text_scan import CALL_PATTERN, calls_in_spans
from ..shared.find_functions import find_functions

# Clever on purpose: a macro is run with `macro_run name` or `unsafe_macro_run name`, and the name is the call.
RUN_PATTERN = re.compile(r"\b(?:unsafe_)?macro_run\s+([A-Za-z_]\w*)")
HASH_COMMENT = re.compile(r"#[^\n]*")  # Deor comments start with "#" as well as "//"

def deor_calls(source):
    """[(name, line_number, called_names)] for every Deor function and macro. A macro is named `macro name`, so the first word goes."""
    text = HASH_COMMENT.sub("", blank_out_text(source))

    return calls_in_spans(find_functions(source, DEOR), text, [CALL_PATTERN, RUN_PATTERN], lambda name: name.split()[-1])
