from dataclasses import dataclass


@dataclass(frozen=True)
class Comment_Found:
    first_line: int
    last_line: int
    text: str  # without the comment markers; a run of // or # lines is one comment
    code_text: str  # the code the comment is about: the line it trails, or the next line of code

    explains_clever: bool  # sits on or above clever code, where rule 3 asks for a how
    language: str
