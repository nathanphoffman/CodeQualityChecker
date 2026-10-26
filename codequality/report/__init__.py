from ..models import CHECK_MANUAL, Project, Result, Rule, Status
from .grouping import group_results, letter, overall_score  # noqa: F401  (used by the command line)
from .detail_output import print_full, print_quick  # noqa: F401
from .json_output import to_json  # noqa: F401
from .text_output import print_text  # noqa: F401

def run(project: Project, rules: list[Rule]) -> list[tuple[Rule, Result]]:
    results = []

    for rule in rules:
        if not rule.applies_to(project):
            continue

        if rule.checkable == CHECK_MANUAL:
            results.append((rule, Result.manual("needs human review")))

            continue

        project.current_rule = rule.id

        try:
            results.append((rule, rule.check(project)))
        except Exception as error:  # a broken check shouldn't kill the whole run
            results.append((rule, Result(Status.SKIPPED, 0.0, f"check crashed: {error}")))

    return results
