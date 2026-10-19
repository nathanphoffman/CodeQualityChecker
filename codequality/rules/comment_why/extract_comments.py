import io
import tokenize
import warnings

from ...source_code import PYTHON
from ...tree_sitter_support.parse_tree import parse_tree
from ...tree_sitter_support.tree_walk import walk
from ..simple_first.find_clever import clever_constructs
from .Comment_Found import Comment_Found
from .limits import PRAGMA_PREFIXES

COMMENT_TYPES = {"comment", "line_comment", "block_comment"}
COMMENT_MARKERS = ("#", "//", "/*", "*")
MARKER_CHARACTERS = "/*#!"


def clean_text(raw):
    """A comment without its markers: // # /* */ and the * down the side of a block comment."""
    lines = [line.strip().lstrip(MARKER_CHARACTERS).rstrip("*/").strip() for line in raw.splitlines()]
    return " ".join(line for line in lines if line)


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


def next_code(lines, after):
    """(line number, text) of the first line after `after` that is code, not blank and not another comment."""
    for number in range(after + 1, len(lines) + 1):
        text = lines[number - 1].strip()
        if text and not text.startswith(COMMENT_MARKERS):
            return number, text
    return 0, ""


def merge_runs(raw):
    """A run of // or # lines on consecutive lines is one comment. Comments trailing code stay alone."""
    merged = []
    for first, last, text, code_before in sorted(raw):
        if merged and not code_before and not merged[-1][3] and first == merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], last, merged[-1][2] + "\n" + text, "")
        else:
            merged.append((first, last, text, code_before))
    return merged


def build_comments(source, language, raw):
    lines = source.splitlines()
    clever_lines = {line for _, line in clever_constructs(source, language)}
    found = []
    for first, last, text, code_before in merge_runs(raw):
        cleaned = clean_text(text)
        next_number, next_text = next_code(lines, last)
        if cleaned.lower().startswith(PRAGMA_PREFIXES):
            continue
        about = code_before or next_text
        explains = (first if code_before else next_number) in clever_lines
        found.append(Comment_Found(first, last, cleaned, about, explains, language))
    return found


def python_comments(source):
    return build_comments(source, PYTHON, python_raw(source))


def tree_comments(source, language):
    return build_comments(source, language, tree_raw(source, language))
