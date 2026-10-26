from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.models import Status
from codequality.registry import all_rules

CLEAR = "def total_price(order_items):\n    running_total = 0\n    return running_total\n"
SHORT = "def f(a):\n    b = a\n    c = b\n    d = c\n    return d\n"
ACRONYMS = "def parseXMLFile(xmlFile):\n    myDTO = xmlFile\n    return myDTO\n"

def grade(root: Path, source: str, rule_id: str):
    (root / "app.py").write_text(source)

    return {rule.id: result for rule, result in report.run(detect(root), all_rules())}[rule_id]

def test_long_names_pass(tmp_path: Path):
    assert grade(tmp_path, CLEAR, "RULE-02-NAME-LENGTH").status == Status.PASS

def test_short_names_are_flagged(tmp_path: Path):
    result = grade(tmp_path, SHORT, "RULE-02-NAME-LENGTH")

    assert result.score < 1.0
    assert "too short" in result.message

def test_unknown_acronyms_are_flagged(tmp_path: Path):
    result = grade(tmp_path, ACRONYMS, "RULE-02-NO-ACRONYMS")

    assert result.score < 1.0
    assert "contain an acronym" in result.message

def test_known_acronyms_and_constants_are_fine(tmp_path: Path):
    source = "MAX_RETRY_COUNT = 3\n\ndef parse_json_response(http_url):\n    return http_url, MAX_RETRY_COUNT\n"

    assert grade(tmp_path, source, "RULE-02-NO-ACRONYMS").status == Status.PASS
