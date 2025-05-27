# Testing and Quality Assurance Guide

This document describes the backend and frontend testing strategy for the Radware Vulnerable API.  It also explains how the traffic generator and health monitor help keep the demo environment stable.
Protected demo records are documented in [PROTECTED_ENTITIES.MD](PROTECTED_ENTITIES.MD) and in the
[docs/PROTECTED_ENTITIES_GUIDE.md](docs/PROTECTED_ENTITIES_GUIDE.md).

## Table of Contents
1. [Backend Testing Framework](#1-backend-testing-framework)
2. [Test Suite Structure](#2-test-suite-structure)
3. [Running Backend Tests](#3-running-backend-tests)
4. [Frontend End‑to‑End Tests](#4-frontend-end-to-end-tests)
5. [Traffic Generation](#5-traffic-generation)
6. [Application Stability](#6-application-stability)
7. [Vulnerability Verification](#7-vulnerability-verification)

## 1. Testing Framework

The testing framework uses:
- **pytest**: For test organization and execution
- **httpx**: For HTTP requests (legacy compatibility)
- **pytest-asyncio**: For asynchronous helpers

Backend tests run entirely in-memory using FastAPI's `TestClient` fixture defined in `tests/conftest.py`. The suite verifies normal API behaviour and enforces the `is_protected` rules. Destructive actions on protected records must return **HTTP 403 Forbidden**, while the same actions against non‑protected data succeed to demonstrate vulnerabilities.

Protected entities ensure core demo data stays intact. Tests should expect certain actions against these records to be rejected while still allowing non‑destructive exploits (like viewing them through BOLA).

## 2. Test Suite Structure

The test suite is organized as follows:

```
tests/
├── __init__.py
├── conftest.py             # TestClient and shared fixtures
├── test_functional.py      # Core API behaviour and 403 checks on protected entities
└── test_vulnerabilities.py # Demonstrates vulnerabilities and expected 403s
```

```
frontend/e2e-tests/
├── admin-ui.spec.ts
├── auth.spec.ts
├── cart.spec.ts
├── checkout-bola.spec.ts
├── checkout.spec.ts
├── global-ui.spec.ts
├── homepage.spec.ts
├── orders-ui.spec.ts
├── product-detail.spec.ts
├── profile-address-management.spec.ts
├── profile-bola.spec.ts
└── vulnerabilities.spec.ts
```

Notable specs:
- **profile-address-management.spec.ts** – Focuses on the logged‑in user's profile management (addresses and credit cards). It verifies CRUD operations and asserts that attempts to change protected defaults or critical fields correctly return 403 with UI warnings.
- **profile-bola.spec.ts** – Exercises BOLA scenarios by manipulating victim profiles and credit cards from another user's account. It covers both protected and non‑protected victims, confirming 403 responses and warning banners for protected data.

Key components:
- **conftest.py** – defines the `TestClient` fixture and common helpers.
- **test_functional.py** – verifies core API logic and asserts `HTTP 403` when destructive actions target protected entities.
- **test_vulnerabilities.py** – demonstrates vulnerabilities on non‑protected data, allows non‑destructive exploits on protected data, and checks that destructive attempts on protected entities return `HTTP 403`.

## 3. Running Backend Tests

### Prerequisites
- Python 3.9+
- Virtual environment with dependencies installed

### Setting Up the Environment

```sh
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt pytest httpx pytest-asyncio
```

### Running the Test Suite

Change to the project root before executing any commands:

```sh
cd /workspace/radware-vulnerable-api-application/
```

Run all backend tests:
```sh
pytest tests/
```

Run only functional tests:
```sh
pytest tests/test_functional.py
```

Run only vulnerability tests:
```sh
pytest tests/test_vulnerabilities.py
```

Run with verbose output:
```sh
pytest tests/ -v
```

### Automated Verification

A verification script is provided to automate the testing process:

```sh
./verify.sh
```

This script:
1. Sets up the virtual environment if needed
2. Starts the API server
3. Runs functional and vulnerability tests
4. Runs the traffic generator briefly
5. Shuts down the server

## 4. Frontend End‑to‑End Tests

Frontend E2E tests reside in `frontend/e2e-tests/` and use **Playwright**.  Each test run starts both the backend and frontend servers, executes the Playwright suite, then stops the servers.  Recent updates added `profile-bola.spec.ts` and removed the obsolete `vulnerability-demos.spec.ts`. The recommended sequence (also shown in `AGENTS.md` §3.2) is:

```sh
echo "Starting backend API..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-config app/log_conf.json > /tmp/backend_uvicorn.log 2>&1 & APP_PID=$!
echo "Starting frontend server..."
python frontend/main.py > /tmp/frontend_flask.log 2>&1 & FRONTEND_PID=$!
sleep 10  # wait for health
npx playwright test frontend/e2e-tests/profile-bola.spec.ts
kill $APP_PID
kill $FRONTEND_PID
```

Some UI demos are gated behind a toggle.  Set `localStorage['uiVulnerabilityFeaturesEnabled']` to `'true'` to activate the vulnerability demo interfaces.

## 5. Traffic Generation

The traffic generator simulates legitimate user interactions with the API, useful for load testing and stability verification.

### Running the Traffic Generator

```sh
python traffic_generator.py [--rps RPS] [--duration SECONDS]
```

Parameters:
- `--rps`: Requests per second (default: 3.0)
- `--duration`: Duration in seconds (default: 60, or run indefinitely if not specified)

### Traffic Patterns

The generator simulates:
- User registration and login
- Product browsing and searching
- Profile management (addresses, credit cards)
- Order creation and viewing

## 6. Application Stability

The system includes a health monitor to ensure continuous operation, particularly useful for demonstrations and extended testing.

### Running the Health Monitor

```sh
python health_monitor.py [--interval SECONDS] [--max-failures COUNT]
```

Parameters:
- `--interval`: Health check interval in seconds (default: 30)
- `--max-failures`: Maximum consecutive failures before restart (default: 3)

### Monitoring Features

The health monitor:
- Periodically checks API server responsiveness
- Automatically restarts the server if it becomes unresponsive
- Maintains detailed logs of server health status
- Ensures the application can run continuously without manual intervention

### Recommended Setup for Continuous Operation

Run both the health monitor and traffic generator:

```sh
# Terminal 1: Start health monitor
python health_monitor.py

# Terminal 2: Start traffic generator for continuous operation
python traffic_generator.py --rps 3
```

## 7. Vulnerability Verification

The test suite confirms the following vulnerabilities are present and exploitable:

### Broken Object Level Authorization (BOLA)
- ✅ Accessing other users' details, addresses, credit cards, and orders
- ✅ Creating addresses and orders for other users
- ✅ Using another user's address or credit card in orders

### Broken Function Level Authorization (BFLA)
- ✅ Creating, updating, and deleting products as non-admin users
- ✅ Updating product stock as non-admin users
- ✅ Deleting users as non-admin users

### Parameter Pollution
- ✅ Escalating user privileges to admin via query parameters
- ✅ Setting internal product status via query parameters

### Injection Points
- ✅ Product search with special characters

All vulnerabilities are intentional and maintained for educational purposes. The application should **never** be deployed in a production environment.
