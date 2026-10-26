import re

from .find_names import kinded_names_by_file
from .name_styles import FILE, FOLDER, TYPE, TYPE_FILE

# a file or folder name made only of letters, digits, "_" and "-"; others like `+linux` or `.github` are not judged
JUDGED_NAME = re.compile(r"[A-Za-z0-9_-]+")

def squashed(name):
    """A name with its case and separators removed, so `User_Account`, `user-account` and `UserAccount` compare equal."""

    return re.sub(r"[_-]", "", name).lower()

def file_kind(stem, kinded):
    """TYPE_FILE when the file defines a type named like the file, else FILE."""
    defined_types = {squashed(name) for name, kind in kinded if kind == TYPE}

    return TYPE_FILE if squashed(stem) in defined_types else FILE

def path_names_by_language(project):
    """{language: [(name, kind), ...]} for the file and folder names of every source file. A folder is counted once per language that has files in it."""
    found = {}
    seen_folders = set()

    for path, (language, kinded) in kinded_names_by_file(project).items():
        parts = path.relative_to(project.root).parts
        stem = parts[-1].split(".")[0]  # `app.test.ts` is named `app`
        names = found.setdefault(language, [])

        if JUDGED_NAME.fullmatch(stem):
            names.append((stem, file_kind(stem, kinded)))

        for depth in range(1, len(parts)):
            folder = (language, parts[:depth])

            if folder not in seen_folders and JUDGED_NAME.fullmatch(parts[depth - 1]):
                seen_folders.add(folder)
                names.append((parts[depth - 1], FOLDER))

    return found
