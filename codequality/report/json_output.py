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
            {"id": r.id, "title": r.title, "severity": r.severity, "status": res.status.value,
             SCORE_KEY: res.score, "message": res.message}
            for r, res in results
        ],
    }, indent=2)
