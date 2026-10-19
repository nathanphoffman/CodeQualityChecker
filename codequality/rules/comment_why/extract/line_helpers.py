COMMENT_MARKERS = ("#", "//", "/*", "*")
MARKER_CHARACTERS = "/*#!"


def clean_text(raw):
    """A comment without its markers: // # /* */ and the * down the side of a block comment."""
    lines = [line.strip().lstrip(MARKER_CHARACTERS).rstrip("*/").strip() for line in raw.splitlines()]
    return " ".join(line for line in lines if line)


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
