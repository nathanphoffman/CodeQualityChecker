from pathlib import Path

from codequality.detect import detect
from codequality.rules.test_what_matters.count_tests import (count_python_tests, count_rust_tests,
                                                             count_tests_in_project, count_typescript_tests)

PYTHON = "def test_one():\n    pass\n\nclass T:\n    def test_two(self):\n        pass\n\ndef helper():\n    pass\n"
RUST = "#[cfg(test)]\nmod tests {\n    #[test]\n    fn one() {}\n\n    #[tokio::test]\n    // note\n    async fn two() {}\n\n    fn helper() {}\n}\n"
TYPESCRIPT = "describe('x', () => {\n  it('a', () => { run(); });\n  test('b', function () { run(); });\n  test(notACallback);\n});\n"

def test_tests_are_counted_in_each_language():
    assert count_python_tests(PYTHON) == 2
    assert count_rust_tests(RUST) == 2
    assert count_typescript_tests(TYPESCRIPT) == 2

def test_tests_in_test_folders_are_counted(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(PYTHON)
    (tmp_path / "b.rs").write_text(RUST)
    assert count_tests_in_project(detect(tmp_path)) == 4
