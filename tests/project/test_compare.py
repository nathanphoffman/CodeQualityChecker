import json
import subprocess
from pathlib import Path

import pytest

from codequality.cli import main

CLEAN_SOURCE = "def total(values):\n    return sum(values)\n"
SECRET_SOURCE = 'API_KEY = "abcd1234efgh5678abcd"\n'

def git(root: Path, *arguments: str) -> None:
    subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *arguments], cwd=root, check=True, capture_output=True)

def repository(root: Path, folder: str = "") -> Path:
    """A git repository with one clean committed file. Returns the project folder, which is `folder` inside it."""
    project = root / folder
    project.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q")
    (project / "app.py").write_text(CLEAN_SOURCE)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "clean")

    return project

def test_a_worse_working_tree_is_reported_and_can_fail_the_run(tmp_path: Path, capsys):
    project = repository(tmp_path)
    (project / "leak.py").write_text(SECRET_SOURCE)

    assert main([str(project), "--compare", "HEAD", "--only", "RULE-05"]) == 0
    assert "RULE-05-HARDCODED-SECRETS" in capsys.readouterr().out
    assert main([str(project), "--compare", "HEAD", "--only", "RULE-05", "--fail-if-worse"]) == 1

def test_no_change_passes_even_with_fail_if_worse(tmp_path: Path, capsys):
    project = repository(tmp_path)

    assert main([str(project), "--compare", "HEAD", "--fail-if-worse"]) == 0
    assert "0.0" in capsys.readouterr().out

def test_an_improvement_does_not_fail_the_run(tmp_path: Path):
    project = repository(tmp_path)
    (project / "leak.py").write_text(SECRET_SOURCE)
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "leak")
    (project / "leak.py").unlink()

    assert main([str(project), "--compare", "HEAD", "--only", "RULE-05", "--fail-if-worse"]) == 0

def test_json_output_lists_the_scores_and_changed_checks(tmp_path: Path, capsys):
    project = repository(tmp_path)
    (project / "leak.py").write_text(SECRET_SOURCE)
    main([str(project), "--compare", "HEAD", "--only", "RULE-05", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["new_score"] < data["old_score"]
    assert "RULE-05-HARDCODED-SECRETS" in {check["id"] for check in data["changed_checks"]}

def test_a_project_in_a_subfolder_is_compared_with_the_same_subfolder(tmp_path: Path, capsys):
    project = repository(tmp_path, "services/api")

    assert main([str(project), "--compare", "HEAD"]) == 0
    assert "Compared with HEAD" in capsys.readouterr().out

def test_the_temporary_checkout_is_removed(tmp_path: Path):
    project = repository(tmp_path)
    main([str(project), "--compare", "HEAD"])
    listing = subprocess.run(["git", "worktree", "list"], cwd=tmp_path, capture_output=True, text=True, check=True).stdout

    assert len(listing.strip().splitlines()) == 1

def test_an_unknown_ref_stops_with_a_clear_message(tmp_path: Path):
    project = repository(tmp_path)

    with pytest.raises(SystemExit) as stopped:
        main([str(project), "--compare", "no-such-branch"])

    assert "no-such-branch" in str(stopped.value)

def test_a_folder_that_is_not_a_git_repository_stops_with_a_clear_message(tmp_path: Path):
    (tmp_path / "app.py").write_text(CLEAN_SOURCE)

    with pytest.raises(SystemExit) as stopped:
        main([str(tmp_path), "--compare", "HEAD"])

    assert "cannot compare" in str(stopped.value)

def test_fail_if_worse_needs_compare(tmp_path: Path):
    with pytest.raises(SystemExit):
        main([str(tmp_path), "--fail-if-worse"])
