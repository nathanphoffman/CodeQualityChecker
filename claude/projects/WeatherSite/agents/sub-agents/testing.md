# Testing Agent
Set up and maintain the data-layer test suite using Vitest. Includes runner configuration and writing/updating test files for validators and NOAA API response structure.

## Nate's Rules
- Use Vitest as the test runner; configure it to work with the existing Next.js/TypeScript setup
- One test file per validator function; one additional test file for overall NOAA API response structure
- No network calls — test only pure logic; mock or skip anything that touches the network
