from ...models import MAX_LISTED_OFFENDERS, Result
from .call_checks import ANY_NAME
from .uses import uses_in_project


def name_matches(use_name, entry_name):
    if entry_name in (ANY_NAME, use_name):
        return True
    return "." in entry_name and use_name.endswith("." + entry_name)


def matches_entry(use, entry):
    return (name_matches(use.name, entry.name)
            and use.text.startswith(entry.prefix)
            and all(part in use.text for part in entry.must_contain)
            and not any(part in use.text for part in entry.must_not_contain))


def mentions_any(words, haystacks):
    """True when no words were asked for, or any haystack contains one of them."""
    if not words:
        return True
    for haystack in haystacks:
        if any(word in haystack for word in words):
            return True
    return False


def is_finding(use, check, language):
    if not any(matches_entry(use, entry) for entry in check.entries[language]):
        return False
    return mentions_any(check.names_words, use.names) and mentions_any(check.line_words, [use.line_text])


def grade_findings(flagged, file_count):
    """flagged maps a file label to the line numbers with findings. Score is the share of files with none."""
    if not file_count:
        return Result.passed("no files found")
    places = []
    for label, lines in flagged.items():
        places += [f"{label}:{line}" for line in lines]
    listed = ", ".join(places[:MAX_LISTED_OFFENDERS])
    message = f"{len(places)} found in {len(flagged)} of {file_count} files: {listed}" if flagged else ""
    return Result.scored(1 - len(flagged) / file_count, message)


def run_call_check(check, project):
    files = uses_in_project(project)
    flagged = {}
    for label, language, uses in files:
        lines = sorted({use.line_number for use in uses if is_finding(use, check, language)})
        if lines:
            flagged[label] = lines
    return grade_findings(flagged, len(files))
