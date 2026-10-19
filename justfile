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

# Run the tests
test:
    uv run python -m pytest tests
