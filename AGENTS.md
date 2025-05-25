# AGENTS.md

## 1. Project Overview
This repository implements an intentionally vulnerable e-commerce API and frontend to demonstrate OWASP API Top 10 issues, including Broken Object Level Authorization (BOLA), Broken Function Level Authorization (BFLA), Parameter Pollution and Security Misconfiguration. AI agents should preserve these vulnerabilities unless explicitly instructed otherwise.

## 2. Core Technologies
- **Backend:** Python 3.9+, FastAPI, Uvicorn  
- **Frontend:** Flask, Jinja2 templates, vanilla JavaScript  
- **Auth:** JWT via python-jose, bcrypt password hashing  
- **Data Store:** In-memory Python dict (populated from `prepopulated_data.json` on startup)  
- **Testing:** pytest + httpx (backend), Playwright (frontend E2E)  
- **Optional Deployment:** Docker, Nginx, Supervisor  

## 3. Repository Structure
/
├── app/ # FastAPI backend
│ ├── routers/ # API route modules (auth, users, products, orders, profile)
│ ├── models/ # Pydantic schemas
│ ├── db.py # In-memory DB logic
│ ├── security.py # JWT, hashing, secrets
│ ├── main.py # FastAPI app & middleware
│ └── log_conf.json # JSON logging config
├── frontend/ # Flask frontend & E2E tests
│ ├── templates/ # Jinja2 HTML templates
│ ├── static/ # CSS, JS, images
│ ├── e2e-tests/ # Playwright scripts
│ └── main.py # Flask app entry point
├── tests/ # pytest functional and vulnerability tests
├── prepopulated_data.json # initial data for in-memory DB
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
  - Body: summary, related issue IDs, test plan  
  - Assign ≥1 reviewer, link failing tests if any  

## 5. Setup & Run
1. **Local**  
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   npm install && npx playwright install   # optional E2E
   ./run_dev.sh
   ```
2. **Docker**
   ```bash
   docker build -t vuln-api .
   docker run -d -p 80:8000 --name vuln-api vuln-api
   ```

## 6. Testing
**Backend tests:**
```bash
pytest tests/ --maxfail=1 --disable-warnings -q
```

**Frontend E2E tests:**
```bash
npx playwright test frontend/e2e-tests/ --timeout=60000
```

**Verification script:**
```bash
./verify.sh
```

## 7. Vulnerability Guidance
Preserve intentional vulnerabilities (BOLA, BFLA, Parameter Pollution) unless task explicitly demands fixes.

Annotate any changes that alter vulnerability behavior.

Refer to `openapi.yaml` for endpoint details and OWASP mappings.

## 8. Programmatic Checks
After any code edit, run:
- `pytest tests/`
- `npx playwright test frontend/e2e-tests/`

Ensure:
- Functional tests pass
- Vulnerability tests fail only when intended
- E2E flows complete without unexpected fixes

## 9. Forbidden Actions
- Do not auto-fix vulnerabilities.
- Do not modify `prepopulated_data.json` unless tasked.
- Do not add dependencies outside `requirements.txt` or `package.json`.