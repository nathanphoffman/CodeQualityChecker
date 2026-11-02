# Global instructions for Claude Code
- Do not EVER prompt me with multiple choice, use plain english questions
- Use language that a regular mid level developer would understand, don't assume I am a expert.
  - Keep responses short. Answer the question asked, then stop.
  - Don't restate my question back to me.
  - Don't add "why this matters" or "worth knowing" sections I didn't ask for.
  - Don't pre-empt follow-up questions. I'll ask.
  - After finishing work, list what changed in a few lines. No recap of the reasoning.
  - If a full answer needs more than ~10 lines, give me the short version and ask if I want detail.

# Git and files
- Never commit or push unless I ask.
- Ask before deleting files.
- Before deleting a folder, name the exact folders and ask me if it is ok. Don't just say "the folders".

# Running checks
- Run tests, linters and builds in the foreground, not in the background. Save the output to a log file and read it before moving on.
- Never commit with a check result you haven't seen.
- If a test fails only when run with others but passes alone, tell me it's flaky instead of re-running it again and again.

# Tools
- Use `uv` for Python, not `pip`.
- If a project has a `justfile`, use its recipes instead of typing the raw commands.

# Config sync script
- NEVER run `scripts/sync_claude.py` or `just sync` (or any variant, including `--dry-run`). It overwrites my Claude config. Only I run it, from my own terminal.
- If config needs to change, edit the files under `claude/` in the CodeQuality repo and tell me to run the sync myself.

# Personal instructions (not in the public repo)
@~/.claude/private.md
