import warnings
from functools import lru_cache

import tree_sitter_hare
import tree_sitter_rust
import tree_sitter_typescript
from tree_sitter import Language, Parser

# Grammars to try in order. TypeScript falls back to TSX so files with JSX parse without errors.
GRAMMARS = {
    "hare": [tree_sitter_hare.language],
    "rust": [tree_sitter_rust.language],
    "typescript": [tree_sitter_typescript.language_typescript, tree_sitter_typescript.language_tsx],
}

MAX_CACHED_FILES = 2048  # every rule parses every file, so keeping the trees means each file is parsed once per run

@lru_cache(maxsize=MAX_CACHED_FILES)
def parse_tree(source, language):
    """Root node of the syntax tree. Like parse_python, it warns when the source has errors."""

    for grammar in GRAMMARS[language]:
        root = Parser(Language(grammar())).parse(source.encode()).root_node

        if not root.has_error:
            return root

    warnings.warn(f"{language} source has syntax errors; its results may be incomplete")

    return root

@lru_cache(maxsize=MAX_CACHED_FILES)
def has_clean_parse(source, language):
    """True when the text parses as code with no errors. Unlike parse_tree, it never warns."""

    return any(not Parser(Language(grammar())).parse(source.encode()).root_node.has_error for grammar in GRAMMARS[language])
