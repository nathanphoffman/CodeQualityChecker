"""These use a fake home folder and a fake repo inside tmp_path, so they never touch the real ~/.claude."""
import subprocess
import sys

import pytest

def git(folder, *args):
    return subprocess.run(["git", "-C", str(folder), *args], check=True, capture_output=True, text=True).stdout

def make_repo(folder):
    folder.mkdir(parents=True, exist_ok=True)
    git(folder, "init", "-q", "-b", "main")

def commit_everything(folder):
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "--allow-empty", "-m", "setup")

class World:
    def __init__(self, tmp_path, monkeypatch, sync_script):
        self.script, self.monkeypatch = sync_script, monkeypatch
        for name in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
            monkeypatch.setenv(name, "Tester")
        for name in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
            monkeypatch.setenv(name, "tester@example.com")
        self.home = tmp_path / "home" / ".claude"
        self.home.mkdir(parents=True)
        self.claude = tmp_path / "repo" / "claude"
        (self.claude / "global").mkdir(parents=True)
        (self.claude / "projects").mkdir()
        (self.claude / "projects.toml").write_text("[projects]\n")
        self.repo = tmp_path / "repo"
        make_repo(self.repo)
        monkeypatch.setattr(sync_script, "REPO", tmp_path / "repo")
        monkeypatch.setattr(sync_script, "CLAUDE_DIR", self.claude)
        monkeypatch.setattr(sync_script, "HOME_CLAUDE", self.home)
        monkeypatch.setattr(sync_script, "STATE_FILE", self.home / "sync-state.json")
        monkeypatch.setattr(sync_script, "is_terminal", lambda: True)

    @property
    def repo_file(self):
        return self.claude / "global" / "CLAUDE.md"

    @property
    def live_file(self):
        return self.home / "CLAUDE.md"

    def backups(self):
        return [path.read_text() for path in (self.home / "backups").rglob("*") if path.is_file()]

    def run(self, answers=(), flags=(), commit_repo=True):
        remaining = list(answers)
        if commit_repo:
            commit_everything(self.repo)  # the sync refuses to run while this repo has uncommitted changes

        def fake_input(prompt=""):
            assert remaining, f"the script asked for input that the test did not expect: {prompt!r}"

            return remaining.pop(0)

        self.monkeypatch.setattr("builtins.input", fake_input)
        self.monkeypatch.setattr(sys, "argv", ["sync_claude.py", *flags])
        code = self.script.main()
        assert not remaining, f"the test gave answers the script never asked for: {remaining}"

        return code

@pytest.fixture
def world(tmp_path, monkeypatch, sync_script):
    return World(tmp_path, monkeypatch, sync_script)

def synced_once(world):
    world.repo_file.write_text("v1")
    assert world.run(["yes"]) == 0

def test_it_refuses_to_run_without_a_terminal(world):
    world.monkeypatch.setattr(world.script, "is_terminal", lambda: False)
    world.repo_file.write_text("v1")

    assert world.run() == 1
    assert not world.live_file.exists()

def test_the_first_sync_creates_the_file_and_remembers_it(world):
    synced_once(world)

    assert world.live_file.read_text() == "v1"
    assert str(world.live_file) in world.script.load_state()

def test_a_second_sync_with_nothing_changed_asks_nothing(world, capsys):
    synced_once(world)

    assert world.run() == 0
    assert "already in sync" in capsys.readouterr().out

def test_a_repo_edit_is_applied_and_the_old_file_backed_up(world):
    synced_once(world)
    world.repo_file.write_text("v2")

    assert world.run(["yes"]) == 0
    assert world.live_file.read_text() == "v2"
    assert "v1" in world.backups()

def test_declining_the_prompt_changes_nothing(world):
    synced_once(world)
    world.repo_file.write_text("v2")

    assert world.run(["no"]) == 1
    assert world.live_file.read_text() == "v1"

def test_dry_run_changes_nothing_but_shows_conflicts(world, capsys):
    synced_once(world)
    world.live_file.write_text("edited outside")

    assert world.run(flags=["--dry-run"]) == 0
    assert world.live_file.read_text() == "edited outside"
    assert "changed outside this repo" in capsys.readouterr().out

def test_an_outside_edit_is_a_conflict_and_enter_takes_codequality(world):
    synced_once(world)
    world.live_file.write_text("edited outside")

    assert world.run([""]) == 0
    assert world.live_file.read_text() == "v1"
    assert "edited outside" in world.backups()

