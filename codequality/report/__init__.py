from ..models import Project, Result, Rule, Status
from .grouping import group_results, letter, overall_score  # noqa: F401  (used by the command line)
from .json_output import to_json  # noqa: F401
from .text_output import print_text  # noqa: F401


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
