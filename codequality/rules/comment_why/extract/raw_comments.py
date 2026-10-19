import io
import tokenize
import warnings

from ....tree_sitter_support.parse_tree import parse_tree
from ....tree_sitter_support.tree_walk import walk

COMMENT_TYPES = {"comment", "line_comment", "block_comment"}


def python_raw(source):
    """(first_line, last_line, raw text, code before it on the line) for every # comment."""

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError) as error:
        warnings.warn(f"skipped Python comments that could not be read: {error}")
        return []

    return [(token.start[0], token.end[0], token.string, token.line[:token.start[1]].strip())
            for token in tokens if token.type == tokenize.COMMENT and not token.string.startswith("#!")]


def tree_raw(source, language):
    lines = source.splitlines()
    return [(node.start_point.row + 1, node.end_point.row + 1, node.text.decode(),
             lines[node.start_point.row][:node.start_point.column].strip())
            for node in walk(parse_tree(source, language)) if node.type in COMMENT_TYPES]
