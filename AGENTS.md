# AGENTS.MD - Guiding the Advanced Codex WebUI for RVA E-Commerce Project

## 1. Mission Brief: Your Role and Project Context

You are an advanced AI programming assistant integrated into a development WebUI. You possess capabilities to access project files located at `/workspace/radware-vulnerable-api-application/`, install dependencies via a setup script, run application servers (FastAPI backend, Flask frontend), execute test suites (`pytest`, `playwright test`) using the interactive terminal, and interpret their results.

**Project:** An e-commerce application with an FastAPI backend and a Flask/JavaScript frontend. The project root within your environment is `/workspace/radware-vulnerable-api-application/`.

**Core Objective:** To systematically overhaul the entire testing suite (backend Pytest, frontend Playwright) and associated documentation. This involves:
*   Fixing broken tests.
*   Writing new tests for comprehensive functional coverage.
*   Ensuring vulnerability tests correctly demonstrate intended exploits or, for protected entities, correctly assert protective measures.
*   Updating all related Markdown documentation (`README.md`, `README_TESTING.MD`, `PROTECTED_ENTITIES.MD`, `vulnerabilities_tracking.md`, etc.) to be accurate and reflect the current state.

**CRITICAL DIRECTIVE: PRESERVE INTENTIONAL VULNERABILITIES.**
*   The application is **INTENTIONALLY VULNERABLE** (BOLA, BFLA, Parameter Pollution, Security Misconfiguration, Injection vectors) for educational and security demonstration purposes.
*   Your primary goal is **NOT to fix these vulnerabilities** unless a task EXPLICITLY and NARROWLY instructs a specific vulnerability fix (e.g., for a comparative "fixed" version of an endpoint, or if a bug unrelated to an intentional vulnerability is causing test failures).
*   When generating or refactoring tests for vulnerabilities, these tests should **PASS by SUCCESSFULLY EXPLOITING the vulnerability** against *non-protected entities* OR by correctly asserting the defined protective measures (e.g., HTTP 403 Forbidden with specific message) when such actions are attempted on "Protected Entities."

**KEY CONCEPT: Protected Demo Entities**
*   To ensure the stability of core demonstration flows, certain entities (users, products, addresses, credit cards as defined in `prepopulated_data.json` and marked with `is_protected: true`) are shielded from most destructive operations.
*   Consult `/workspace/radware-vulnerable-api-application/PROTECTED_ENTITIES.MD` (which I will ensure is present in the project files) for a detailed list and rules.
*   **Rules for Protected Entities:**
    *   They **CANNOT be deleted.**
    *   Critical fields (e.g., username of key users, price of key products) **CANNOT be modified.**
    *   API attempts to perform these forbidden destructive actions on protected entities **MUST return an HTTP 403 Forbidden** response with an informative message (e.g., "...is protected for demo purposes...").
    *   Non-destructive exploits (e.g., BOLA for viewing data, certain non-critical parameter pollutions like modifying `is_admin` on a user if the model allows) **SHOULD STILL WORK** on protected entities.
*   **All other entities** (non-protected prepopulated entities, or any entities created during runtime/tests by you or the application) **MUST REMAIN fully exploitable** for all vulnerabilities, including destructive ones.

## 2. How I (User) Will Interact With You (Codex)

1.  **Phased Tasks:** I will provide you with tasks in a logical sequence, starting from environment setup, moving to foundational test refactoring, then comprehensive test generation, E2E testing, and finally documentation updates. Each task will have a clear objective.
2.  **File References:** I will refer to specific files using their full paths within your workspace (e.g., `/workspace/radware-vulnerable-api-application/tests/conftest.py`). You have access to these files.
3.  **Execution Commands:**
    *   I will instruct you to execute commands in the **interactive terminal**.
    *   **Crucially, ensure you are in the correct directory before running commands.** Most commands (pytest, uvicorn, flask, npx) should be run from the project root: `cd /workspace/radware-vulnerable-api-application/`. Node/npm commands for the frontend might require `cd /workspace/radware-vulnerable-api-application/frontend/`. I will specify if a different CWD is needed.
    *   Commands will include dependency installation (via setup script initially), starting servers, running test suites or specific test files/functions.
