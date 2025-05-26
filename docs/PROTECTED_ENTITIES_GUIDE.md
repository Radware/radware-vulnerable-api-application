# Protected Entities and Testing Guide

This guide summarizes how the `is_protected` flag works and how to run the test suites for the Radware Vulnerable API project.

## Why Protected Entities Exist

The repository contains certain users, products and profile data that are marked as **protected**. These records are defined in `prepopulated_data.json` and documented in [PROTECTED_ENTITIES.md](../PROTECTED_ENTITIES.md).

Key goals of the protected entity system include:

1. **Flow Stability** – automated demos rely on these records to always exist.
2. **Predictable Demos** – common walkthroughs reference the same data.
3. **WAAP Learning** – security tools can learn normal behavior from stable data.
4. **User Guidance** – attempts to delete or heavily modify protected items return an HTTP 403 with a message directing testers toward non‑protected records.

All newly created entities are *not* protected and may be freely modified or deleted to demonstrate vulnerabilities.

## Writing and Running Tests

The project uses **pytest** for backend tests and **Playwright** for frontend end‑to‑end tests. These commands are also listed in `AGENTS.md`.

### Environment Setup

```sh
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r requirements.txt pytest httpx pytest-asyncio
```

### Running Backend Tests

Run functional tests:
```sh
pytest tests/test_functional.py --maxfail=1 --disable-warnings -q
```

Run vulnerability tests:
```sh
pytest tests/test_vulnerabilities.py --maxfail=1 --disable-warnings -q
```

### Running Frontend Tests

```sh
npx playwright test frontend/e2e-tests/ --timeout=60000
```

Alternatively, execute `./verify.sh` to set up the environment, start the API server, run both pytest suites, and generate brief traffic before shutting the server down.

## Expected Test Behavior for Protected Entities

When tests attempt destructive actions (such as deleting a user or product) against a protected record, the API should respond with **403 Forbidden** and an explanatory message. Operations against non‑protected entities should still succeed, demonstrating the vulnerabilities.

Stock quantity changes for protected products are allowed but a log entry is generated noting the update. This keeps demo flows stable while highlighting that a protected item was modified.

Refer to [PROTECTED_ENTITIES.md](../PROTECTED_ENTITIES.md) for the complete list of protected records and tips on choosing non‑protected items for your tests.
