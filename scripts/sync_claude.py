"""Copy the Claude config in claude/ onto this machine. Run by hand, in a terminal, only by the owner.

    python scripts/sync_claude.py             sync, asking before anything changes
    python scripts/sync_claude.py --dry-run   show what would change and stop

The repo wins by default. Replaced files are first copied to ~/.claude/backups/sync-<time>/.

Git rules:
  - If this repo has uncommitted changes, the sync stops. Commit first.
  - A project with uncommitted changes (or that is not a git repo) is skipped and listed. The others go ahead.
  - After writing, each project gets one commit on its current branch containing only the files the sync wrote
    (gitignored ones are left out). Nothing is pushed. ~/.claude is not a git repo, so it is not committed.

The script remembers what it last wrote (~/.claude/sync-state.json). If a live file no longer matches
that, it was changed outside this repo, so it is not overwritten silently. Those files are listed at the
end with a short diff, and for each one you choose: take CodeQuality (default), take the destination
(which replaces the CodeQuality copy), or skip.
"""
import argparse
import difflib
import filecmp
import hashlib
import json
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from codequality.detect import detect, tooling_languages  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
CLAUDE_DIR = REPO / "claude"
HOME_CLAUDE = Path.home() / ".claude"
STATE_FILE = HOME_CLAUDE / "sync-state.json"
COMMIT_MESSAGE = "Update Claude config from the CodeQuality sync"
DIFF_LINES_SHOWN = 8


def plan_for(source: Path, claude_root: Path, project_root: Path | None) -> list[tuple[Path, Path]]:
    """List (from, to) pairs. project_root is None for the global config.
    Items under skills/, agents/ and commands/ are copied one at a time."""
    if project_root is None:
        files = {"CLAUDE.md": claude_root / "CLAUDE.md", "settings.json": claude_root / "settings.json",
                 "keybindings.json": claude_root / "keybindings.json", "private.md": claude_root / "private.md"}
    else:
        files = {"CLAUDE.md": project_root / "CLAUDE.md", "CLAUDE.local.md": project_root / "CLAUDE.local.md",
                 ".mcp.json": project_root / ".mcp.json", "settings.json": claude_root / "settings.json",
                 "settings.local.json": claude_root / "settings.local.json"}
    pairs = [(source / name, target) for name, target in files.items() if (source / name).exists()]
    for kind in ("skills", "agents", "commands"):
        folder = source / kind
        if folder.is_dir():
            pairs += [(item, claude_root / kind / item.name) for item in sorted(folder.iterdir()) if item.name != ".gitkeep"]
    return pairs


# A language that shares another's folder, and the files of that folder it does not need.
BIOME_ONLY = ("typescript", ("tsconfig.strict.json",))  # biome.json without the TypeScript-only file
LINTER_FOLDER = {"cpp": ("c", ()), "javascript": BIOME_ONLY, "css": BIOME_ONLY, "html": BIOME_ONLY, "vue": BIOME_ONLY}


def linter_pairs(project_root: Path) -> list[tuple[Path, Path]]:
    """Linter and formatter configs from claude/linters/<language>/ for each language found in the project, copied to its root."""
    pairs: dict[Path, Path] = {}
    for language in sorted(tooling_languages(detect(project_root))):
        folder_name, skipped = LINTER_FOLDER.get(language, (language, ()))
        folder = CLAUDE_DIR / "linters" / folder_name
        if folder.is_dir():
            for item in sorted(folder.iterdir()):
                if item.name not in skipped:
                    pairs.setdefault(project_root / item.name, item)  # two languages can share a file; the first one wins
    return [(source, target) for target, source in pairs.items()]


def build_plan() -> list[tuple[Path, Path]]:
    pairs = plan_for(CLAUDE_DIR / "global", HOME_CLAUDE, None)
    config = tomllib.loads((CLAUDE_DIR / "projects.toml").read_text())
    mapped = {name: Path(p).expanduser() for name, p in config.get("projects", {}).items()}
    for name, path in mapped.items():
        src = CLAUDE_DIR / "projects" / name
        if not src.is_dir():
            print(f"warning: projects.toml lists '{name}' but claude/projects/{name}/ does not exist")
        elif not path.is_dir():
            print(f"warning: {path} (project '{name}') does not exist on this machine, skipping")
        else:
            pairs += plan_for(src, path / ".claude", path)
            pairs += linter_pairs(path)
    for folder in sorted((CLAUDE_DIR / "projects").iterdir()):
        if folder.is_dir() and folder.name not in mapped:
            print(f"warning: claude/projects/{folder.name}/ is not in projects.toml, skipping")
    return pairs


