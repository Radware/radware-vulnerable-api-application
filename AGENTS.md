# AGENTS.MD - Guiding Codex WebUI for RVA E-Commerce Project

## 1. Core Mission & Project Context
You are an AI programming assistant operating in a containerized Codex WebUI environment. Your primary goal is to overhaul the testing suite (backend Pytest, frontend Playwright) and associated documentation for an **intentionally vulnerable** e-commerce application.

**Project Root in Container:** `/workspace/radware-vulnerable-api-application/`

**CRITICAL DIRECTIVE: PRESERVE INTENTIONAL VULNERABILITIES.**
-   Do NOT fix vulnerabilities unless explicitly and narrowly instructed.
-   Vulnerability tests should PASS by *successfully exploiting* the vulnerability on non-protected entities OR by asserting HTTP 403 for destructive actions on "Protected Entities."

**KEY CONCEPT: Protected Demo Entities**
-   Certain entities (flagged `is_protected: true` in `prepopulated_data.json` and detailed in `PROTECTED_ENTITIES.MD`) have specific defense rules:
    -   **Protected Users (`user.is_protected: true`):**
        -   CANNOT be deleted.
        -   Their `username` CANNOT be changed.
        -   Their `email` CAN be changed.
        -   They MUST retain at least one address and one credit card. Attempts to delete the last one of either will result in HTTP 403 with a specific message.
    -   **Addresses and Credit Cards belonging to a Protected User:**
        -   Can generally be modified (e.g., street name, cardholder name, expiry dates).
        -   Can be deleted, *unless* it's the user's last address or last credit card respectively.
        -   Can be set as default, and this will correctly un-default any previous default item for that user.
    -   **Protected Products (`product.is_protected: true`):**
        -   CANNOT be deleted.
        -   Core fields like `name`, `price`, `category` CANNOT be modified. `internal_status` can be modified via parameter pollution for demo purposes. Stock can be updated (with minimums for direct updates).
