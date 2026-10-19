import re

PYTHON, RUST, TYPESCRIPT = "python", "rust", "typescript"
TYPESCRIPT_SUFFIXES = (".ts", ".tsx")
SUFFIX_LANGUAGE = {".py": PYTHON, ".rs": RUST, ".ts": TYPESCRIPT, ".tsx": TYPESCRIPT}
TSCONFIG_FILE = "tsconfig.json"
NAME_GROUP, PAREN_GROUP = "name", "paren"  # names of the groups in the regexes that find functions and declarations
# Tests may fake secrets, call unsafe things and repeat themselves on purpose, so some rules only judge real code.
TEST_FOLDERS = {"tests", "test", "__tests__", "fixtures"}
BRACKET_PAIRS = {"(": ")", "{": "}", "[": "]"}

# Clever on purpose: matches comments and string literals so we can blank them out.
# Otherwise braces inside text would confuse the brace counting.
TEXT_PATTERN = re.compile(r"//[^\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`", re.S)


def blank_out_text(source):
    """Replace comments and strings with spaces, keeping newlines so line numbers still match."""
    # each comment or string found is rewritten with every character except newlines turned into a space
    return TEXT_PATTERN.sub(lambda hit: re.sub(r"[^\n]", " ", hit.group()), source)


def matching_close(text, open_index):
    open_char = text[open_index]
    close_char = BRACKET_PAIRS[open_char]
    depth = 0
    for index in range(open_index, len(text)):
        depth += (text[index] == open_char) - (text[index] == close_char)
        if depth == 0:
            return index
    return None


def line_number_at(text, index):
    return text.count("\n", 0, index) + 1


def non_test_files(project, suffixes):
    """Project files with these suffixes, outside test folders."""
    return [path for path in project.files(*suffixes) if not TEST_FOLDERS & set(path.relative_to(project.root).parts)]


def read_source(path):
    """The text of a file. Bytes that are not valid text are skipped instead of stopping the run."""
    return path.read_text(errors="ignore")


def items_in_project(project, for_python, for_tree):
    """[(file label, item)] from every non-test source file: Python read by for_python(source), others by for_tree(source, language)."""
    found = []
    for path in non_test_files(project, SUFFIX_LANGUAGE):
        language = SUFFIX_LANGUAGE[path.suffix]
        source = read_source(path)
        items = for_python(source) if language == PYTHON else for_tree(source, language)
        found += [(project.label_for(path), item) for item in items]
    return found
