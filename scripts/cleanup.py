"""Format, lint, grade and clean up a project, with one Claude agent per project.

    uv run python scripts/cleanup.py PATH              clean up one project
    uv run python scripts/cleanup.py --all             every project in claude/projects.toml
    uv run python scripts/cleanup.py --all --parallel 3
    uv run python scripts/cleanup.py PATH --plan       show what would run, change nothing

For each project:
  1. Skip the project if git has uncommitted changes (the formatters would mix with them) and tell you to commit first.
  2. Run the formatters and auto-fixers for the languages found (tools that are not installed are skipped).
  3. Grade the project with codequality, run the checks (linters, type checks, security scans) and save it all as one report.
  4. Start `claude -p` in the project with instructions to raise the score. It never pushes.
  5. Grade again and print the score before and after.
"""
import argparse
import json
import subprocess
import sys
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from codequality.detect import detect, tooling_languages  # noqa: E402

SCORE_MINIMUM = 85
SCORE_PREFERRED = 90
SCORE_IDEAL = 95
MAX_PASSES = 5  # stop after this many grade-and-fix rounds so a stubborn score cannot loop forever

# Clippy lints switched on for cleanup (the thresholds are in claude/linters/rust/clippy.toml). Turn crash-prone calls like unwrap into
# codequality rules, not lints here.
RUST_LINTS = ["-W", "clippy::too_many_arguments", "-W", "clippy::too_many_lines", "-W", "clippy::excessive_nesting",
              "-W", "clippy::fn_params_excessive_bools", "-W", "clippy::min_ident_chars", "-W", "unused"]

# Tools installed in this repo (uv for the Python ones, npm for biome and tsc), so every project is checked with the same versions.
# They run with the project as the working folder, so they still pick up that project's own config files.
PYTHON_TOOL = ["uv", "run", "--quiet", "--project", str(REPO)]
BIOME = str(REPO / "node_modules" / ".bin" / "biome")
TSC = str(REPO / "node_modules" / ".bin" / "tsc")
GOLANGCI = str(REPO / ".tools" / "bin" / "golangci-lint")  # installed with: GOBIN=$PWD/.tools/bin go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest
GOVULNCHECK = str(REPO / ".tools" / "bin" / "govulncheck")

# Fixers: run in the project folder, in order, for each language found. A command whose program is missing is skipped.
FORMATTERS = {
    "rust": [["cargo", "clippy", "--fix", "--allow-dirty", "--allow-staged", "--", *RUST_LINTS], ["cargo", "fmt"]],  # fmt last, to tidy what clippy rewrote
    "python": [[*PYTHON_TOOL, "ruff", "format", "."], [*PYTHON_TOOL, "ruff", "check", "--fix", "."]],
    "typescript": [[BIOME, "check", "--write", "."]],
    "go": [[GOLANGCI, "fmt"], [GOLANGCI, "run", "--fix"]],  # fmt also sorts and groups imports and drops unused ones
    "csharp": [["dotnet", "format"]],
    "javascript": [[BIOME, "check", "--write", "."]],
    "css": [[BIOME, "check", "--write", "."]],
    "html": [[BIOME, "check", "--write", "."]],
    "vue": [[BIOME, "check", "--write", "."]],
    "sql": [[*PYTHON_TOOL, "sqlfluff", "fix", "--force", "{files:.sql}"]],
    "c": [[*PYTHON_TOOL, "clang-format", "-i", "{files:.c,.h}"]],
    "cpp": [[*PYTHON_TOOL, "clang-format", "-i", "{files:.cpp,.cc,.cxx,.hpp,.hh,.hxx}"]],
    "shell": [["shfmt", "-i", "4", "-w", "{files:.sh,.bash}"]],  # shfmt takes its settings from flags, so it does not fight .editorconfig
}

