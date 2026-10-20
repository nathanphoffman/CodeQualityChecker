import ast

from ..extract.deor_comments import looks_like_deor
from ....source_code import DEOR, PYTHON
from ....language_parsers.tree_sitter.parse_tree import has_clean_parse
from ...clear_names.judge_names import WORD_PATTERN
from ..limits import CODE_SYMBOLS, STOP_WORDS, WHY_PHRASES

STEM_ENDINGS = ("ing", "ed", "es", "s")
MIN_STEMMED_LENGTH = 3
CODE_CHARACTERS = "=;{}"

def words_of(text):
    """Lower-case words, with camelCase and snake_case split apart."""

    return [word.lower() for word in WORD_PATTERN.findall(text)]

def stem(word):
    for ending in STEM_ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= MIN_STEMMED_LENGTH:
            return word[:-len(ending)]

    return word

def content_words(text):
    return {stem(word) for word in words_of(text) if word not in STOP_WORDS and not word.isdigit()}

def overlap_ratio(comment_text, code_text):
    """Share of the comment's meaningful words that also appear in the code."""
    comment_words = content_words(comment_text)

    if not comment_words:
        return 0.0

    return len(comment_words & content_words(code_text)) / len(comment_words)

def has_code_symbols(text):
    """Code symbols outside backticks. Quoting code in backticks is explaining, not copying."""
    outside_backticks = "".join(text.split("`")[::2])

    return any(symbol in outside_backticks for symbol in CODE_SYMBOLS)

def mentions_reason(text):
    padded = " " + " ".join(words_of(text)) + " "

    return "://" in text or any(f" {phrase} " in padded for phrase in WHY_PHRASES)

def has_code_shape(text):
    """Cheap check before parsing: an assignment, a semicolon, braces, or a call like f(x) with no space before the (."""

    if any(character in text for character in CODE_CHARACTERS):
        return True

    paren = text.find("(")

    return paren > 0 and text[paren - 1] != " "

def is_commented_out_code(text, language):
    if not has_code_shape(text):
        return False

    if language == DEOR:
        return looks_like_deor(text)

    if language != PYTHON:
        return has_clean_parse(text, language)

    try:
        return bool(ast.parse(text).body)  # text that is itself a # comment parses to nothing
    except (SyntaxError, ValueError):
        return False
