# TODO

## Rexx: swap the hand-written reader for a real grammar

Rexx is supported, but through our own small reader (`codequality/language_parsers/rexx/`), because the only tree-sitter grammar found
(`stcarmi/tree-sitter-rexx`) is for syntax highlighting and has no license file. The reader builds a tree shaped like tree-sitter's, so
every rule works on it, with these limits:

- A command is any line that is not an instruction, so a typo in a keyword reads as a host command instead of an error.
- `import`-style checks do nothing, because plain Rexx has no imports (ooRexx's `::requires` is not read).
- A routine is a label plus everything up to the next label. Labels used only for `signal` jumps count as routines too.
- Objects and classes from ooRexx (`::class`, `::method`) are not understood.

If a proper grammar turns up with a clear license, vendor it like Hare and Mojo (see `vendor/`) and delete the reader.
