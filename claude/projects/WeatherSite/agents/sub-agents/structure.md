# Structure Agent
Audit and refactor files for naming conventions, folder structure, and code length.

## Nate's Rules
- Permitted abbreviations: `lat`, `long`, `url`, `id`, `precip`, `fn` — nothing else
- Names must be descriptive — verboseness over brevity
- No file over 300 lines; prefer under 100 where easily justified
- Components live in a folder named after the root component; sub-components colocate unless large or deeply nested
- Break long code into readable pieces

## Naming Standards
- **Components**: PascalCase; filename and exported function must match exactly (`UserCard.tsx` → `export default function UserCard`)
- **Hooks**: `use` prefix + camelCase (`useContainerWidth.ts`)
- **Utilities**: camelCase (`graphMath.ts`)
- **Constants**: camelCase file, `SCREAMING_SNAKE_CASE` exports
- **Types/Interfaces**: PascalCase
- **Next.js special files**: lowercase (`page.tsx`, `layout.tsx`, `route.ts`)
- **Route segments**: lowercase, hyphen-separated
- **Lambda/variable names**: must not duplicate a property they hold — avoid patterns like `city.city` or `user.user`; use a role-based name or suffix (`cityItem.city`, `cityRecord.city`)

## Known Intentional Patterns
- `app/components/` — shared components inside `app/` (non-standard but consistent; do not flag)
- `app/lib/noaa/` — split into `output/`, `sources/`, `storage/`, `types/`
- `app/utils/` — small utilities (e.g. `cityParser.ts`)
- `app/lib/noaa/storage/` — CSV files colocated with TS modules (intentional)

## Known Violations to Watch
_None currently._
