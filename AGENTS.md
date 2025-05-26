# AGENTS.MD - Vulnerable E-Commerce API (with Protected Entities)

## 1. Project Overview
This repository implements an **intentionally vulnerable** e-commerce API and frontend. Its primary purpose is to demonstrate OWASP API Top 10 issues, including Broken Object Level Authorization (BOLA), Broken Function Level Authorization (BFLA), Parameter Pollution, and Security Misconfiguration.

**CRITICAL: AI agents MUST preserve these intentional vulnerabilities unless a task EXPLICITLY and NARROWLY instructs a specific vulnerability fix.**

**NEW CONCEPT: Protected Demo Entities**
To ensure core demo stability, certain entities (users, products, etc., defined in `PROTECTED_ENTITIES.md` and flagged `is_protected: true` in `prepopulated_data.json`) have specific protection rules:
- They **cannot be deleted**.
- Critical fields (like username for flow users, price for flow products) **cannot be modified**.
- Attempts to perform these destructive actions on protected entities **MUST** result in an HTTP 403 Forbidden response with an informative message guiding the user.
- Non-destructive vulnerabilities (e.g., BOLA viewing, specific parameter pollutions) **SHOULD STILL WORK** on these protected entities.
- **All other entities** (non-protected prepopulated, or user-created) **MUST REMAIN fully exploitable** for all vulnerabilities, including destructive ones.

## 2. Core Technologies
- **Backend:** Python 3.9+, FastAPI, Uvicorn
- **Frontend:** Flask, Jinja2 templates, vanilla JavaScript
- **Auth:** JWT via python-jose, bcrypt password hashing
- **Data Store:** In-memory Python dict (populated from `prepopulated_data.json` on startup, includes `is_protected` flags)
- **Testing:**
    - `pytest tests/test_functional.py`: Tests core legitimate functionalities. **These tests MUST always pass.**
    - `pytest tests/test_vulnerabilities.py`: Tests the exploitability of intentional vulnerabilities. **These tests MUST always pass by successfully exploiting the vulnerabilities.**
    - `npx playwright test frontend/e2e-tests/`: Tests frontend user flows and UI indicators related to vulnerabilities. **These tests MUST always pass.**
- **Optional Deployment:** Docker, Nginx, Supervisor

## 3. Repository Structure
/
├── app/ # FastAPI backend
│   ├── routers/ # API route modules (auth, users, products, orders, profile)
│   ├── models/  # Pydantic schemas (now with `is_protected` flag)
│   ├── db.py    # In-memory DB logic (loads `is_protected` flag)
│   ├── security.py # JWT, hashing, secrets
│   ├── main.py     # FastAPI app & middleware
│   └── log_conf.json # JSON logging config
├── frontend/ # Flask frontend & E2E tests
│   ├── templates/ # Jinja2 HTML templates (will need UI hints for protected entities)
│   ├── static/    # CSS, JS, images (JS will handle 403 messages for protected entities)
│   ├── e2e-tests/ # Playwright scripts (will need updates for protected entity UI)
│   └── main.py    # Flask app entry point
├── tests/ # pytest backend tests
│   ├── test_functional.py
│   └── test_vulnerabilities.py
├── prepopulated_data.json # initial data for in-memory DB (now with `is_protected` flags)
├── PROTECTED_ENTITIES.md # NEW: Defines which entities are protected and why. **Consult this file.**
├── openapi.yaml # full API spec with vulnerability annotations
├── Dockerfile # build configuration
├── nginx.conf # reverse -proxy routes
├── supervisord.conf # process supervision
├── run_dev.sh # starts backend & frontend locally
├── verify.sh # automates setup & test suite
├── README.md # project overview & manual vulnerability testing
└── requirements.txt # Python dependencies

## 4. Coding Conventions
- **Formatting:** Black for Python; limit lines to 88 chars
- **Naming:** snake_case for Python, camelCase for JS
- **Typing:** use type hints on all functions and models
- **Docstrings:** triple-quoted, explain purpose and edge cases
- **Commit & PRs:**
  - Title: `[Scope] Short description` (e.g. `[Auth] Add login endpoint`)
  - Body: summary, related issue IDs, test plan. **Clearly state if changes affect protected entity behavior or vulnerability exploitability.**
  - Assign ≥1 reviewer, link failing tests if any

