# CodeQuality

Your coding rules in `RULES.md`, plus a script that grades any project against them.

## Usage

    python -m codequality /path/to/project
    python -m codequality /path/to/project --json
    python -m codequality /path/to/project --min-score 80   # exit 1 if below

## Ignoring files

Put a `.codequalityignore` in the project root: one wildcard per line, `#` for comments, and a folder name skips everything inside it.
Follow the wildcard with rule IDs to skip it for those rules only, e.g. `tests RULE-09` (an ID matches every rule that starts with it).
`--exclude PATTERN` does the same from the command line. `.gitignore` is respected too.

## How it works

1. `detect.py` figures out the languages (Python, Rust, TypeScript, Go, C, C#, Mojo, Fortran, Hare, Rexx, Deor) and frameworks in the project.
2. Every rule that applies is run. Each returns a score from 0.0 to 1.0 plus a message.
3. `report.py` prints per-rule grades and an overall weighted score.

## Adding a rule

1. Write it up in `RULES.md` with an ID (e.g. `RUST-003`).
2. Add a function in `codequality/rules/` using the `@rule(...)` decorator with the same ID.
   Rules that can't be checked by code should use `checkable="manual"` and show up as "manual review".

## Layout

    RULES.md                    the rules, written for humans
    codequality/
      cli.py                    command line entry
      detect.py                 language + framework detection
      models.py                 Rule, Result, Status
      registry.py               @rule decorator and rule lookup
      report.py                 text/JSON output and scoring
      rules/common.py           language-agnostic rules
      rules/rust.py             Rust rules + axum/actix/tauri
      rules/typescript.py       TS rules + react/next/express/nest
    tests/                      grouped into folders: rules_01_to_04, rules_05_to_09, rules_10_to_14, languages, project
