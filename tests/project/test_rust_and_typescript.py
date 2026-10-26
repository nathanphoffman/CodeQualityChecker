from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.models import Status
from codequality.registry import all_rules

def grade(root: Path, rule_id: str):
    return {rule.id: result for rule, result in report.run(detect(root), all_rules())}[rule_id]

def rust_project(root: Path, source: str = "fn main() {}\n") -> Path:
    (root / "Cargo.toml").write_text('[package]\nname = "demo"\n')
    (root / "main.rs").write_text(source)

    return root

def typescript_project(root: Path, source: str = "export const total = 1;\n") -> Path:
    (root / "tsconfig.json").write_text('{"compilerOptions": {"strict": true}}')
    (root / "index.ts").write_text(source)

    return root

def test_cargo_lock_is_required(tmp_path: Path):
    rust_project(tmp_path)

    assert grade(tmp_path, "RUST-001").status == Status.FAIL

    (tmp_path / "Cargo.lock").write_text("")

    assert grade(tmp_path, "RUST-001").status == Status.PASS

def test_rustfmt_and_clippy_each_count_half(tmp_path: Path):
    rust_project(tmp_path)

    assert grade(tmp_path, "RUST-002").score == 0.0

    (tmp_path / "rustfmt.toml").write_text("")

    assert grade(tmp_path, "RUST-002").score == 0.5

    (tmp_path / "clippy.toml").write_text("")

    assert grade(tmp_path, "RUST-002").score == 1.0

def test_unwrap_calls_lower_the_score(tmp_path: Path):
    rust_project(tmp_path, "fn main() {\n    a.unwrap();\n    b.expect(\"x\");\n}\n")

    assert 0.0 < grade(tmp_path, "RUST-003").score < 1.0

def test_rust_without_unwrap_passes_and_test_folders_are_skipped(tmp_path: Path):
    rust_project(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "it.rs").write_text("fn t() { a.unwrap(); a.unwrap(); a.unwrap(); }\n")

    assert grade(tmp_path, "RUST-003").status == Status.PASS

def test_strict_mode_must_be_true(tmp_path: Path):
    typescript_project(tmp_path)

    assert grade(tmp_path, "TS-001").status == Status.PASS

    (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {"strict": false}}')

    assert grade(tmp_path, "TS-001").status == Status.FAIL

def test_explicit_any_lowers_the_score(tmp_path: Path):
    typescript_project(tmp_path, "const a: any = 1;\nconst b = a as any;\nconst c = <any>a;\n")

    assert grade(tmp_path, "TS-002").score == 0.0

def test_typescript_without_any_passes(tmp_path: Path):
    typescript_project(tmp_path)

    assert grade(tmp_path, "TS-002").status == Status.PASS

def test_linter_config_is_required(tmp_path: Path):
    typescript_project(tmp_path)

    assert grade(tmp_path, "TS-003").status == Status.FAIL

    (tmp_path / "biome.json").write_text("{}")

    assert grade(tmp_path, "TS-003").status == Status.PASS
