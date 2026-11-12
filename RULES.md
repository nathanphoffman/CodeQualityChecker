1. Power of 6s. People understand things best in groups of about 6.
   - Everything should have 6 or fewer: functions per file, items per folder, services per system, arguments to functions, attributes on components etc.
   - Function and macro call depth should strive to be 6 or less
   - Exception: functions should aim for 6 lines or fewer, but may run up to 36 when splitting them is exceedingly difficult for performance or structural reasons.
2. Clear names. Names should explain themselves; longer and clearer beats short and vague ones. No acronyms unless an intern would know them, like ID. Follow the language's naming conventions; otherwise use:
   - SCREAMING_SNAKE for constants, like MAX_RETRY_COUNT
   - Pascal_Snake for structures such as classes, interfaces, and files that define them, such as components and types, like User_Account
   - lower_snake for everything else, including variables, functions, folders, and filenames that define them, like fetch_user_profile
3. Simple beats clever. Compare lengths:
   - Simple is less than 3x as long: use simple.
   - Simple is 3x to 6x as long: use your judgment.
   - Simple is over 6x as long: use clever.
   Regex always counts as clever. Always add a comment explaining how clever code works.
4. Be secure. Follow security best practices. Never put secrets like keys or passwords in code; keep them in configuration or environment variables.
   - Key and .env files are listed in .gitignore.
   - Avoid risky calls such as running strings as code or shell commands, SQL built from strings, broken hashes, or weak random numbers for secrets.
5. Don't repeat yourself. Shared logic lives in one place.
   - No copied runs of statements, and no functions that are copies of each other.
6. No magic numbers. Name constants instead of hardcoding values.
   - Strings repeated again and again, and numbers shared across files, become named constants too.
7. Minimize dependencies. Don't add a library for something a few lines can do.
8. One job per function. Functions should avoid mutating or processing anything outside their core concern.
   - Nest blocks (if, loops, try, switch) at most 3 levels deep.
   - Avoid true/false flag parameters; write one function per behavior.
   - Functions have at most 6 paths through them, statements in a function work on the same variables, and function names don't say "and", "or" or "then".
9. Add comments. Modest commentary is better than none or tons but why is better than what. Except clever code from rule 3, where comments should explain how it works.
   - The amount of comments fits the code size, and complicated functions have a comment or docstring.
10. Test what matters. Verify every change. Write simple unit and integration tests for critical logic only; skip trivial code.
11. Fail loudly but directedly. Never hide errors, don't over report or over-throw.
   - The amount of error checking fits the code size.
12. Clean up. In code you touch, remove dead code, unused imports, and leftover variables, and exports nothing imports.
   - Also remove commented-out code, unreachable code, and unused private functions.
13. Keep the project small. Judge size in powers of 6, a project of 6^x lines.
   - Up to 6^4 (1,296 lines) is full marks.
   - 6^6 (46,656 lines) is the most to aim for; past that, split it into separate projects.
14. Space it out. Blank lines separate ideas like paragraphs.
   - Max 6 lines in a row without a blank line.
   - A blank line before control statements, returns, line comments, and function/macro definitions, unless first in a block.
   - A blank line after function/macro definitions, closing brackets or multi-line statements, unless followed by another closing bracket, else, catch, or finally.
   - Never have two blank lines in a row (Python is exempt, as PEP 8 wants two between top-level definitions).
15. Project basics. Every project has a README, a .gitignore and tests.
16. Language/Framework best practices. Follow the habits the language's community expects, and the safety and performance basics of any framework the project uses. Framework checks only run when the framework is a dependency.
   - Set up the expected formatter and linter (ruff for Python, golangci-lint for Go, clippy and rustfmt for Rust, eslint or biome for TypeScript, clang-format for C, .editorconfig for C#, fprettify or fortitude for Fortran).
   - TypeScript: strict mode on in tsconfig, and few explicit `any` types.
   - Rust: commit Cargo.lock for binaries, and few `unwrap()` and `expect()` calls.
   - Python frameworks: django, flask, fastapi, sqlalchemy, pydantic.
   - TypeScript frameworks: react, next, express, nest, vue, angular, svelte, nuxt, fastify.
   - Rust frameworks: axum, actix, rocket, tauri, diesel, sqlx, bevy.
   - Go frameworks: gin, echo, fiber, net/http, gorm.
   - C# frameworks: ASP.NET Core, Entity Framework Core, Blazor, Unity.

Short version: Power of 6s. Clear names. Simple first. One job. Be secure. No repetition. Test what matters. Fail loud. Leave it cleaner.