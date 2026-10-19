from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.registry import all_rules


def test_detects_rust_axum(tmp_path: Path):
    (tmp_path / "Cargo.toml").write_text('[dependencies]\naxum = "0.7"\n')
    p = detect(tmp_path)
    assert p.languages == {"rust"}
    assert p.frameworks == {"axum"}


def test_detects_ts_react(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "18"}}')
    (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {"strict": true}}')
    p = detect(tmp_path)
    assert p.languages == {"typescript"}
    assert p.frameworks == {"react"}
    results = report.run(p, all_rules())
    assert any(r.id == "TS-001" and res.score == 1.0 for r, res in results)