def read_files(path: Path) -> dict[str, bytes]:
    """A file becomes {"": bytes}; a folder becomes {relative path: bytes}."""
    if path.is_file():
        return {"": path.read_bytes()}
    return {str(p.relative_to(path)): p.read_bytes() for p in sorted(path.rglob("*")) if p.is_file()}


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    for name, data in read_files(path).items():
        digest.update(name.encode() + b"\0" + data + b"\0")
    return digest.hexdigest()


def same(repo_copy: Path, live: Path) -> bool:
    if not live.exists() or repo_copy.is_dir() != live.is_dir():
        return False
    if repo_copy.is_file():
        return filecmp.cmp(repo_copy, live, shallow=False)
    compared = filecmp.dircmp(repo_copy, live)
    if compared.left_only or compared.diff_files or compared.funny_files:
        return False
    return all(same(repo_copy / d, live / d) for d in compared.common_dirs)


def diff_lines(repo_copy: Path, live: Path) -> list[str]:
    repo_files, live_files = read_files(repo_copy), read_files(live)
    lines = []
    for name in sorted(set(repo_files) | set(live_files)):
        label = name or live.name
        if name not in live_files:
            lines.append(f"only in CodeQuality: {label}")
        elif name not in repo_files:
            lines.append(f"only in destination: {label}")
        elif repo_files[name] != live_files[name]:
            try:
                left, right = repo_files[name].decode().splitlines(), live_files[name].decode().splitlines()
            except UnicodeDecodeError:
                lines.append(f"binary file differs: {label}")
                continue
            lines += difflib.unified_diff(left, right, f"CodeQuality {label}", f"destination {label}", lineterm="", n=0)
    return lines


def classify(repo_copy: Path, live: Path, state: dict[str, str]) -> str:
    if not live.exists():
        return "create"
    if same(repo_copy, live):
        return "same"
    if state.get(str(live)) == fingerprint(live):
        return "update"  # live file is exactly what we wrote last time, so only the repo changed
    return "conflict"


def copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dest)


def replace(src: Path, dest: Path) -> None:
    """Make dest an exact copy of src, removing anything in dest that src does not have."""
    if dest.is_dir():
        shutil.rmtree(dest)
    elif dest.exists():
        dest.unlink()
    copy(src, dest)


def back_up(live: Path, backup_root: Path) -> None:
    if live.exists():
        kept = backup_root / str(live).lstrip("/")
        kept.parent.mkdir(parents=True, exist_ok=True)
        copy(live, kept)


def load_state() -> dict[str, str]:
    try:
        return json.loads(STATE_FILE.read_text())
    except (OSError, ValueError):
        return {}