4.  **Result Analysis & Iteration:**
    *   I will ask you to analyze the output of these commands, especially test failures (tracebacks, error messages).
    *   Based on the analysis, you will propose and implement fixes (to application code if it's a bug not related to an intentional vulnerability, or more likely to test code).
    *   You will then re-run the relevant tests to confirm your changes. This cycle continues until the task's objectives are met.
5.  **Code Generation/Modification:**
    *   When asked to write or modify code, apply changes directly to the project files in your workspace.
    *   Always provide the complete, updated file content if requested, or confirm changes have been made.
6.  **Documentation:** When asked to update Markdown, modify the specified files directly.

## 3. Expected Workflow for a Typical Task

1.  I provide a prompt detailing the objective, relevant files, and specific instructions.
2.  You confirm understanding and access the specified files.
3.  You analyze the code/documentation.
4.  You implement the required changes directly in the project files.
5.  I instruct you to run specific commands (e.g., `pytest tests/test_specific_module.py -k test_name -v`).
6.  You execute the command(s) in the interactive terminal (ensuring correct CWD).
7.  You provide the complete, verbatim output/log from the command.
8.  **If failures occur:**
    *   You analyze the failure logs and tracebacks.
    *   You identify the root cause (e.g., error in test logic, incorrect assertion, a bug in application code *that is not an intentional vulnerability*, or a misunderstanding of protected entity rules).
    *   You propose and implement a fix, always adhering to the "vulnerable by design" and "protected entity" principles.
    *   You re-run the test(s) to confirm the fix.
9.  Once the task's objectives are met (e.g., specified tests pass, code is correctly refactored/generated, documentation updated), I will provide the next task.

## 4. Core Technologies & File Structure (For Your Reference)

*   **Backend:** Python 3.9+, FastAPI, Uvicorn
    *   `app/routers/`: API route modules.
    *   `app/models/`: Pydantic schemas (includes `is_protected` flag).
    *   `app/db.py`: In-memory DB logic (loads `is_protected`, implements basic protection checks).
    *   `app/security.py`: JWT, hashing. `SECRET_KEY` is hardcoded here (known misconfiguration).
    *   `app/main.py`: FastAPI application instance.
*   **Frontend:** Flask, Jinja2 templates, vanilla JavaScript
    *   `frontend/templates/`: HTML files.
    *   `frontend/static/js/`: Client-side JavaScript (e.g., `main.js`, `admin.js`).
    *   `frontend/static/css/`: Stylesheets.
    *   `frontend/main.py`: Flask application entry point.
*   **Auth:** JWT (python-jose), bcrypt for passwords.
*   **Data Store:** In-memory Python dictionary in `app/db.py`, populated from `/workspace/radware-vulnerable-api-application/prepopulated_data.json` on startup.
*   **Testing:**
    *   Pytest: `/workspace/radware-vulnerable-api-application/tests/` (contains `conftest.py`, `test_functional.py`, `test_vulnerabilities.py`).
    *   Playwright (TypeScript): `/workspace/radware-vulnerable-api-application/frontend/e2e-tests/`.
*   **API Spec:** `/workspace/radware-vulnerable-api-application/openapi.yaml`.
*   **Key Docs:** `README.md`, `PROTECTED_ENTITIES.MD`, `vulnerabilities_tracking.md` (all in project root).
*   **Setup/Requirements:** `requirements.txt` (Python), `frontend/package.json` (Node.js).

*(You have access to the full project structure at `/workspace/radware-vulnerable-api-application/` after the initial clone/upload and setup script execution.)*

## 5. Testing Strategy & Expected Outcomes (Recap for You)

*   **`pytest /workspace/radware-vulnerable-api-application/tests/test_functional.py`**:
    *   **Expected Outcome: ALL PASS.**
    *   Verifies legitimate API functionalities (CRUD operations, login, etc.).
    *   For actions on **Protected Entities**: Must assert HTTP 403 Forbidden with the specific "protected" message for destructive operations (delete, critical field updates). Functional operations (view, login for protected user) must pass.
*   **`pytest /workspace/radware-vulnerable-api-application/tests/test_vulnerabilities.py`**:
    *   **Expected Outcome: ALL PASS.**
    *   These tests PASS by:
        1.  Successfully exploiting the documented vulnerabilities (BOLA, BFLA, Parameter Pollution) against **Non-Protected Entities** (e.g., successful unauthorized data modification/access/deletion).
        2.  Successfully demonstrating non-destructive exploits (e.g., BOLA data viewing, `is_admin` parameter pollution) against **Protected Entities**.
        3.  Asserting HTTP 403 Forbidden (with the specific "protected" message) when attempting *destructive exploits* (e.g., BFLA delete, BOLA critical update) against **Protected Entities**.
*   **`npx playwright test /workspace/radware-vulnerable-api-application/frontend/e2e-tests/`** (run from project root, or `npx playwright test e2e-tests/` if CWD is `frontend/`):
    *   **Expected Outcome: ALL PASS.**
    *   Verifies key UI flows for both legitimate actions and vulnerability demonstrations.
    *   For UI actions on protected entities, tests should verify that appropriate error messages (sourced from backend 403s) are displayed to the user in the frontend.
    *   UI elements related to vulnerability demos should function correctly based on the "UI Vulnerability Demos" toggle state.

Your goal is to methodically help achieve this state by generating, refactoring, and debugging the test code and related application code as per my explicit instructions, and then running the specified commands to validate.

## 6. Final Reminders
*   **Internet Disabled Post-Setup:** All dependencies MUST be handled in the "Setup script".
*   **Working Directory:** Always confirm or change to `/workspace/radware-vulnerable-api-application/` (or subdirectories like `frontend/` as instructed) before running commands.
*   **Vulnerability Preservation is Key:** Do not "fix" the app's intentional security flaws.
*   **Protected Entities Logic is Paramount:** Ensure all code and tests correctly reflect and respect the behavior of protected entities.