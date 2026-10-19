from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.registry import all_rules

PYPROJECT = '''
[project]
name = "x"
dependencies = ["requests>=2", "Tree_Sitter[extra]>=0.2; python_version>'3'"]

[dependency-groups]
dev = ["pytest"]
'''


def dependency_result(root: Path):
    return {rule.id: result for rule, result in report.run(detect(root), all_rules())}["RULE-08-DEPENDENCIES"]


def test_no_dependencies_is_a_pass(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1\n")
    assert dependency_result(tmp_path).score == 1.0


def test_small_project_is_judged_as_1296_lines(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    (tmp_path / "a.py").write_text("x = 1\n")
    result = dependency_result(tmp_path)
    assert abs(result.score - 0.75 ** 2) < 1e-9  # 2 dependencies, dev tools not counted
    assert "requests" in result.message and "tree-sitter" in result.message


def test_requirements_and_package_json_and_cargo_count_once_each(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("# comment\nrequests==2.0\n-r other.txt\n")
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "18"}, "devDependencies": {"jest": "1"}}')
    (tmp_path / "Cargo.toml").write_text('[dependencies]\naxum = "0.7"\n[dev-dependencies]\ntokio-test = "1"\n')
    assert dependency_result(tmp_path).message.startswith("3 dependencies")
