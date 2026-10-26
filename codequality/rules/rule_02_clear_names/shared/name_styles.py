import re

from ....source_code import C_LANG, CSHARP, GO, HARE, MOJO, PYTHON, RUST, TYPESCRIPT

FUNCTION, TYPE, CONSTANT, VARIABLE, VALUE, VARIANT = "function", "type", "constant", "variable", "value", "variant"
# VALUE is an assignment that may be a constant or a variable, and VARIANT is a member of an enum

# Clever on purpose: one pattern per naming style, tested on a name with its leading and trailing underscores removed.
# A word is one letter followed by lower case letters and digits, so `UserAccount` is two words and `user_id` is two.
NAME_STYLES = {
    "lower_snake": re.compile(r"[a-z][a-z0-9]*(_[a-z0-9]+)*"),  # lower case words joined by "_"
    "SCREAMING_SNAKE": re.compile(r"[A-Z][A-Z0-9]*(_[A-Z0-9]+)*"),  # capital words joined by "_"
    "Pascal_Snake": re.compile(r"[A-Z][a-z0-9]*(_[A-Z][a-z0-9]*)*"),  # Capitalized words joined by "_"
    "camelCase": re.compile(r"[a-z][a-z0-9]*([A-Z][a-z0-9]*)*"),  # a lower case word, then Capitalized words joined with no "_"
    "PascalCase": re.compile(r"[A-Z][a-z0-9]*([A-Z][a-z0-9]*)*"),  # Capitalized words joined with no "_"
    "mixedCaps": re.compile(r"[A-Za-z][A-Za-z0-9]*"),  # Go: letters and digits only, no underscores
}

def style(*names):
    return tuple(names)

# Your rules from RULES.md: SCREAMING_SNAKE for constants, Pascal_Snake for structures, lower_snake for everything else.
MY_CONVENTION = {
    FUNCTION: style("lower_snake"),
    TYPE: style("Pascal_Snake"),
    CONSTANT: style("SCREAMING_SNAKE"),
    VARIABLE: style("lower_snake"),
    VALUE: style("lower_snake", "SCREAMING_SNAKE"),
    VARIANT: style("Pascal_Snake", "SCREAMING_SNAKE"),  # your rules name neither case, and a variant is both a constant and a structure
}

PYTHON_CONVENTION = {
    FUNCTION: style("lower_snake"),
    TYPE: style("PascalCase"),
    CONSTANT: style("SCREAMING_SNAKE"),
    VARIABLE: style("lower_snake"),
    VALUE: style("lower_snake", "SCREAMING_SNAKE"),
    VARIANT: style("PascalCase"),  # Rust: "Enum variants: UpperCamelCase" (RFC 430)
}

# Languages with no official style (Fortran, Rexx, Deor) are missing, so only MY_CONVENTION judges them.
LANGUAGE_CONVENTIONS = {
    PYTHON: PYTHON_CONVENTION,
    MOJO: PYTHON_CONVENTION,
    RUST: PYTHON_CONVENTION,
    TYPESCRIPT: {
        FUNCTION: style("camelCase", "PascalCase"),  # PascalCase for React components
        TYPE: style("PascalCase"),
        CONSTANT: style("camelCase", "PascalCase", "SCREAMING_SNAKE"),
        VARIABLE: style("camelCase"),
        VALUE: style("camelCase", "PascalCase", "SCREAMING_SNAKE"),
        VARIANT: style("PascalCase"),  # the TypeScript coding guidelines: "Use PascalCase for enum values"
    },
    HARE: {
        FUNCTION: style("lower_snake"),
        TYPE: style("lower_snake"),
        CONSTANT: style("SCREAMING_SNAKE"),  # the Hare style guide: "Constants MUST be named in UPPER_UNDERSCORE_CASE"
        VARIABLE: style("lower_snake"),
        VALUE: style("lower_snake", "SCREAMING_SNAKE"),
        VARIANT: style("SCREAMING_SNAKE"),  # the Hare style guide: "Members MUST be named in ALL_CAPS"
    },
    C_LANG: {  # K&R: lower case for variables and functions, upper case for symbolic constants
        FUNCTION: style("lower_snake"),
        TYPE: style("lower_snake"),
        CONSTANT: style("SCREAMING_SNAKE"),
        VARIABLE: style("lower_snake"),
        VALUE: style("lower_snake", "SCREAMING_SNAKE"),
        VARIANT: style("SCREAMING_SNAKE"),
    },
    GO: {kind: style("mixedCaps") for kind in MY_CONVENTION},  # Go writes constants in MixedCaps too
    CSHARP: {
        FUNCTION: style("PascalCase"),
        TYPE: style("PascalCase"),
        CONSTANT: style("PascalCase", "SCREAMING_SNAKE"),
        VARIABLE: style("camelCase", "PascalCase"),  # PascalCase for fields and constants, which share a node with locals
        VALUE: style("PascalCase"),
        VARIANT: style("PascalCase"),
    },
}

def follows(name, kind, convention):
    """True when the name is written in a style the convention allows for this kind of name. Leading and trailing underscores (`_private`, `__init__`) don't count."""
    bare = name.strip("_")

    return not bare or any(NAME_STYLES[allowed].fullmatch(bare) for allowed in convention[kind])

def share_following(kinded_names, convention):
    """The share (0 to 1) of (name, kind) pairs written in the convention's styles."""

    return sum(follows(name, kind, convention) for name, kind in kinded_names) / len(kinded_names)

def best_convention(kinded_names, language):
    """(label, convention, share) for whichever of the language's own style and yours fits better. Only one counts, so a name matching both is not rewarded twice."""
    candidates = [("your", MY_CONVENTION)]

    if language in LANGUAGE_CONVENTIONS:
        candidates.append((f"{language}'s", LANGUAGE_CONVENTIONS[language]))

    scored = [(share_following(kinded_names, convention), label, convention) for label, convention in candidates]
    share, label, convention = max(scored, key=lambda entry: entry[0])

    return label, convention, share
