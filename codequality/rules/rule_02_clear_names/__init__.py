"""Rule 2: Clear names. Longer and clearer beats short and vague; no acronyms an intern wouldn't know."""
from ...registry import rule
from collections import Counter

from ...models import MAX_LISTED_OFFENDERS, Result
from .shared.find_names import kinded_names_by_language, names_in_project
from .shared.name_styles import best_convention, follows
from .shared.path_names import path_names_by_language
from .shared.judge_names import grade_names, has_unknown_acronym, is_too_short

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

@rule("RULE-02-NAMING-STYLE", "Names follow the language's naming style, or yours")
def check_naming_style(project):
    paths = path_names_by_language(project)
    by_language = {language: kinded + paths[language] for language, kinded in kinded_names_by_language(project).items()}
    total = sum(len(kinded) for kinded in by_language.values())

    if not total:
        return Result.passed("no names found")

    following, notes, breakers = 0, [], Counter()

    for language, kinded in by_language.items():
        if not kinded:
            continue

        label, convention, share = best_convention(kinded, language)
        following += round(share * len(kinded))
        notes.append(f"{language} follows {label} style {share:.0%}")
        breakers.update(name for name, kind in kinded if not follows(name, kind, convention))

    listed = ", ".join(f"{name} ({count})" for name, count in breakers.most_common(MAX_LISTED_OFFENDERS))

    return Result.scored(following / total, "; ".join(notes) + (f"; breaking it: {listed}" if listed else ""))
