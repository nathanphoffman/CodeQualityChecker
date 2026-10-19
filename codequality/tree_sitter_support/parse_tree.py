import warnings

import tree_sitter_rust
import tree_sitter_typescript
from tree_sitter import Language, Parser

GRAMMARS = {"rust": tree_sitter_rust.language, "typescript": tree_sitter_typescript.language_typescript}


def parse_tree(source, language):
    """Root node of the syntax tree. Like parse_python, it warns when the source has errors."""
    parser = Parser(Language(GRAMMARS[language]()))
    root = parser.parse(source.encode()).root_node
    if root.has_error:
        warnings.warn(f"{language} source has syntax errors; its results may be incomplete")
    return root
