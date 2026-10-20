from pathlib import Path

from codequality.rules.rule_09_comment_why.shared.extract import python_comments, tree_comments
from codequality.rules.rule_09_comment_why.shared.judging.judge_comment import why_confidence

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

def test_amount_score_is_a_peak():
    from codequality.rules.rule_09_comment_why.shared.amount_checks import amount_score

    ideal = 6 ** 1.5
    assert amount_score(10, 10) == 1.0
    assert abs(amount_score(10 * ideal / 6, 10) - 0.90) < 1e-9  # one comment per 6 lines: the simple-function edge
    assert abs(amount_score(10 * ideal / 36, 10) - 0.90) < 1e-9  # one per 36: the complex-function edge
    assert abs(amount_score(10 * 6 ** 0.5, 10) - 0.90) < 1e-9 and abs(amount_score(10 / 6 ** 0.5, 10) - 0.90) < 1e-9
    assert abs(amount_score(10 * 6, 10) - 0.90 * 0.25) < 1e-9  # a whole power of 6 off: the edge, then one more step

    assert amount_score(0, 10) == 0.0

def test_comment_amount_message_reads_as_a_scale(tmp_path: Path):
    from codequality import report
    from codequality.detect import detect
    from codequality.registry import all_rules

    (tmp_path / "a.py").write_text("# note\nx = 1\n" + "x = 1\n" * 28)
    results = {rule.id: result for rule, result in report.run(detect(tmp_path), all_rules())}
    assert results["RULE-09-COMMENT-AMOUNT"].message.startswith("Encountered 1 non-complex comments, expected 2")

def test_the_amount_check_counts_twice_as_much_as_a_warning():
    from codequality.registry import all_rules

    weights = {rule.id: rule.weight for rule in all_rules()}
    assert weights["RULE-09-COMMENT-AMOUNT"] == 2 * weights["RULE-09-COMMENTS-SAY-WHY"]

def test_comments_on_clever_code_do_not_count_toward_the_amount(tmp_path: Path):
    from codequality.rules.rule_09_comment_why.shared.amount_checks import count_plain_comments
    from codequality.detect import detect

    (tmp_path / "a.py").write_text("import re\n# how this works\nPATTERN = re.compile('x')\n# plain note\ny = 1\n")
    assert count_plain_comments(detect(tmp_path)) == 1