def test_an_outside_edit_can_replace_the_codequality_copy(world):
    synced_once(world)
    world.live_file.write_text("edited outside")

    assert world.run(["dest"]) == 0
    assert world.repo_file.read_text() == "edited outside"
    assert world.live_file.read_text() == "edited outside"

def test_skip_leaves_both_files_alone(world):
    synced_once(world)
    world.live_file.write_text("edited outside")

    assert world.run(["skip"]) == 0
    assert world.repo_file.read_text() == "v1"
    assert world.live_file.read_text() == "edited outside"

def test_after_taking_the_destination_the_next_sync_is_quiet(world, capsys):
    synced_once(world)
    world.live_file.write_text("edited outside")
    world.run(["dest"])

    assert world.run() == 0
    assert "already in sync" in capsys.readouterr().out

def test_an_existing_file_that_was_never_synced_is_a_conflict(world, capsys):
    world.live_file.write_text("already here")
    world.repo_file.write_text("v1")

    assert world.run(["skip"]) == 0
    assert "never been synced before" in capsys.readouterr().out
    assert world.live_file.read_text() == "already here"

def test_an_identical_existing_file_is_not_a_conflict(world, capsys):
    world.live_file.write_text("v1")
    world.repo_file.write_text("v1")

    assert world.run() == 0
    assert "already in sync" in capsys.readouterr().out

def test_a_skill_folder_is_copied_as_one_item(world):
    skill = world.claude / "global" / "skills" / "cleanup"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("skill text")

    assert world.run(["yes"]) == 0
    assert (world.home / "skills" / "cleanup" / "SKILL.md").read_text() == "skill text"

def test_a_project_gets_its_files_and_linter_configs(world, tmp_path):
    project = tmp_path / "real_project"
    (project / "src").mkdir(parents=True)
    (project / "Cargo.toml").write_text('[package]\nname = "demo"\n')
    (project / "src" / "main.rs").write_text("fn main() {}\n")
    make_repo(project)
    commit_everything(project)
    (world.claude / "projects.toml").write_text(f'[projects]\ndemo = "{project}"\n')
    (world.claude / "projects" / "demo").mkdir()
    (world.claude / "projects" / "demo" / "CLAUDE.md").write_text("project notes")
    (world.claude / "projects" / "demo" / "settings.json").write_text("{}")
    (world.claude / "linters" / "rust").mkdir(parents=True)
    (world.claude / "linters" / "rust" / "rustfmt.toml").write_text("max_width = 120")
    (world.claude / "linters" / "python").mkdir()
    (world.claude / "linters" / "python" / "ruff.toml").write_text("line-length = 120")

    assert world.run(["yes"]) == 0
    assert (project / "CLAUDE.md").read_text() == "project notes"
    assert (project / ".claude" / "settings.json").read_text() == "{}"
    assert (project / "rustfmt.toml").read_text() == "max_width = 120"
    assert not (project / "ruff.toml").exists()  # no Python in this project

def test_a_project_folder_missing_from_the_toml_is_skipped_with_a_warning(world, capsys):
    (world.claude / "projects" / "unlisted").mkdir()
    (world.claude / "projects" / "unlisted" / "CLAUDE.md").write_text("x")

    assert world.run() == 0
    assert "not in projects.toml" in capsys.readouterr().out


def project_with_config(world, tmp_path, name="real_project", ignore=""):
    project = tmp_path / name
    project.mkdir()
    (project / ".gitignore").write_text(ignore)
    make_repo(project)
    commit_everything(project)
    (world.claude / "projects.toml").write_text(f'[projects]\ndemo = "{project}"\n')
    (world.claude / "projects" / "demo").mkdir()
    (world.claude / "projects" / "demo" / "CLAUDE.md").write_text("project notes")

    return project

def test_it_stops_when_this_repo_has_uncommitted_changes(world, capsys):
    world.repo_file.write_text("v1")

    assert world.run(commit_repo=False) == 1
    assert "uncommitted changes" in capsys.readouterr().out
    assert not world.live_file.exists()

def test_dry_run_only_warns_when_this_repo_is_dirty(world, capsys):
    world.repo_file.write_text("v1")

    assert world.run(flags=["--dry-run"], commit_repo=False) == 0
    assert "a real sync would stop" in capsys.readouterr().out

def test_a_project_with_uncommitted_changes_is_held_back_and_untouched(world, tmp_path, capsys):
    project = project_with_config(world, tmp_path)
    (project / "work_in_progress.txt").write_text("not committed")

    assert world.run() == 0
    assert "held back" in capsys.readouterr().out
    assert not (project / "CLAUDE.md").exists()

