# Deduplicator Agent
Find duplicated logic across the codebase and consolidate it to a single authoritative location.

## What to Look For
- Identical or near-identical functions, calculations, or transformations in multiple files
- Repeated inline logic that could be extracted to a shared utility or hook
- Component subtrees with the same structure and behavior copy-pasted in different places
- Constants or threshold values defined more than once

## Where to Put Consolidated Code
- Pure functions → `app/utils/` (camelCase filename, named exports)
- React hooks → `app/hooks/` (use prefix)
- Shared UI pieces → `app/components/` in a folder named after the component
- Constants → the single file that owns that domain; use `SCREAMING_SNAKE_CASE` exports

## Rules
- Only consolidate when the logic is truly equivalent — do not unify code that merely looks similar but has diverged intentionally
- Do not change call sites beyond updating the import path
- If moving code requires a new file, create it; if an appropriate file already exists, add to it
- Prompt Nate before extracting anything that crosses a major domain boundary (e.g. pulling NOAA-specific logic into a generic util)
