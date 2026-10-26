from pathlib import Path

from codequality import report
from codequality.detect import detect, ignore_patterns
from codequality.registry import all_rules

BAD_COMMENTS = "x = 1  # increment x\ny = 2  # set y\n"

def rule_scores(root: Path) -> dict[str, float]:
    return {rule.id: result.score for rule, result in report.run(detect(root), all_rules())}

def project_with(tmp_path: Path, ignore_lines: str) -> Path:
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "app.py").write_text(BAD_COMMENTS)
    (tmp_path / ".codequalityignore").write_text(ignore_lines)

    return tmp_path

def test_plain_lines_apply_to_every_rule_and_rule_lines_are_kept_apart(tmp_path: Path):
    project_with(tmp_path, "# note\n\nvendor/\ntests RULE-09 RULE-02\n")

    assert ignore_patterns(tmp_path) == (["vendor"], {"tests": ["RULE-09", "RULE-02"]})

def test_missing_ignore_file_means_nothing_is_ignored(tmp_path: Path):
    assert ignore_patterns(tmp_path) == ([], {})

def test_a_rule_line_only_changes_that_rule(tmp_path: Path):
    before = rule_scores(project_with(tmp_path, ""))
    after = rule_scores(project_with(tmp_path, "src RULE-09\n"))
    changed = {rule_id for rule_id in before if before[rule_id] != after[rule_id]}

    assert changed and all(rule_id.startswith("RULE-09") for rule_id in changed)

def test_a_rule_line_for_another_rule_changes_nothing(tmp_path: Path):
    before = rule_scores(project_with(tmp_path, ""))

    assert rule_scores(project_with(tmp_path, "src RULE-05\n")) == before

def test_a_plain_line_skips_the_path_for_every_rule(tmp_path: Path):
    project_with(tmp_path, "src\n")

    assert not detect(tmp_path).files(".py")