# Checks: change nothing. Their output goes into the report so the agent sees what is left, including security scans and type checks.
# "all" runs for every project.
CHECKS = {
    "rust": [["cargo", "clippy", "--all-targets", "--", *RUST_LINTS], ["cargo", "audit"]],
    "python": [[*PYTHON_TOOL, "ruff", "check", "."], [*PYTHON_TOOL, "mypy", ".", "--ignore-missing-imports"],  # the project's libraries are not installed here
               [*PYTHON_TOOL, "bandit", "-r", ".", "-q"], [*PYTHON_TOOL, "pip-audit"]],
    "typescript": [[BIOME, "check", "."], [TSC, "--noEmit"], ["npm", "audit", "--omit=dev"]],
    "go": [[GOLANGCI, "run"], [GOVULNCHECK, "./..."]],
    "csharp": [["dotnet", "build", "--no-incremental", "-p:EnforceCodeStyleInBuild=true", "-p:GenerateDocumentationFile=true", "-p:NoWarn=CS1591"], ["dotnet", "list", "package", "--vulnerable"]],
    "c": [[*PYTHON_TOOL, "clang-tidy", "{files:.c}", "--"]],  # C++ is not checked: clang-tidy needs the project's include paths
    "javascript": [[BIOME, "check", "."]],
    "css": [[BIOME, "check", "."]],
    "html": [[BIOME, "check", "."]],
    "vue": [[BIOME, "check", "."]],
    "sql": [[*PYTHON_TOOL, "sqlfluff", "lint", "{files:.sql}"]],
    "shell": [["shellcheck", "{files:.sh,.bash}"]],
    "all": [["gitleaks", "detect", "--no-banner"]],
}
CHECK_LINES_KEPT = 300  # per command, so one noisy tool cannot bury the rest of the report

# What the agent may run without asking. Anything else is refused because the agent runs unattended.
AGENT_ALLOWED_TOOLS = [
    "Read", "Edit", "Write", "Glob", "Grep",
    "Bash(git status:*)", "Bash(git diff:*)", "Bash(git add:*)", "Bash(git commit:*)", "Bash(git log:*)",
    "Bash(cargo:*)", "Bash(npm:*)", "Bash(npx:*)", "Bash(pytest:*)", "Bash(ruff:*)", "Bash(go:*)", "Bash(dotnet:*)", "Bash(just:*)",
    f"Bash({sys.executable} -m codequality:*)", "Bash(uv run:*)", f"Bash({BIOME}:*)", f"Bash({TSC}:*)", f"Bash({GOLANGCI}:*)",
]
AGENT_DENIED_TOOLS = ["Bash(git push:*)", "Bash(git reset:*)", "Bash(git checkout:*)", "Bash(rm:*)"]

PROMPT = """You are cleaning up this project so it scores higher against the CodeQuality rules.

The full report is in {report}: the CodeQuality grade, then linter, type-check and security-scan output. Fix the lowest-scoring rules first. To grade again, run:
    {grade_command}

Score targets: {minimum} is the minimum, {preferred} is preferred, {ideal} is ideal. Keep going until you reach {preferred}, and
stop there unless {ideal} is cheap. Do at most {passes} rounds of fix-then-grade.

Rules for the work:
- Do not change behaviour. Tidy-ups only, and never mix a behaviour change in.
- Build and run the tests after each round. If something breaks, undo that change and leave the rule alone.
- Make a git commit per rule or group of fixes with a short message. Never push, never switch branches.
- Do not game the score: no deleting code or tests just to satisfy a check, and no changing the rules or ignore file.
- Follow this project's CLAUDE.md.
- When you finish, say the score before and after, and list anything you could not fix and why. A few lines.
"""


def say(name: str, message: str) -> None:
    print(f"[{name}] {message}", flush=True)


def run(command: list[str], folder: Path, **options) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=folder, text=True, capture_output=True, **options)


def grade_command(project: Path) -> list[str]:
    return [sys.executable, "-m", "codequality", str(project)]


def grade_score(project: Path) -> float | None:
    done = run(grade_command(project) + ["--json"], REPO)
    try:
        return json.loads(done.stdout)["score"]
    except (ValueError, KeyError):
        return None


def languages_in(project: Path) -> list[str]:
    return sorted(tooling_languages(detect(project)))


def expand(command: list[str], project: Path) -> list[str] | None:
    """Replace a "{files:.sh,.bash}" word with the project's matching files. None when there are none, so the command is skipped."""
    expanded = []
    for word in command:
        if word.startswith("{files:"):
            found = detect(project).files(*word[len("{files:"):-1].split(","))
            if not found:
                return None
            expanded += [str(path) for path in found]
        else:
            expanded.append(word)
    return expanded


def commands_for(table: dict[str, list[list[str]]], project: Path, languages: list[str]) -> list[list[str]]:
    """The commands for these languages with file lists filled in. The same command is only run once."""
    commands = []
    for language in languages:
        for command in table.get(language, []):
            filled = expand(command, project)
            if filled and filled not in commands:
                commands.append(filled)
    return commands


