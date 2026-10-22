# TODO

## Add Rexx support

Not done yet. The problem:

- The only Rexx tree-sitter grammar found is `stcarmi/tree-sitter-rexx`. Its own header says it is for syntax highlighting, not full parsing, so it gives a flat list of words (keywords, labels, strings) with no functions or blocks.
- That repo has no LICENSE file, only `"license": "ISC"` in `package.json`, so it should not be copied into `vendor/` until that is cleared up (ask the author, or check for a license in a newer version).
- The other Rexx grammar found (`dhineshaps/rexx-tree-sitter`) is a 58-line toy.

Options to look at later:

1. Write a small Rexx reader by hand, like the Deor one: a label such as `greet:` is a function, and `do`/`end`, `select`/`end` blocks are matched by us. Checks would be shallower than for the other languages.
2. Find or write a real Rexx grammar and vendor it the way Hare and Mojo are (see `vendor/`).

Files Rexx would use: `.rexx`, `.rex`, `.exec`.
