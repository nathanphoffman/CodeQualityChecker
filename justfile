# Run `just` with no arguments to list recipes.
default:
    @just --list

# Grade a project against all rules. Defaults to this project.
check path=".":
    uv run python -m codequality {{path}}

# Run only one rule (or any ID prefix), e.g. `just rule RULE-03` or `just rule RULE-03 ../other-project`
rule id path=".":
    uv run python -m codequality {{path}} --only {{id}}

# Output JSON instead of text
json path=".":
    uv run python -m codequality {{path}} --json

# Exit with an error if the score is below the minimum (default 80)
gate path="." min="80":
    uv run python -m codequality {{path}} --min-score {{min}}

# Compare this project's score with an earlier commit, branch or tag, e.g. `just compare main`
compare ref path=".":
    uv run python -m codequality {{path}} --compare {{ref}}

# Run the tests
test:
    uv run python -m pytest tests

# Copy claude/ config onto this machine (run by hand in a terminal; Claude must never run this)
sync *args:
    uv run python scripts/sync_claude.py {{args}}

# Build each project's CLAUDE.md from claude/claude-md-pieces/ into claude/projects/ (then deploy with `just sync`)
build *names:
    uv run python scripts/build_claude.py {{names}}

# Format, lint, grade and clean up a project with one Claude agent per project: `just cleanup ~/Code/myapp`, `just cleanup --all`, add `--plan` to preview
cleanup *args:
    uv run python scripts/cleanup.py {{args}}
