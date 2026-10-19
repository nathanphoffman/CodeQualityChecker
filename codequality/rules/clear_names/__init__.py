"""Rule 2: Clear names. Longer and clearer beats short and vague; no acronyms an intern wouldn't know."""
from ...registry import rule
from .find_names import names_in_project
from .judge_names import grade_names, has_unknown_acronym, is_too_short


@rule("RULE-02-NAME-LENGTH", "Names are long enough to explain themselves")
def check_name_length(project):
    names = names_in_project(project)
    result = grade_names(names, is_too_short, "are too short")
    if names:
        result.message = f"average length {sum(map(len, names)) / len(names):.1f}; {result.message}"
    return result


@rule("RULE-02-NO-ACRONYMS", "No unfamiliar acronyms in names")
def check_acronyms(project):
    return grade_names(names_in_project(project), has_unknown_acronym, "contain an acronym")
