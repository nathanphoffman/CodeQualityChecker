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


def clean_all_args(skip=()):
    import argparse

    return argparse.Namespace(all=True, skip=list(skip), path=None)

def point_at_config(cleanup_script, monkeypatch, tmp_path, text):
    (tmp_path / "claude").mkdir()
    (tmp_path / "claude" / "projects.toml").write_text(text)
    monkeypatch.setattr(cleanup_script, "REPO", tmp_path)

def test_all_leaves_out_the_projects_on_the_skip_list(tmp_path, monkeypatch, cleanup_script, capsys):
    point_at_config(cleanup_script, monkeypatch, tmp_path, '[projects]\nkeep = "~/a"\nleave = "~/b"\n\n[cleanup]\nskip = ["leave"]\n')

    assert list(cleanup_script.projects_to_clean(clean_all_args())) == ["keep"]
    assert "[leave] skipped" in capsys.readouterr().out

def test_the_skip_flag_adds_to_the_skip_list(tmp_path, monkeypatch, cleanup_script):
    point_at_config(cleanup_script, monkeypatch, tmp_path, '[projects]\none = "~/a"\ntwo = "~/b"\nthree = "~/c"\n\n[cleanup]\nskip = ["one"]\n')

    assert list(cleanup_script.projects_to_clean(clean_all_args(skip=["two"]))) == ["three"]

def test_a_config_without_a_cleanup_section_skips_nothing(tmp_path, monkeypatch, cleanup_script):
    point_at_config(cleanup_script, monkeypatch, tmp_path, '[projects]\none = "~/a"\n')

    assert list(cleanup_script.projects_to_clean(clean_all_args())) == ["one"]


def run_with_scores(cleanup_script, monkeypatch, tmp_path, scores):
    started = []
    monkeypatch.setattr(cleanup_script, "is_ready", lambda name, project: True)
    monkeypatch.setattr(cleanup_script, "run_formatters", lambda name, project, plan: None)
    monkeypatch.setattr(cleanup_script, "start_agent", lambda name, project, plan, attempt=1: started.append(name))
    remaining = list(scores)
    monkeypatch.setattr(cleanup_script, "grade_score", lambda project: remaining.pop(0))
    cleanup_script.clean_project("demo", tmp_path, plan=False)

    return started

def test_another_agent_starts_while_the_score_is_below_the_floor(tmp_path, monkeypatch, cleanup_script, capsys):
    # before, then after agent 1, after agent 2
    started = run_with_scores(cleanup_script, monkeypatch, tmp_path, [60.0, 75.0, 82.0])

    assert len(started) == 2
    assert "reached the floor" in capsys.readouterr().out

def test_it_stops_after_the_cap_and_says_the_floor_was_not_reached(tmp_path, monkeypatch, cleanup_script, capsys):
    started = run_with_scores(cleanup_script, monkeypatch, tmp_path, [50.0, 55.0, 60.0, 65.0])

    assert len(started) == cleanup_script.MAX_AGENT_RUNS
    assert "DID NOT reach the floor" in capsys.readouterr().out

def test_no_second_agent_when_the_first_reaches_the_floor(tmp_path, monkeypatch, cleanup_script):
    assert len(run_with_scores(cleanup_script, monkeypatch, tmp_path, [70.0, 88.0])) == 1

def test_the_score_goals_are_ordered(cleanup_script):
    assert cleanup_script.SCORE_FLOOR < cleanup_script.SCORE_TARGET_LOW <= cleanup_script.SCORE_TARGET_HIGH < cleanup_script.SCORE_IDEAL


def with_git_identity(monkeypatch):
    for name in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(name, "Tester")
    for name in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(name, "tester@example.com")

def test_changes_made_by_the_cleanup_are_committed(tmp_path, monkeypatch, cleanup_script):
    with_git_identity(monkeypatch)
    git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("one")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "first")
    (tmp_path / "a.txt").write_text("two")
    (tmp_path / "new.txt").write_text("new")

    cleanup_script.commit_changes("demo", tmp_path, "cleanup: test")

    assert subprocess.run(["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True).stdout.strip() == ""
    assert subprocess.run(["git", "log", "-1", "--format=%s"], cwd=tmp_path, capture_output=True, text=True).stdout.strip() == "cleanup: test"

def test_nothing_is_committed_when_nothing_changed(tmp_path, monkeypatch, cleanup_script):
    with_git_identity(monkeypatch)
    git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("one")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "first")

    cleanup_script.commit_changes("demo", tmp_path, "cleanup: test")

    assert subprocess.run(["git", "log", "--format=%s"], cwd=tmp_path, capture_output=True, text=True).stdout.split("\n")[:-1] == ["first"]

def test_the_agents_grade_command_starts_in_the_codequality_folder(tmp_path, cleanup_script):
    command = cleanup_script.agent_grade_command(tmp_path)

    assert f"--directory {cleanup_script.REPO}" in command and command.endswith(f"-m codequality {tmp_path}")


def test_the_agent_may_git_rm_but_not_rm(cleanup_script):
    assert "Bash(git rm:*)" in cleanup_script.AGENT_ALLOWED_TOOLS
    assert "Bash(rm:*)" in cleanup_script.AGENT_DENIED_TOOLS
