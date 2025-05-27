# AGENTS.MD - Guiding Codex WebUI for RVA E-Commerce Project

## 1. Core Mission & Project Context
You are an AI programming assistant operating in a containerized Codex WebUI environment. Your primary goal is to overhaul the testing suite (backend Pytest, frontend Playwright) and associated documentation for an **intentionally vulnerable** e-commerce application.

**Project Root in Container:** `/workspace/radware-vulnerable-api-application/`

**CRITICAL DIRECTIVE: PRESERVE INTENTIONAL VULNERABILITIES.**
-   Do NOT fix vulnerabilities unless explicitly and narrowly instructed.
-   Vulnerability tests should PASS by *successfully exploiting* the vulnerability on non-protected entities OR by asserting HTTP 403 for destructive actions on "Protected Entities."

**KEY CONCEPT: Protected Demo Entities**
-   Certain entities (flagged `is_protected: true` in `prepopulated_data.json` and detailed in `PROTECTED_ENTITIES.MD`) have specific defense rules:
    -   CANNOT be deleted.
    -   Critical fields CANNOT be modified.
    -   Attempts MUST result in HTTP 403 Forbidden with a message like "...is protected for demo purposes...".
    -   Non-destructive exploits (BOLA viewing, allowed parameter pollutions) SHOULD still work.
-   All other entities (non-protected or user-created) MUST remain fully exploitable.

## 2. How I Will Interact With You & Your Workflow
1.  **Tasks:** I will provide tasks in "Code Mode."
2.  **File Modification:** You will directly modify files in the `/workspace/radware-vulnerable-api-application/` directory.
3.  **Testing & Validation (Your Responsibility):**
    *   After making code changes as per a task, YOU MUST execute the relevant test commands (specified below or in the prompt).
    *   Analyze `stdout`/`stderr` from test runs.
    *   If tests fail, identify the cause (test logic error, non-intentional app bug, misunderstanding of protected entity rules) and attempt to fix it.
    *   Re-run tests until they pass according to the task's criteria.
    *   Report test outcomes (pass/fail summaries, relevant logs for failures).
4.  **Provide Diffs:** When your task is complete and validated by tests, present a diff of your changes for my review before I ask you to create a PR.

## 3. Standard Testing Instructions (How to Validate Changes)

**ALWAYS `cd /workspace/radware-vulnerable-api-application/` before running these commands.**

**3.1. Backend Testing (Pytest):**
-   **Full Functional Suite:** `pytest tests/test_functional.py -v`
-   **Full Vulnerability Suite:** `pytest tests/test_vulnerabilities.py -v`
-   **Specific Functional File/Test:** `pytest tests/test_functional.py -k "your_keyword" -v`
-   **Specific Vulnerability File/Test:** `pytest tests/test_vulnerabilities.py -k "your_keyword" -v`

**3.2. Frontend E2E Testing (Playwright):**
    **IMPORTANT:** For any task requiring Playwright tests, you must ensure the backend and frontend servers are running *within the current task's container environment*.
    *   **Sequence for Playwright Tasks:**
        1.  `echo "Ensuring ports are free..."`
        2.  `lsof -ti:8000 | xargs -r kill -9 2>/dev/null`
        3.  `lsof -ti:5001 | xargs -r kill -9 2>/dev/null`
        4.  `echo "Starting backend API..."`
        5.  `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-config app/log_conf.json > /tmp/backend_uvicorn.log 2>&1 & APP_PID=$!`
        6.  `for i in {1..15}; do curl -s http://localhost:8000/docs >/dev/null && break; sleep 2; done`
        7.  `echo "Starting frontend server..."`
        8.  `python frontend/main.py > /tmp/frontend_flask.log 2>&1 & FRONTEND_PID=$!`
        9.  `for i in {1..15}; do curl -s http://localhost:5001 >/dev/null && break; sleep 2; done`
        10. `echo "Running Playwright tests..."`
        11. `npx playwright test frontend/e2e-tests/<specific_spec_file.spec.ts_or_leave_blank_for_all>`
            *   (e.g., `npx playwright test frontend/e2e-tests/auth.spec.ts`)
        12. `TEST_EXIT=$?`
        13. `echo "Playwright tests finished. Killing servers..."`
        14. `kill $APP_PID $FRONTEND_PID || true`
        15. `wait $APP_PID $FRONTEND_PID 2>/dev/null`
        16. `echo "Servers shut down."`
        17. `if [ $TEST_EXIT -ne 0 ]; then echo "Dumping backend log:" && cat /tmp/backend_uvicorn.log; echo "Dumping frontend log:" && cat /tmp/frontend_flask.log; fi`
    *   **Command to Run All E2E Tests:** (Follow the sequence above, using `npx playwright test frontend/e2e-tests/` at step 10).
    *   **Command for Specific E2E File:** (Follow sequence, using `npx playwright test frontend/e2e-tests/your_file.spec.ts` at step 10).

**3.3. General:**
-   After any code modifications (app or test), run the narrowest possible set of tests to verify your change before running broader suites.
-   If a functional test fails due to a bug in the application code (that is NOT an intentional vulnerability), you should fix that application bug.
-   If a vulnerability test fails to exploit a vulnerability on a NON-PROTECTED entity, the application code or the test's exploit logic needs fixing.
-   If a test fails because it's incorrectly trying to perform a destructive action on a PROTECTED entity and not asserting the 403, fix the test's assertion.

## 4. Code Contribution & Style
-   **Python:** Black formatting (88 char limit), snake_case, type hints, clear docstrings.
-   **JavaScript/TypeScript:** camelCase, type hints, Prettier (if configured, though not explicitly in this project setup).
-   **Clarity:** Prioritize readable and maintainable code and tests.

## 5. Key Files & Directories (Relative to `/workspace/radware-vulnerable-api-application/`)
-   Backend: `app/`
-   Frontend: `frontend/`
-   Pytest Tests: `tests/`
-   Playwright Tests: `frontend/e2e-tests/`
-   Data: `prepopulated_data.json`
-   Docs: `README.md`, `PROTECTED_ENTITIES.MD`, `openapi.yaml`

