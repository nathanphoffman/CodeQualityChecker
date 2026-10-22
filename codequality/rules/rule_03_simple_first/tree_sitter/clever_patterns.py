import re

from ....source_code import TYPESCRIPT, line_number_at

# Clever on purpose: one regex per kind of clever construct, run on text with strings and comments blanked.
#   regex:      building a regex always counts as clever
#   fold/reduce: accumulator pipelines, the classic "what does this do?" construct
#   iife:       a function defined and called at once. "(" must not follow a name, or it is just a call
#               whose first argument is an arrow function
#   bit_tricks: shifts and xor with spaces around them (unspaced ones are usually generics like Vec<Vec<u8>>)
#   macro/transmute: Rust metaprogramming and type punning, and C macros that take arguments
#   reflect/unsafe/goto: Go and C ways around the type system and the normal flow of the code
TEXT_PATTERNS = {
    "rust": {
        "regex": r"\bRegex(?:Builder|Set)?::new\s*\(|\bregex!\s*\(",

        "fold": r"\.\s*(?:fold|scan)\s*\(",
        "macro": r"\bmacro_rules!",
        "transmute": r"\btransmute\s*(?:::<[^>]*>)?\s*\(",
        "bit_tricks": r"\s(?:<<|>>|\^)\s",
    },

    "hare": {"bit_tricks": r"\s(?:<<|>>|\^)\s"},

    "c": {
        "macro": r"(?m)^[ \t]*#[ \t]*define[ \t]+\w+\(",  # a #define that takes arguments
        "goto": r"\bgoto\b",
        "bit_tricks": r"\s(?:<<|>>|\^)\s",
    },

    "csharp": {
        "regex": r"\bnew\s+Regex\s*\(|\bRegex\.\w+\s*\(",
        "reflection": r"\bActivator\.CreateInstance|\.GetMethod\s*\(|\.GetProperty\s*\(",
        "unsafe": r"\bunsafe\b",
        "goto": r"\bgoto\b",
        "bit_tricks": r"\s(?:<<|>>>?|\^)\s",
    },

    "mojo": {
        "walrus": r":=",
        "mlir": r"\b__mlir_\w+",  # writing compiler-level code by hand
        "bit_tricks": r"\s(?:<<|>>|\^)\s",
    },

    "fortran": {
        "goto": r"(?i)\bgo\s*to\b",
        "equivalence": r"(?i)\bequivalence\b",  # two names for the same memory
        "common": r"(?i)\bcommon\s*/",  # shared global memory
        "transfer": r"(?i)\btransfer\s*\(",  # reading memory as another type
    },

    "go": {
        "regex": r"\bregexp\.(?:MustCompile|Compile)\s*\(",
        "reflect": r"\breflect\.\w+",
        "unsafe": r"\bunsafe\.\w+",
        "goto": r"\bgoto\b",
        "bit_tricks": r"\s(?:<<|>>|\^|&\^)\s",
    },

    "typescript": {
        "regex": r"\bnew\s+RegExp\s*\(",
        "reduce": r"\.\s*reduce(?:Right)?\s*\(",
        "iife": r"(?<![\w)\]])\(\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*=>)",

        "bit_tricks": r"\s(?:<<|>>>?|\^)\s",
    },
}

# Clever on purpose: finds a TypeScript regex literal like /\d+/g. It must follow an operator, bracket or
# "return" (otherwise it is division), then runs to the next unescaped "/" (slashes inside [...] don't end it).
# Run on the original source because "//" inside a regex would otherwise look like a comment.
TS_REGEX_LITERAL = re.compile(
    r"(?:=>|[=(,:;!&|?{}\[]|\breturn)[ \t]*/(?![/*])(?:\\.|\[(?:\\.|[^\]\\\n])*\]|[^/\\\n\[])+/[a-z]*"
)

def pattern_hits(source, text, language):
    """Returns (kind, line_number) for every simple clever construct."""
    hits = []

    for kind, pattern in TEXT_PATTERNS[language].items():
        # every place this kind's pattern from TEXT_PATTERNS matches, as (kind, line)
        hits += [(kind, line_number_at(text, match.start())) for match in re.finditer(pattern, text)]

    if language == TYPESCRIPT:
        hits += [("regex", line_number_at(source, match.start())) for match in TS_REGEX_LITERAL.finditer(source)]

    return hits