def is_ready(name: str, project: Path) -> bool:
    """False when the project cannot be cleaned yet: not a git repository, or it has uncommitted changes."""
    if not (project / ".git").exists():
        say(name, "skipped: not a git repository")
        return False
    if run(["git", "status", "--porcelain"], project).stdout.strip():
        say(name, "skipped: you have uncommitted changes. Commit them first, then run the cleanup again.")
        return False
    return True


def short(command: list[str]) -> str:
    """The command as one line, with a long list of files cut short."""
    text = " ".join(Path(command[0]).name if index == 0 else word for index, word in enumerate(command))

    return text if len(text) <= 100 else text[:100] + " ..."


def run_formatters(name: str, project: Path, plan: bool) -> None:
    for command in commands_for(FORMATTERS, project, languages_in(project)):
        say(name, ("would run: " if plan else "running: ") + short(command))
        if plan:
            continue
        try:
            done = run(command, project)
        except FileNotFoundError:
            say(name, f"  {command[0]} is not installed, skipped")
            continue
        if done.returncode != 0:
            say(name, f"  {Path(command[0]).name} exited with {done.returncode}; the agent will see anything left")
    say(name, ("would fix spacing" if plan else "fixing spacing (RULE-14)"))
    if not plan:
        run(grade_command(project) + ["--fix-spacing"], REPO)


def run_checks(name: str, project: Path) -> str:
    """Run every check for the languages found and return their output as report text."""
    sections = []
    for command in commands_for(CHECKS, project, [*languages_in(project), "all"]):
        try:
            done = run(command, project)
        except FileNotFoundError:
            sections.append(f"## {Path(command[0]).name}\nnot installed, skipped\n")
            continue
        lines = (done.stdout + done.stderr).splitlines()
        more = f"\n... {len(lines) - CHECK_LINES_KEPT} more lines" if len(lines) > CHECK_LINES_KEPT else ""
        sections.append(f"## {short(command)}  (exit {done.returncode})\n" + "\n".join(lines[:CHECK_LINES_KEPT]) + more + "\n")
    return "\n".join(sections)


def start_agent(name: str, project: Path, plan: bool) -> None:
    report = Path(tempfile.gettempdir()) / f"codequality-{name}-report.txt"
    log = Path(tempfile.gettempdir()) / f"codequality-{name}-agent.log"
    prompt = PROMPT.format(report=report, grade_command=" ".join(grade_command(project)), minimum=SCORE_MINIMUM,
                           preferred=SCORE_PREFERRED, ideal=SCORE_IDEAL, passes=MAX_PASSES)
    command = ["claude", "-p", "--permission-mode", "acceptEdits",
               "--allowedTools", *AGENT_ALLOWED_TOOLS, "--disallowedTools", *AGENT_DENIED_TOOLS]
    if plan:
        say(name, f"would grade into {report}, then run: {' '.join(command[:4])} ... (prompt on stdin)")
        return
    report.write_text(run(grade_command(project) + ["--full"], REPO).stdout + "\n# Linter, type and security checks\n\n" + run_checks(name, project))
    say(name, f"agent started (log: {log})")
    done = subprocess.run(command, cwd=project, input=prompt, text=True, capture_output=True)
    log.write_text(done.stdout + done.stderr)
    say(name, f"agent finished with exit code {done.returncode}")


def clean_project(name: str, project: Path, plan: bool) -> None:
    if not project.is_dir():
        say(name, f"skipped: {project} does not exist")
        return
    if not is_ready(name, project):
        return
    before = None if plan else grade_score(project)
    run_formatters(name, project, plan)
    start_agent(name, project, plan)
    if not plan:
        say(name, f"score: {before} -> {grade_score(project)}")


def projects_to_clean(args: argparse.Namespace) -> dict[str, Path]:
    if args.all:
        config = tomllib.loads((REPO / "claude" / "projects.toml").read_text())["projects"]
        return {name: Path(path).expanduser() for name, path in config.items()}
    project = args.path.resolve()
    return {project.name: project}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", type=Path, nargs="?", help="the project to clean up")
    parser.add_argument("--all", action="store_true", help="every project in claude/projects.toml")
    parser.add_argument("--parallel", type=int, default=1, help="how many projects at once (default 1)")
    parser.add_argument("--plan", action="store_true", help="show what would happen and change nothing")
    args = parser.parse_args()
    if not args.all and not args.path:
        parser.error("give a project path or --all")

    projects = projects_to_clean(args)
    with ThreadPoolExecutor(max_workers=max(args.parallel, 1)) as pool:
        for name, path in projects.items():
            pool.submit(clean_project, name, path, args.plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