-   Attempts to perform forbidden actions (e.g., deleting a protected user, changing their username, deleting their last address/card, deleting/critically modifying a protected product) MUST result in HTTP 403 Forbidden. The error message should ideally be specific to the rule violated (e.g., "...cannot delete last address...", "...username cannot be changed...", "...product is protected...").
-   Non-destructive exploits (BOLA viewing, allowed parameter pollutions) SHOULD still work on protected entities or their sub-entities where applicable.
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
    *   **Sequence for Playwright Tasks (Robust Version):**
        1.  `echo "--- Preparing for Playwright Tests ---"`
        2.  `cd /workspace/radware-vulnerable-api-application/`
        3.  Define variables: `BACKEND_PORT=8000`, `FRONTEND_PORT=5001`, `BACKEND_LOG="/tmp/backend_uvicorn_TASKNAME.log"`, `FRONTEND_LOG="/tmp/frontend_flask_TASKNAME.log"` (use a unique TASKNAME in logs for clarity if running multiple E2E tasks).
        4.  `echo "Clearing previous server logs..."`
        5.  `rm -f $BACKEND_LOG $FRONTEND_LOG`
        6.  `echo "Attempting to stop any existing server on port $BACKEND_PORT..."`
        7.  `lsof -ti tcp:$BACKEND_PORT | xargs -r kill -9 || ss -tulnp | grep ":$BACKEND_PORT" | awk '{print $7}' | sed 's/.*pid=\([0-9]*\).*/\1/' | xargs -r kill -9 || echo "No process found on port $BACKEND_PORT or tools unavailable."`
        8.  `sleep 1`
        9.  `echo "Attempting to stop any existing server on port $FRONTEND_PORT..."`
        10. `lsof -ti tcp:$FRONTEND_PORT | xargs -r kill -9 || ss -tulnp | grep ":$FRONTEND_PORT" | awk '{print $7}' | sed 's/.*pid=\([0-9]*\).*/\1/' | xargs -r kill -9 || echo "No process found on port $FRONTEND_PORT or tools unavailable."`
        11. `sleep 1`
        12. `echo "Starting backend API on port $BACKEND_PORT in background..."`
        13. `python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --log-config app/log_conf.json > $BACKEND_LOG 2>&1 & APP_PID=$!`
        14. `echo "Backend potentially started with PID: $APP_PID. Log: $BACKEND_LOG"`
        15. `sleep 3`
        16. `echo "Starting frontend server on port $FRONTEND_PORT in background..."`
        17. `python frontend/main.py > $FRONTEND_LOG 2>&1 & FRONTEND_PID=$!`
        18. `echo "Frontend potentially started with PID: $FRONTEND_PID. Log: $FRONTEND_LOG"`
        19. `sleep 8`
        20. `echo "Checking if backend is responsive..."`
        21. `if curl -s --head "http://localhost:$BACKEND_PORT/docs" | grep "200 OK" > /dev/null; then echo "Backend is UP."; else echo "ERROR: Backend FAILED. Check $BACKEND_LOG."; kill $APP_PID || true; kill $FRONTEND_PID || true; exit 1; fi`
        22. `echo "Checking if frontend is responsive..."`
        23. `if curl -s --head "http://localhost:$FRONTEND_PORT/" | grep "200 OK" > /dev/null; then echo "Frontend is UP."; else echo "ERROR: Frontend FAILED. Check $FRONTEND_LOG."; kill $APP_PID || true; kill $FRONTEND_PID || true; exit 1; fi`
        24. `echo "Running Playwright tests: <SPECIFIC_PLAYWRIGHT_COMMAND_USER_WILL_PROVIDE>..."`
        25. `TEST_EXIT_CODE=0`
        26. `<SPECIFIC_PLAYWRIGHT_COMMAND_USER_WILL_PROVIDE> || TEST_EXIT_CODE=$?`
        27. `echo "Playwright test execution finished with exit code: $TEST_EXIT_CODE"`
        28. `echo "--- Cleaning up servers ---"`
        29. `if [ ! -z "$APP_PID" ]; then echo "Killing backend (PID $APP_PID)..."; kill $APP_PID || echo "Backend already stopped."; sleep 0.5; kill -9 $APP_PID 2>/dev/null || true; fi`
        30. `if [ ! -z "$FRONTEND_PID" ]; then echo "Killing frontend (PID $FRONTEND_PID)..."; kill $FRONTEND_PID || echo "Frontend already stopped."; sleep 0.5; kill -9 $FRONTEND_PID 2>/dev/null || true; fi`
        31. `wait $APP_PID $FRONTEND_PID 2>/dev/null || true`
        32. `echo "Server cleanup attempted."`
        33. `if [ $TEST_EXIT_CODE -ne 0 ]; then echo "Playwright tests FAILED. Dumping server logs:"; echo "--- Backend Log ($BACKEND_LOG) ---"; cat $BACKEND_LOG; echo "--- Frontend Log ($FRONTEND_LOG) ---"; cat $FRONTEND_LOG; echo "--- End of Logs ---"; else echo "Playwright tests passed or completed."; fi`
    *   **Command to Run All E2E Tests:** (Follow the sequence above, using `npx playwright test frontend/e2e-tests/` at step 26, replacing the placeholder).
    *   **Command for Specific E2E File:** (Follow sequence, using `npx playwright test frontend/e2e-tests/your_file.spec.ts` at step 26, replacing the placeholder).

**3.3. General:**
-   After any code modifications (app or test), run the narrowest possible set of tests to verify your change before running broader suites.
-   If a functional test fails due to a bug in the application code (that is NOT an intentional vulnerability), you should fix that application bug.
-   If a vulnerability test fails to exploit a vulnerability on a NON-PROTECTED entity, the application code or the test's exploit logic needs fixing.
-   If a test fails because it's incorrectly trying to perform a destructive action on a PROTECTED entity and not asserting the 403, fix the test's assertion based on the defined protected entity rules.

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