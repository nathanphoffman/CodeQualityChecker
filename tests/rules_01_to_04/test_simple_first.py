from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.models import Status
from codequality.registry import all_rules

UNEXPLAINED = "import re\n\ndef find_digits(text):\n    return re.findall(r'(\\d+)-(\\d+)', text)\n"
EXPLAINED = "import re\n\ndef find_digits(text):\n    # pulls out pairs like 12-34, one group per number\n    return re.findall(r'(\\d+)-(\\d+)', text)\n"
SIMPLE = "def add_tax(price, rate):\n    return price + price * rate\n"

def grade(root: Path, source: str, rule_id: str):
    (root / "app.py").write_text(source)

    return {rule.id: result for rule, result in report.run(detect(root), all_rules())}[rule_id]

def test_code_with_nothing_clever_passes(tmp_path: Path):
    assert grade(tmp_path, SIMPLE, "RULE-03-CLEVER-IS-EXPLAINED").status == Status.PASS
    assert grade(tmp_path, SIMPLE, "RULE-03-LITTLE-CLEVERNESS").status == Status.PASS

def test_clever_line_without_a_comment_is_flagged(tmp_path: Path):
    result = grade(tmp_path, UNEXPLAINED, "RULE-03-CLEVER-IS-EXPLAINED")

    assert result.score < 1.0
    assert "regex" in result.message

def test_clever_line_with_a_comment_is_fine(tmp_path: Path):
    assert grade(tmp_path, EXPLAINED, "RULE-03-CLEVER-IS-EXPLAINED").status == Status.PASS

def test_clever_code_still_counts_against_the_amount_even_when_explained(tmp_path: Path):
    assert grade(tmp_path, EXPLAINED, "RULE-03-LITTLE-CLEVERNESS").score < 1.0
