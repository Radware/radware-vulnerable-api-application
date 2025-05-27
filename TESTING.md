# Testing Guide

For complete instructions on running backend tests (Pytest) and frontend end-to-end tests (Playwright), see [README_TESTING.md](README_TESTING.md).

Common commands from the project root:

```sh
# Run all backend tests
pytest tests/

# Run E2E tests (backend + frontend servers will be started)
npx playwright test frontend/e2e-tests/
```
