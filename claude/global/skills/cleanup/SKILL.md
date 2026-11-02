---
name: cleanup
description: Format, lint and grade this project (or every project with "all") against the CodeQuality rules, then hand the fixes to a Claude agent. Run it by typing /cleanup.
disable-model-invocation: true
---

Run the CodeQuality cleanup script. It does the work itself (formatters and linters, the grade, then one fixing agent per project), so do not fix code yourself.

- `/cleanup`: clean up the project in the current directory.
- `/cleanup all`: clean up every project listed in the CodeQuality repo's `claude/projects.toml`.

Run this from the project's folder:

    uv run --project ~/Code/CodeQuality python ~/Code/CodeQuality/scripts/cleanup.py "$PWD"

For `all`, run this instead:

    uv run --project ~/Code/CodeQuality python ~/Code/CodeQuality/scripts/cleanup.py --all

When it finishes, tell the user the score before and after, and anything it skipped and why (a project with uncommitted changes is skipped until the user commits them). Keep it to a few lines.
