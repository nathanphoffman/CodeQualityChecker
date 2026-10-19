1. Power of 6s. People understand things best in groups of about 6.
   - Everything should have 6 or fewer: functions per file, items per folder, services per system, arguments to functions, attributes on components etc.
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
4. One job per function. Functions should avoid mutating or processing anything outside their core concern.
5. Be secure. Follow security best practices. Never put secrets like keys or passwords in code; keep them in configuration or environment variables.
6. Don't repeat yourself. Shared logic lives in one place.
7. No magic numbers. Name constants instead of hardcoding values.
8. Minimize dependencies. Don't add a library for something a few lines can do.
9. Add comments. Modest commentary is better than none or tons but why is better than what. Except clever code from rule 3, where comments should explain how it works.
10. Test what matters. Verify every change. Write simple unit and integration tests for critical logic only; skip trivial code.
11. Fail loudly but directedly. Never hide errors, don't over report or over-throw.
12. Clean up. In code you touch, remove dead code, unused imports, and leftover variables.
13. The total project line count as n^n should be roughly 6 or below (rule of 6 scaling).

Short version: Power of 6s. Clear names. Simple first. One job. Be secure. No repetition. Test what matters. Fail loud. Leave it cleaner.