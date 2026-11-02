def rust_project(root):
    (root / "src").mkdir(parents=True)
    (root / "Cargo.toml").write_text('[package]\nname = "demo"\n')
    (root / "src" / "main.rs").write_text("fn main() {}\n")

    return root

def set_up(tmp_path, monkeypatch, build_script):
    claude = tmp_path / "claude"
    (claude / "claude-md-pieces").mkdir(parents=True)
    (claude / "projects" / "demo").mkdir(parents=True)
    monkeypatch.setattr(build_script, "CLAUDE_DIR", claude)
    monkeypatch.setattr(build_script, "PIECES_DIR", claude / "claude-md-pieces")
    rules = tmp_path / "RULES.md"
    rules.write_text("1. First rule.\n2. Second rule.\n")
    monkeypatch.setattr(build_script, "RULES_FILE", rules)

    return claude

def test_builds_global_then_language_then_project_notes(tmp_path, monkeypatch, build_script):
    claude = set_up(tmp_path, monkeypatch, build_script)
    
    (claude / "claude-md-pieces" / "rust.md").write_text("RUST")
    (claude / "projects" / "demo" / "CLAUDE.project.md").write_text("NOTES")
    project = rust_project(tmp_path / "real_project")

    build_script.build_one("demo", project)
    text = (claude / "projects" / "demo" / "CLAUDE.md").read_text()

    assert text.startswith(build_script.GENERATED_MARK)
    assert text.index("1. First rule.") < text.index("RUST") < text.index("NOTES")

def test_pieces_that_do_not_exist_are_skipped(tmp_path, monkeypatch, build_script):
    claude = set_up(tmp_path, monkeypatch, build_script)
    
    project = tmp_path / "real_project2"
    project.mkdir()

    result = build_script.build_one("demo", project)

    assert "rust" not in result
    assert "1. First rule.\n2. Second rule." in (claude / "projects" / "demo" / "CLAUDE.md").read_text()  # numbered and worded as in RULES.md

def test_a_hand_written_claude_md_is_never_overwritten(tmp_path, monkeypatch, build_script):
    claude = set_up(tmp_path, monkeypatch, build_script)
    
    hand_written = claude / "projects" / "demo" / "CLAUDE.md"
    hand_written.write_text("my own notes")
    project = tmp_path / "real_project3"
    project.mkdir()

    result = build_script.build_one("demo", project)

    assert result.startswith("skipped")
    assert hand_written.read_text() == "my own notes"

def test_a_generated_claude_md_is_rebuilt(tmp_path, monkeypatch, build_script):
    claude = set_up(tmp_path, monkeypatch, build_script)
    build_script.RULES_FILE.write_text("1. FIRST\n")
    project = tmp_path / "real_project4"
    project.mkdir()
    build_script.build_one("demo", project)
    build_script.RULES_FILE.write_text("1. SECOND\n")

    build_script.build_one("demo", project)

    assert "1. SECOND" in (claude / "projects" / "demo" / "CLAUDE.md").read_text()
    assert "1. FIRST" not in (claude / "projects" / "demo" / "CLAUDE.md").read_text()
