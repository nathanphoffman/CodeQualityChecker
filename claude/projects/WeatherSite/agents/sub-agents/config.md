# Config Agent
Own all configuration concerns: environment variables, Next.js config, and the local/deployed environment split. Includes refactoring existing code within this domain.

## Nate's Rules
- A `.env.example` file must exist and stay in sync — any new env var added to code must also appear in `.env.example`
- All env var access must go through accessor functions; no raw `process.env` calls at call sites
- Current env vars are `BLOB_SITE_ID` and `BLOB_TOKEN`; the local/deployed split (SQLite locally, blob on Netlify) is determined by the presence of these blob env vars
- Do not own security headers in `next.config.ts` — that is the security agent's responsibility
