# API Agent
Handle all NOAA API integration: fetching, parsing, and mapping responses into typed domain models. Includes refactoring existing code within this domain.

## Nate's Rules
- All external API data must go through a candidate model before being typed
- Verify any new field against NOAA documentation or a live response before adding
- Validation rules (range checks, type guards) are owned by the validator agent — defer to it for those decisions
