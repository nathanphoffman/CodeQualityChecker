from .tree import parse_deor, walk_statements

WRAPPER_HEADER = "fn deor_rust_block() {"
WRAPPER_LINES_ABOVE = 1  # the header line, so line N of a wrapped block is line first_line + N - 1 - WRAPPER_LINES_ABOVE of the file

def rust_statements(source):
    return [statement for statement in walk_statements(parse_deor(source).roots) if statement.rust_lines]

def rust_blocks(source):
    """[(first_line, rust source)] for every `rust` block. The block is wrapped in a function so it parses as Rust."""
    blocks = []

    for statement in rust_statements(source):
        first, last = statement.rust_lines[0].number, statement.rust_lines[-1].number
        text = {line.number: line.code for line in statement.rust_lines}
        body = "\n".join(text.get(number, "") for number in range(first, last + 1))
        blocks.append((first, WRAPPER_HEADER + "\n" + body + "\n}\n"))

    return blocks

def real_line(first_line, wrapped_line):
    """The line in the Deor file for a line of a wrapped block."""

    return first_line + wrapped_line - 1 - WRAPPER_LINES_ABOVE

def rust_only_source(source):
    """The file with every line that is not inside a `rust` block blanked, so line numbers still match."""
    keep = {line.number: line.code for statement in rust_statements(source) for line in statement.rust_lines}

    return "\n".join(keep.get(number, "") for number in range(1, len(source.splitlines()) + 1))
