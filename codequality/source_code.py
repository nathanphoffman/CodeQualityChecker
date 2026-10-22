import re
import warnings

PYTHON, RUST, TYPESCRIPT, DEOR, HARE, C_LANG, GO, MOJO, FORTRAN, CSHARP = ("python", "rust", "typescript", "deor", "hare", "c", "go",
                                                                         "mojo", "fortran", "csharp")
TYPESCRIPT_SUFFIXES = (".ts", ".tsx")
SUFFIX_LANGUAGE = {".py": PYTHON, ".rs": RUST, ".ts": TYPESCRIPT, ".tsx": TYPESCRIPT, ".deor": DEOR, ".ha": HARE, ".c": C_LANG, ".h": C_LANG,
                   ".go": GO, ".cs": CSHARP, ".mojo": MOJO, ".🔥": MOJO,
                   ".f90": FORTRAN, ".F90": FORTRAN, ".f95": FORTRAN, ".f03": FORTRAN, ".f08": FORTRAN}
TSCONFIG_FILE = "tsconfig.json"
GO_TEST_SUFFIX = "_test.go"  # Go keeps its tests beside the code, in files named like this
TEST_FILE_SUFFIXES = (GO_TEST_SUFFIX, "Tests.cs", "Test.cs")  # and C# test files are named after the class they test
NAME_GROUP, PAREN_GROUP = "name", "paren"  # names of the groups in the regexes that find functions and declarations

# Tests may fake secrets, call unsafe things and repeat themselves on purpose, so some rules only judge real code.
TEST_FOLDERS = {"tests", "test", "__tests__", "fixtures"}
BRACKET_PAIRS = {"(": ")", "{": "}", "[": "]"}

# Clever on purpose: matches comments and string literals so we can blank them out.
# Otherwise braces inside text would confuse the brace counting.
TEXT_PATTERN = re.compile(r"//[^\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`", re.S)

# Mojo has # comments and triple-quoted strings. Fortran has ! comments and doubles a quote to put one inside a string.
# Its // is an operator (joining strings), not a comment, so it must be left alone.
LANGUAGE_TEXT_PATTERNS = {
    MOJO: re.compile(r"#[^\n]*|\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'", re.S),
    FORTRAN: re.compile(r"![^\n]*|\"(?:\"\"|[^\"\n])*\"|'(?:''|[^'\n])*'"),
}

def blank_out_text(source, language=None):
    """Replace comments and strings with spaces, keeping newlines so line numbers still match."""
    pattern = LANGUAGE_TEXT_PATTERNS.get(language, TEXT_PATTERN)

    # each comment or string found is rewritten with every character except newlines turned into a space
    return pattern.sub(lambda hit: re.sub(r"[^\n]", " ", hit.group()), source)

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

    return [path for path in project.files(*suffixes)
            if not TEST_FOLDERS & set(path.relative_to(project.root).parts) and not path.name.endswith(TEST_FILE_SUFFIXES)]

def read_source(path):
    """The text of a file. A file that is not valid UTF-8 is skipped with a warning, not half-read."""

    try:
        return path.read_text()
    except UnicodeDecodeError as error:
        warnings.warn(f"skipped {path}: not valid UTF-8 ({error})")

        return ""

def items_in_project(project, for_python, for_tree):
    """[(file label, item)] from every non-test source file: Python read by for_python(source), others by for_tree(source, language)."""
    found = []

    for path in non_test_files(project, SUFFIX_LANGUAGE):
        language = SUFFIX_LANGUAGE[path.suffix]
        source = read_source(path)
        items = for_python(source) if language == PYTHON else for_tree(source, language)
        found += [(project.label_for(path), item) for item in items]

    return found