def save_state(state: dict[str, str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def show_conflict(repo_copy: Path, live: Path, state: dict[str, str]) -> None:
    if str(live) in state:
        reason = "it was changed outside this repo since the last sync"
    else:
        reason = "it already exists, differs from CodeQuality, and has never been synced before"
    print(f"\n{live}\n  why: {reason}")
    lines = diff_lines(repo_copy, live)
    for line in lines[:DIFF_LINES_SHOWN]:
        print(f"    {line}")
    if len(lines) > DIFF_LINES_SHOWN:
        print(f"    ... {len(lines) - DIFF_LINES_SHOWN} more line(s)")


def git(folder: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(folder), *args], text=True, capture_output=True)


def is_under(path: Path, folder: Path) -> bool:
    return folder == path or folder in path.parents


def repo_root(path: Path) -> Path | None:
    """The git repository a path lives in, or None. The path itself may not exist yet."""
    folder = path
    while not folder.is_dir():
        folder = folder.parent
    done = git(folder, "rev-parse", "--show-toplevel")

    return Path(done.stdout.strip()) if done.returncode == 0 else None


def has_uncommitted_changes(root: Path) -> bool:
    return bool(git(root, "status", "--porcelain").stdout.strip())


def only_clean_repos(pairs: list[tuple[Path, Path]]) -> tuple[list[tuple[Path, Path]], dict[str, str]]:
    """Drop the pairs that live in a git repo with uncommitted changes, or in a folder that is not a git repo.
    Returns the pairs that are fine and {project folder: why it was held back}. ~/.claude is not checked."""
    allowed, held, checked = [], {}, {}
    for repo_copy, live in pairs:
        if is_under(live, HOME_CLAUDE):
            allowed.append((repo_copy, live))
            continue
        root = repo_root(live)
        if root is None:
            held[str(live.parent)] = "not a git repository"
            continue
        if root not in checked:
            checked[root] = has_uncommitted_changes(root)
        if checked[root]:
            held[str(root)] = "uncommitted changes"
        else:
            allowed.append((repo_copy, live))
    return allowed, held


def commit_written(written: list[Path]) -> None:
    """One commit per project repo, on its current branch, with only the files the sync wrote. Never pushes."""
    by_repo: dict[Path, list[Path]] = {}
    for path in written:
        root = None if is_under(path, HOME_CLAUDE) else repo_root(path)
        if root:
            by_repo.setdefault(root, []).append(path)
    for root, paths in by_repo.items():
        ours = [str(path) for path in paths if git(root, "check-ignore", "-q", str(path)).returncode != 0]  # 0 means ignored
        if not ours:
            continue
        if git(root, "symbolic-ref", "-q", "HEAD").returncode != 0:
            print(f"  not committed in {root}: it is not on a branch")
            continue
        git(root, "add", "--", *ours)
        names = "\n".join(f"- {Path(path).relative_to(root)}" for path in ours)
        done = git(root, "commit", "-m", f"{COMMIT_MESSAGE}\n\n{names}", "--", *ours)
        print(f"  committed in {root}" if done.returncode == 0 else f"  could not commit in {root}: {done.stderr.strip() or done.stdout.strip()}")


def resolve_conflicts(conflicts: list[tuple[Path, Path]], state: dict[str, str], backup_root: Path) -> list[Path]:
    """Ask about each conflict. Returns the live files that were overwritten with the CodeQuality version."""
    written = []
    print(f"\n{len(conflicts)} file(s) could not be synced automatically.")
    for repo_copy, live in conflicts:
        show_conflict(repo_copy, live, state)
        answer = input("  Enter = take CodeQuality, 'dest' = take the destination (replaces the CodeQuality copy), 'skip' = leave both: ").strip().lower()
        if answer == "dest":
            replace(live, repo_copy)
            state[str(live)] = fingerprint(live)
            print(f"  CodeQuality copy replaced with the destination version ({repo_copy.relative_to(REPO)})")
        elif answer == "skip":
            print("  Left alone.")
        else:
            back_up(live, backup_root)
            replace(repo_copy, live)
            state[str(live)] = fingerprint(live)
            written.append(live)
            print("  Destination replaced with the CodeQuality version.")
    return written


def is_terminal() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not is_terminal():
        print("This must be run by a person in a terminal. Refusing.")
        return 1

    if has_uncommitted_changes(REPO):
        if not args.dry_run:
            print("This repo has uncommitted changes. Commit them first, then run the sync again.")
            return 1
        print("Note: this repo has uncommitted changes, so a real sync would stop. Commit them first.\n")

    state = load_state()
    plan, held = only_clean_repos(build_plan())
    groups: dict[str, list[tuple[Path, Path]]] = {"create": [], "update": [], "conflict": [], "same": []}
    for repo_copy, live in plan:
        groups[classify(repo_copy, live, state)].append((repo_copy, live))
    for folder, reason in sorted(held.items()):
        print(f"held back: {folder} ({reason})")

    safe = groups["create"] + groups["update"]
    for repo_copy, live in safe:
        verb = "create " if not live.exists() else "replace"
        print(f"{verb}  {live}   <- {repo_copy.relative_to(REPO)}")
    if not safe and not groups["conflict"]:
        print("Everything is already in sync.")
    if args.dry_run:
        if groups["conflict"]:
            print(f"\n{len(groups['conflict'])} file(s) would need your decision:")
            for repo_copy, live in groups["conflict"]:
                show_conflict(repo_copy, live, state)
        return 0

    if safe and input(f"\nApply {len(safe)} change(s) and commit them in each project? Type 'yes': ").strip() != "yes":
        print("Cancelled.")
        return 1

    backup_root = HOME_CLAUDE / "backups" / f"sync-{datetime.now():%Y%m%d-%H%M%S}"
    written = [live for _, live in safe]
    for repo_copy, live in safe:
        back_up(live, backup_root)
        copy(repo_copy, live)
        state[str(live)] = fingerprint(live)
    for _, live in groups["same"]:
        state.setdefault(str(live), fingerprint(live))  # start watching it for outside edits

    if groups["conflict"]:
        written += resolve_conflicts(groups["conflict"], state, backup_root)
    save_state(state)
    commit_written(written)
    if has_uncommitted_changes(REPO):
        print("\nThis repo now has uncommitted changes (from choosing 'dest'). Commit them when you are ready.")
    if backup_root.exists():
        print(f"\nOld versions saved in {backup_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
