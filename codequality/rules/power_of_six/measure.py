import os

from ...models import IGNORED_FOLDERS
from ...source_code import SUFFIX_LANGUAGE
from .find_functions import find_functions


def parse_source_files(project):
    """Maps each Rust/TypeScript file to the functions found in it."""
    return {
        project.label_for(path): find_functions(path.read_text(errors="ignore"), SUFFIX_LANGUAGE[path.suffix])
        for path in project.files(*SUFFIX_LANGUAGE)
    }


def functions_per_file(project):
    return {file: len(infos) for file, infos in parse_source_files(project).items()}


def per_function(project, attribute):
    return {
        f"{file}:{info.line_number} {info.name}": getattr(info, attribute)
        for file, infos in parse_source_files(project).items()
        for info in infos
    }


def items_per_folder(project):
    counts = {}
    for folder, subfolders, names in os.walk(project.root):
        subfolders[:] = [s for s in subfolders if s not in IGNORED_FOLDERS and not s.startswith(".")]
        counts[project.label_for(folder)] = len([n for n in subfolders + names if not n.startswith(".")])
    return counts
