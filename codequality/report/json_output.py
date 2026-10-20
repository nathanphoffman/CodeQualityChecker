import json

from .grouping import PERCENT, group_results, letter, overall_score

SCORE_KEY = "score"

def to_json(project, results):
    score = overall_score(results)

    return json.dumps({
        "project": str(project.root),
        "languages": sorted(project.languages),
        "frameworks": sorted(project.frameworks),
        SCORE_KEY: round(score, 1),
        "grade": letter(score),

        "groups": [
            {"id": group.key, "title": group.title, SCORE_KEY: group.score,
             "grade": letter(group.score * PERCENT) if group.score is not None else None}
            for group in group_results(results)
        ],

        "rules": [
            {"id": rule.id, "title": rule.title, "severity": rule.severity, "status": result.status.value,
             SCORE_KEY: result.score, "message": result.message}
            for rule, result in results
        ],
    }, indent=2)
