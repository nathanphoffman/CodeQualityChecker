from .limits import (CODE_KEYWORDS, COMMENTED_CODE_PENALTY, KEYWORD_PENALTY, MIN_TODO_WORDS, NOISE_PENALTY,
                     OPENER_PENALTY, OVERLAP_WEIGHT, PUNCTUATION_ONLY, SYMBOL_PENALTY, TODO_MARKERS, TOLERANCE,
                     VAGUE_TODO_PENALTY, WHAT_VERBS, WHY_DISCOUNT)
from .signals import has_code_symbols, is_commented_out_code, mentions_reason, overlap_ratio, words_of


def noise_penalty(text):
    """Empty and punctuation-only comments, and TODOs that say nothing more."""
    if not text.strip(PUNCTUATION_ONLY):
        return NOISE_PENALTY
    words = words_of(text)
    return VAGUE_TODO_PENALTY if words[0] in TODO_MARKERS and len(words) < MIN_TODO_WORDS else 0.0


def wording_penalty(text):
    """Signs of describing code: code symbols, code keywords, and opening with a what-verb."""
    words = words_of(text)
    penalty = SYMBOL_PENALTY if has_code_symbols(text) else 0.0
    penalty += KEYWORD_PENALTY if CODE_KEYWORDS & set(words) else 0.0
    return penalty + (OPENER_PENALTY if words and words[0] in WHAT_VERBS else 0.0)


def raw_penalty(comment):
    if is_commented_out_code(comment.text, comment.language):
        return COMMENTED_CODE_PENALTY
    overlap = overlap_ratio(comment.text, comment.code_text) * OVERLAP_WEIGHT
    return min(1.0, overlap + wording_penalty(comment.text) + noise_penalty(comment.text))


def why_confidence(comment):
    """0.0 to 1.0: how likely the comment explains why, as opposed to repeating what the code does."""
    if comment.explains_clever:
        return 1.0
    penalty = raw_penalty(comment)
    if penalty < 1.0 and mentions_reason(comment.text):
        penalty *= WHY_DISCOUNT
    return 1 - max(0.0, penalty - TOLERANCE) / (1 - TOLERANCE)
