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

def test_related_package_names_count_as_one_family(tmp_path: Path):
    deps = '"tree-sitter>=0.25", "tree-sitter-rust>=0.24", "tree-sitter-typescript>=0.23", "requests>=2"'
    (tmp_path / "pyproject.toml").write_text(f'[project]\nname = "x"\ndependencies = [{deps}]\n')
    (tmp_path / "a.py").write_text("x = 1\n")
    result = dependency_result(tmp_path)

    # 3 related names count as the square root of 3, plus 1 unrelated: 2.73 dependencies on 1296 lines
    assert abs(result.score - 0.75 ** (3 ** 0.5 + 1)) < 1e-9
    assert result.message.startswith("4 dependencies counted as 2.7")

def test_names_sharing_only_a_generic_word_are_not_related():
    from codequality.rules.few_dependencies.group_dependencies import are_related

    assert are_related("serde", "serde_json") and are_related("pytest", "pytest-cov")
    assert not are_related("python-dateutil", "python-dotenv")
    assert not are_related("requests", "flask")
