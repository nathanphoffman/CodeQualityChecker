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

def test_clever_code_in_test_files_is_not_flagged(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "wrapper.py").write_text(UNEXPLAINED)
    result = grade(tmp_path, SIMPLE, "RULE-03-CLEVER-IS-EXPLAINED")
    assert result.message == "no clever code found" and result.score == 1.0

def test_arrow_callbacks_given_to_react_hooks_are_not_clever():
    from codequality.rules.rule_03_simple_first.shared.find_clever import clever_constructs

    hooked = "function C() {\n  useEffect(() => { items.forEach(i => go(i)); }, []);\n  const [x] = useState(() => init());\n}\n"
    plain = "const g = list.map(i => i.map(j => j));\n"

    assert clever_constructs(hooked, "typescript") == []
    assert [kind for kind, _ in clever_constructs(plain, "typescript")] == ["nested_closure"]

def test_files_named_dot_test_or_dot_tests_are_left_out(tmp_path: Path):
    from codequality.detect import detect
    from codequality.source_code import non_test_files

    for name in ("cart.ts", "cart.test.ts", "cart.tests.ts"):
        (tmp_path / name).write_text("export const a = 1;\n")

    assert [path.name for path in non_test_files(detect(tmp_path), (".ts",))] == ["cart.ts"]