def test_a_clean_project_still_syncs_when_another_is_held_back(world, tmp_path):
    project = project_with_config(world, tmp_path)
    busy = tmp_path / "busy"
    make_repo(busy)
    commit_everything(busy)
    (busy / "scratch.txt").write_text("dirty")
    (world.claude / "projects.toml").write_text(f'[projects]\ndemo = "{project}"\nbusy = "{busy}"\n')
    (world.claude / "projects" / "busy").mkdir()
    (world.claude / "projects" / "busy" / "CLAUDE.md").write_text("busy notes")

    assert world.run(["yes"]) == 0
    assert (project / "CLAUDE.md").read_text() == "project notes"
    assert not (busy / "CLAUDE.md").exists()

def test_a_project_that_is_not_a_git_repository_is_held_back(world, tmp_path, capsys):
    project = tmp_path / "plain_folder"
    project.mkdir()
    (world.claude / "projects.toml").write_text(f'[projects]\ndemo = "{project}"\n')
    (world.claude / "projects" / "demo").mkdir()
    (world.claude / "projects" / "demo" / "CLAUDE.md").write_text("project notes")

    assert world.run() == 0
    assert "not a git repository" in capsys.readouterr().out
    assert not (project / "CLAUDE.md").exists()

def test_the_written_files_are_committed_on_the_current_branch_and_nothing_else(world, tmp_path):
    project = project_with_config(world, tmp_path)
    (world.claude / "projects" / "demo" / "settings.json").write_text("{}")

    assert world.run(["yes"]) == 0
    committed = git(project, "show", "--name-only", "--format=", "HEAD").split()

    assert sorted(committed) == [".claude/settings.json", "CLAUDE.md"]
    assert git(project, "status", "--porcelain").strip() == ""
    assert git(project, "rev-parse", "--abbrev-ref", "HEAD").strip() == "main"
    assert "Update Claude config" in git(project, "log", "-1", "--format=%s")

def test_gitignored_files_are_written_but_not_committed(world, tmp_path):
    project = project_with_config(world, tmp_path, ignore="CLAUDE.local.md\n")
    (world.claude / "projects" / "demo" / "CLAUDE.local.md").write_text("private")

    assert world.run(["yes"]) == 0

    assert (project / "CLAUDE.local.md").read_text() == "private"
    assert "CLAUDE.local.md" not in git(project, "show", "--name-only", "--format=", "HEAD")

def test_a_sync_with_nothing_to_write_makes_no_commit(world, tmp_path):
    project = project_with_config(world, tmp_path)
    assert world.run(["yes"]) == 0
    before = git(project, "rev-parse", "HEAD").strip()

    assert world.run() == 0
    assert git(project, "rev-parse", "HEAD").strip() == before


def rust_project(project):
    (project / "src").mkdir()
    (project / "Cargo.toml").write_text('[package]\nname = "demo"\n')
    (project / "src" / "main.rs").write_text("fn main() {}\n")
    commit_everything(project)

def test_a_project_override_replaces_the_shared_linter_file(world, tmp_path):
    project = project_with_config(world, tmp_path)
    rust_project(project)
    (world.claude / "linters" / "rust").mkdir(parents=True)
    (world.claude / "linters" / "rust" / "rustfmt.toml").write_text("max_width = 120")
    (world.claude / "linters" / "rust" / "clippy.toml").write_text("shared clippy")
    (world.claude / "projects" / "demo" / "linters").mkdir()
    (world.claude / "projects" / "demo" / "linters" / "rustfmt.toml").write_text("max_width = 100")

    assert world.run(["yes"]) == 0
    assert (project / "rustfmt.toml").read_text() == "max_width = 100"
    assert (project / "clippy.toml").read_text() == "shared clippy"  # not overridden, so the shared one is used

def test_an_override_for_a_language_the_project_does_not_have_is_still_copied(world, tmp_path):
    project = project_with_config(world, tmp_path)
    (world.claude / "projects" / "demo" / "linters").mkdir()
    (world.claude / "projects" / "demo" / "linters" / "special.toml").write_text("mine")

    assert world.run(["yes"]) == 0
    assert (project / "special.toml").read_text() == "mine"

def test_other_projects_still_get_the_shared_file(world, tmp_path):
    project = project_with_config(world, tmp_path)
    rust_project(project)
    (world.claude / "linters" / "rust").mkdir(parents=True)
    (world.claude / "linters" / "rust" / "rustfmt.toml").write_text("max_width = 120")

    assert world.run(["yes"]) == 0
    assert (project / "rustfmt.toml").read_text() == "max_width = 120"
