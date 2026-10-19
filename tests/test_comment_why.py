from pathlib import Path

from codequality.rules.comment_why.extract import python_comments, tree_comments
from codequality.rules.comment_why.judging.judge_comment import why_confidence

CASES = [
    # (source, expected: "what" if confidence is low, "why" if high)
    ("counter = 0\n# increment the counter\ncounter += 1\n", "what"),
    ("x = 1\n# total = price * quantity\ny = 2\n", "what"),
    ("x = 1\n# -----\ny = 2\n", "what"),
    ("x = 1\n# TODO\ny = 2\n", "what"),
    ("for item in items:\n    # loop over each item in items\n    handle(item)\n", "what"),
    ("retries = 3\n# the server rate-limits us, so we back off instead of hammering it\nretries += 1\n", "why"),
    ("x = 1\n# handle the case if the file is missing\ny = open(path)\n", "why"),  # a lone "if" is just wording
    ("x = 1\n# Stripe sends this twice, so the second one must be ignored (see https://example.com/bug)\ny = 2\n", "why"),
    ("x = 1\n# see `close()` for the cleanup that follows\ny = 2\n", "why"),
]


def test_python_comments_are_sorted_into_what_and_why():
    for source, expected in CASES:
        (comment,) = python_comments(source)
        confidence = why_confidence(comment)
        assert (confidence < 0.5) == (expected == "what"), (comment.text, confidence)


def test_comments_on_clever_code_are_marked_so_they_can_be_left_out():
    source = "import re\n# matches a number, then a unit\nPATTERN = re.compile(r'\\d+px')\nx = re.compile(r'a')  # regex\n"
    comments = python_comments(source)
    assert len(comments) == 2 and all(comment.explains_clever for comment in comments)


def test_rust_and_typescript_comments_are_read():
    rust = "fn main() {\n    // increment the counter\n    counter += 1;\n}\n"
    typescript = "function f() {\n  /* because the API caps pages at 50 */\n  const size = 50;\n}\n"
    (rust_comment,) = tree_comments(rust, "rust")
    (typescript_comment,) = tree_comments(typescript, "typescript")
    assert why_confidence(rust_comment) < 0.5 < why_confidence(typescript_comment)


def test_pragma_comments_are_ignored():
    assert python_comments("import os  # noqa: F401\n#!/usr/bin/env python\n") == []


def test_comment_above_a_multi_line_statement_covers_clever_code_inside_it():
    source = "import re\n# the patterns, one per kind\nPATTERNS = {\n    'a': re.compile('x'),\n    'b': 2,\n}\nother = 1\n"
    (comment,) = python_comments(source)
    assert comment.explains_clever
    assert not python_comments("# just a note\nx = 1\n")[0].explains_clever


def amount_scores(tmp_path: Path, comment_count: int, code_lines: int):
    from codequality import report
    from codequality.detect import detect
    from codequality.registry import all_rules

    commented = "".join(f"# note {n}\nx = 1\n" for n in range(comment_count))  # code between, or the comments would merge
    body = commented + "x = 1\n" * (code_lines - 2 * comment_count)
    (tmp_path / "a.py").write_text(body)
    results = {rule.id: result.score for rule, result in report.run(detect(tmp_path), all_rules())}
    return results["RULE-09-ENOUGH-COMMENTS"], results["RULE-09-MODEST-COMMENTS"]


def test_one_comment_per_36_lines_is_perfect_on_both_sides(tmp_path: Path):
    assert amount_scores(tmp_path, 1, 36) == (1.0, 1.0)


def test_too_few_is_harsher_than_too_many(tmp_path: Path):
    few, _ = amount_scores(tmp_path, 1, 72)  # half the target: 0.5 squared
    assert abs(few - 0.25) < 1e-9
    other = tmp_path / "many"
    other.mkdir()
    _, many = amount_scores(other, 2, 36)  # double the target: 1 / sqrt(2)
    assert abs(many - 0.5 ** 0.5) < 1e-9 and many > few


def test_comments_on_clever_code_do_not_count_toward_the_amount(tmp_path: Path):
    from codequality.rules.comment_why.amount_checks import comments_per_target
    from codequality.detect import detect

    (tmp_path / "a.py").write_text("import re\n# how this works\nPATTERN = re.compile('x')\n# plain note\ny = 1\n")
    count, _, _ = comments_per_target(detect(tmp_path))
    assert count == 1
