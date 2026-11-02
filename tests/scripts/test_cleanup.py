import subprocess

def git(folder, *args):
    subprocess.run(["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args], cwd=folder, check=True, capture_output=True)

def test_a_folder_that_is_not_a_git_repository_is_skipped(tmp_path, cleanup_script, capsys):
    assert cleanup_script.is_ready("demo", tmp_path) is False
    assert "not a git repository" in capsys.readouterr().out

def test_uncommitted_changes_are_skipped_with_a_commit_first_message(tmp_path, cleanup_script, capsys):
    git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("hello")

    assert cleanup_script.is_ready("demo", tmp_path) is False
    assert "Commit them first" in capsys.readouterr().out

def test_a_clean_repository_is_ready(tmp_path, cleanup_script):
    git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("hello")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "first")

    assert cleanup_script.is_ready("demo", tmp_path) is True

def test_a_file_list_placeholder_is_filled_with_matching_files(tmp_path, cleanup_script):
    (tmp_path / "build.sh").write_text("echo hi\n")
    (tmp_path / "notes.txt").write_text("not a script")

    command = cleanup_script.expand(["shfmt", "-w", "{files:.sh,.bash}"], tmp_path)

    assert command == ["shfmt", "-w", str(tmp_path / "build.sh")]

def test_a_command_with_no_matching_files_is_dropped(tmp_path, cleanup_script):
    assert cleanup_script.expand(["shfmt", "-w", "{files:.sh}"], tmp_path) is None

def test_the_same_command_is_only_listed_once(tmp_path, cleanup_script):
    table = {"css": [["biome", "check", "."]], "html": [["biome", "check", "."]]}

    assert cleanup_script.commands_for(table, tmp_path, ["css", "html"]) == [["biome", "check", "."]]

def test_languages_without_commands_are_ignored(tmp_path, cleanup_script):
    assert cleanup_script.commands_for({}, tmp_path, ["hare"]) == []

def test_long_commands_are_shortened_for_display(cleanup_script):
    shown = cleanup_script.short(["tool", *["/very/long/path/file.sh"] * 20])

    assert len(shown) <= 104 and shown.endswith("...")

def test_javascript_and_shell_files_count_as_tooling_languages(tmp_path, cleanup_script):
    (tmp_path / "run.sh").write_text("echo hi\n")
    (tmp_path / "app.mjs").write_text("export const x = 1;\n")

    assert {"shell", "javascript"} <= set(cleanup_script.languages_in(tmp_path))

def test_the_agent_may_not_push(cleanup_script):
    assert "Bash(git push:*)" in cleanup_script.AGENT_DENIED_TOOLS
    assert not any("git push" in tool for tool in cleanup_script.AGENT_ALLOWED_TOOLS)
