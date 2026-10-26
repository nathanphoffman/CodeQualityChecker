from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.registry import all_rules

def test_detects_rust_axum(tmp_path: Path):
    (tmp_path / "Cargo.toml").write_text('[dependencies]\naxum = "0.7"\n')
    project = detect(tmp_path)
    assert project.languages == {"rust"}
    assert project.frameworks == {"axum"}

def test_detects_ts_react(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "18"}}')
    (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {"strict": true}}')
    project = detect(tmp_path)
    assert project.languages == {"typescript"}
    assert project.frameworks == {"react"}

    results = report.run(project, all_rules())
    assert any(rule.id == "TS-001" and result.score == 1.0 for rule, result in results)
