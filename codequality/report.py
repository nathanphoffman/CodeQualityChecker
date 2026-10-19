from __future__ import annotations

import json
import sys

from .models import Project, Result, Rule, Status


def run(project: Project, rules: list[Rule]) -> list[tuple[Rule, Result]]:
    results = []
    for r in rules:
        if not r.applies_to(project):
            continue
        if r.checkable == "manual":
            results.append((r, Result.manual("needs human review")))
            continue
        try:
            results.append((r, r.check(project)))
        except Exception as e:  # a broken check shouldn't kill the whole run
            results.append((r, Result(Status.SKIPPED, 0.0, f"check crashed: {e}")))
    return results


def overall_score(results: list[tuple[Rule, Result]]) -> float:
    graded = [(r, res) for r, res in results if res.status not in (Status.MANUAL, Status.SKIPPED)]
    total = sum(r.weight for r, _ in graded)
    if not total:
        return 100.0
    return 100.0 * sum(r.weight * res.score for r, res in graded) / total


def letter(score: float) -> str:
    for cutoff, grade in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
        if score >= cutoff:
            return grade
    return "F"


# ANSI colors, left empty when output is piped or redirected so files and JSON stay clean.
USE_COLOR = sys.stdout.isatty()
GREEN, YELLOW, RED, BOLD, DIM, RESET = ("\033[" + code + "m" if USE_COLOR else "" for code in ("32", "33", "31", "1", "2", "0"))
STATUS_COLORS = {Status.PASS: GREEN, Status.PARTIAL: YELLOW, Status.FAIL: RED}


def print_rule(r: Rule, res: Result) -> None:
    color = STATUS_COLORS.get(res.status, DIM)
    print(f"{color}{res.status.value.upper():7}{RESET} {BOLD}{r.id}{RESET}  {r.title}  ({res.score:.0%})")
    if res.message:
        print(f"{DIM}        {res.message}{RESET}")
    print()


def print_text(project: Project, results: list[tuple[Rule, Result]]) -> None:
    print(f"Project: {project.root}")
    print(f"Languages: {', '.join(sorted(project.languages)) or 'none detected'}")
    print(f"Frameworks: {', '.join(sorted(project.frameworks)) or 'none detected'}\n")
    for r, res in results:
        print_rule(r, res)
    score = overall_score(results)
    manual = sum(1 for _, res in results if res.status == Status.MANUAL)
    print(f"\nScore: {score:.1f} ({letter(score)})   manual-review rules: {manual}")


def to_json(project: Project, results: list[tuple[Rule, Result]]) -> str:
    score = overall_score(results)
    return json.dumps({
        "project": str(project.root),
        "languages": sorted(project.languages),
        "frameworks": sorted(project.frameworks),
        "score": round(score, 1),
        "grade": letter(score),
        "rules": [
            {"id": r.id, "title": r.title, "severity": r.severity, "status": res.status.value,
             "score": res.score, "message": res.message}
            for r, res in results
        ],
    }, indent=2)
