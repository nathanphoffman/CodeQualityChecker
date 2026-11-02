# Deor

The transpiler enforces these. Edit `.deor` files, never the generated `.rs` beside them. The full list is in the Deor spec, `docs/enforced_practices.md`.

- Names are at least 3 characters everywhere: variables, parameters, fields, functions, types.
- Enums, structs and types are PascalCase, shapes are camelCase, variables and functions are snake_case, consts are SCREAMING_SNAKE_CASE.
- Top-level order in a file: imports, then `enum`/`struct`/`type`/`shape`, then macros, then functions. Nothing structural goes after a macro or function.
- A function takes at most 3 parameters. No nested functions, no lambdas, no methods on structs.
- A call with 2 or 3 arguments needs every argument to be a variable that already exists. No literals or expressions. A call with 1 argument may use a literal. This includes `range(start, stop)`.
- Building or returning a struct uses `(field_a, field_b)`: each must be a variable named exactly like the struct's field. Order doesn't matter. No literals.
- A function that returns several values declares a named struct for them. There are no tuples.
- A `type` validator must have a predicate body, and wraps a primitive or a struct.
- `const` can't be reassigned. `as` never takes an explicit type: use `int val = 5` or `val as 5`, not both.
- List shapes start as `empty`.
