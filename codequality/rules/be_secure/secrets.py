import fnmatch
import re

from ...models import IGNORED_FOLDERS, Result
from ...source_code import SUFFIX_LANGUAGE, non_test_files, read_source
from .limits import (CONFIG_SUFFIXES, MIN_SECRET_LENGTH, PLACEHOLDER_HINTS, SAFE_FILE_ENDINGS, SECRET_FILE_PATTERNS,
                     SECRET_WORDS)

# Clever on purpose: finds a secret word assigned a quoted value, like a password variable or a JSON "api_key" entry.
#   the secret word, then any other word characters, e.g. api_key or password_hash
#   an optional closing quote (JSON keys), then ":" or "=", then an opening quote
#   a value of MIN_SECRET_LENGTH or more characters with no spaces or quotes, which also rules out `== "x"` tests
SECRET_ASSIGNMENT = re.compile(
    rf"(?:{'|'.join(SECRET_WORDS)})\w*[\"']?\s*[:=]\s*[\"'](?P<value>[^\"'\s]{{{MIN_SECRET_LENGTH},}})[\"']",
    re.IGNORECASE,
)

# Clever on purpose: key formats that are secrets no matter what they are assigned to.
#   AKIA + 16 characters is an AWS access key, ghp_ + 36 is a GitHub token, sk- + 20 or more is an API key
#   the last alternative is the first line of a PEM private key file
KNOWN_KEY_FORMAT = re.compile(r"AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY")


def is_placeholder(value):
    return any(hint in value.lower() for hint in PLACEHOLDER_HINTS)


def secret_line_numbers(text):
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        assignment = SECRET_ASSIGNMENT.search(line)
        if KNOWN_KEY_FORMAT.search(line) or (assignment and not is_placeholder(assignment.group("value"))):
            found.append(number)
    return found


def hardcoded_secrets(project):
    """({file label: line numbers}, number of files scanned)."""
    paths = non_test_files(project, tuple(SUFFIX_LANGUAGE) + CONFIG_SUFFIXES)
    flagged = {}
    for path in paths:
        lines = secret_line_numbers(read_source(path))
        if lines:
            flagged[project.label_for(path)] = lines
    return flagged, len(paths)


def is_covered_by_gitignore(label, ignore_lines):
    patterns = [line.strip().strip("/") for line in ignore_lines if line.strip() and not line.startswith("#")]
    return any(fnmatch.fnmatch(label, pattern) or fnmatch.fnmatch(label.split("/")[-1], pattern) for pattern in patterns)


def is_secret_file(project, path):
    """A key or .env file in a real folder. Example and template files don't count."""
    in_ignored_folder = IGNORED_FOLDERS & set(path.relative_to(project.root).parts)
    has_secret_name = any(fnmatch.fnmatch(path.name, pattern) for pattern in SECRET_FILE_PATTERNS)
    return path.is_file() and has_secret_name and not in_ignored_folder and not path.name.endswith(SAFE_FILE_ENDINGS)


def secret_files(project):
    """Key and .env files that are not ignored by .gitignore, so they could be committed."""
    ignore_file = project.root / ".gitignore"
    ignore_lines = read_source(ignore_file).splitlines() if ignore_file.exists() else []
    labels = [project.label_for(path) for path in sorted(project.root.rglob("*")) if is_secret_file(project, path)]
    return [label for label in labels if not is_covered_by_gitignore(label, ignore_lines)]


def judge_secret_files(project):
    found = secret_files(project)
    return Result.failed(f"{len(found)} not in .gitignore: {', '.join(found)}") if found else Result.passed()