## 5. Setup & Run
1. **Local**
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   # For frontend (if testing UI changes):
   # npm install && npx playwright install
   ./run_dev.sh # Starts backend. For frontend, run `cd frontend && python main.py`
   ```

2. **Docker**
   ```bash
   docker build -t vuln-api .
   docker run -d -p 80:8000 --name vuln-api vuln-api # Port 80 for Nginx, 8000 for direct Uvicorn
   ```

## 6. Testing Strategy & Expected Outcomes
**IMPORTANT FOR AGENT:** Understand the PASS/FAIL criteria for each test suite.

### Backend Functional Tests (pytest tests/test_functional.py):
- **Command:** `pytest tests/test_functional.py --maxfail=1 --disable-warnings -q`
- **Expected Outcome:** ALL PASS. These tests verify that legitimate API operations work as expected, even with the protection logic (e.g., a protected user can still log in).

### Backend Vulnerability Tests (pytest tests/test_vulnerabilities.py):
- **Command:** `pytest tests/test_vulnerabilities.py --maxfail=1 --disable-warnings -q`
- **Expected Outcome:** ALL PASS. These tests PASS by successfully exploiting vulnerabilities.
  - If a test attempts a destructive action on a protected entity (e.g., delete AliceSmith), the test should assert that it receives an HTTP 403 Forbidden with the specific "This entity is protected..." message. This is a PASS for that part of the test.
  - If a test attempts a destructive action on a non-protected entity, it should succeed in performing the destructive action (e.g., deleting GraceWilson). This is a PASS.
  - If a test demonstrates BOLA viewing or non-destructive parameter pollution on a protected entity, it should succeed in exploiting the vulnerability. This is a PASS.

### Frontend E2E Tests (npx playwright test frontend/e2e-tests/):
- **Command:** `npx playwright test frontend/e2e-tests/ --timeout=60000`
- **Expected Outcome:** ALL PASS. These tests verify:
  - Legitimate user flows through the UI.
  - Correct display of "protected entity" indicators in the UI.
  - Correct display of warning messages when a UI action attempts a destructive operation on a protected entity and receives a 403 from the backend.
  - Successful demonstration of vulnerabilities on non-protected entities via the UI.

**Note to Agent:** If backend API responses change (e.g., new 403 messages), corresponding frontend JavaScript and E2E tests (*.spec.ts) will likely need updates to correctly handle and assert these new UI states.

### Verification Script (./verify.sh):
Runs all the above test suites. The script itself should complete successfully, with each test suite reporting its expected outcomes as defined above.

## 7. Task Execution Guidance
- **Consult PROTECTED_ENTITIES.md:** Before making changes to any entity or its handling, check if it's listed as protected.
- **Backend API Changes:**
  - If implementing protection logic, ensure 403 responses for protected entities include the specific informative message.
  - When adding new features or fixing non-vulnerability bugs, ensure new entities are created as non-protected by default.
- **Frontend UI Changes:**
  - Visually indicate protected entities.
  - Handle 403 "protected entity" responses from the backend gracefully, displaying the informative message to the user.
- **Test Updates:**
  - If your changes modify how protected entities behave or how vulnerabilities are demonstrated, YOU MUST UPDATE the relevant tests in test_vulnerabilities.py and potentially frontend/e2e-tests/ to reflect the new expected outcomes.
  - For example, if a test previously expected to delete Alice and now should expect a 403, that test needs modification.

## 8. Simulating Exploits for Agent Testing (If Direct Test Execution Fails)
If you are an AI agent and cannot directly execute pytest or playwright tests reliably, or if tests are failing due to reasons beyond your direct code changes (e.g., environment issues on your side):

You MUST simulate the key test scenarios using cURL commands (for backend) or by describing the expected browser interactions (for frontend) to verify your changes.

Example cURL for testing protected user deletion:
1. Register/Login as attacker_user. Get ATTACKER_TOKEN.
2. Obtain ALICE_USER_ID (a protected user from PROTECTED_ENTITIES.md).
3. Execute:
   ```bash
   curl -X DELETE -H "Authorization: Bearer $ATTACKER_TOKEN" http://localhost:8000/api/users/$ALICE_USER_ID
   ```
4. Expected cURL Output: HTTP 403, JSON body containing `{"detail":"User 'AliceSmith' is protected for demo purposes..."}`.

Example Browser Interaction Description for UI test:
1. Log in as AliceSmith.
2. Navigate to Profile page.
3. Observe that AliceSmith's details are displayed, and an indicator (e.g., 🛡️) shows she is a "Protected User."
4. Attempt to change AliceSmith's username in the UI form (if available and should be blocked).
5. **Expected UI Behavior:** The UI should prevent the submission OR the API call should return a 403, and the UI should display a message like "Username of protected user AliceSmith cannot be changed."

Provide these cURL commands or detailed browser interaction steps and their expected outcomes as part of your response if direct test execution is problematic.

## 9. Forbidden Actions
- Do NOT auto-fix vulnerabilities unless the task is specifically to fix that one vulnerability.
- Do NOT modify prepopulated_data.json values for is_protected unless the task is specifically about changing an entity's protection status.
- Do NOT add dependencies outside requirements.txt or package.json without explicit instruction.
- Do NOT remove or alter the core functionality of the "Protected Entity" mechanism once implemented, unless specifically tasked.