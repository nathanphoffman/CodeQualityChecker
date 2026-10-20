from ...language_parsers.deor.tree import parse_deor, walk_statements

def deor_unsafe_macros(source):
    """[("unsafe_macro", line)] for every unsafe_macro: its variables leak into the code that runs it, which takes explaining."""

    return [("unsafe_macro", statement.first_line) for statement in walk_statements(parse_deor(source).roots)
            if statement.keyword == "unsafe_macro"]
