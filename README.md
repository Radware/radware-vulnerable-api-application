# Vulnerable E-commerce API

*Version: v1.1.0*

## 1. Introduction

**Purpose:** This project is a deliberately vulnerable API-based e-commerce application built using Python and FastAPI. Its primary goal is to demonstrate common API security vulnerabilities, with a strong focus on Broken Object Level Authorization (BOLA), Broken Function Level Authorization (BFLA), and Mass Assignment/Parameter Pollution. The API is designed to primarily use path and query parameters for interactions, minimizing the use of request bodies for vulnerable endpoints to simulate specific attack vectors.

**Design:**
*   **Pure API-focused:** A minimal Flask-based demo UI is included under `frontend/`,
    but the primary interaction is via API clients (e.g., Postman, curl, custom scripts).
*   **Framework:** FastAPI (Python) for its modern features, speed, and automatic OpenAPI documentation.
*   **Database:** A simple in-memory Python dictionary acts as the database to keep the setup lightweight and focus on API logic rather than database intricacies. Data is ephemeral and resets on application restart.
*   **Authentication:** JWT (JSON Web Tokens) are used for authenticating users. Tokens are passed via Authorization headers (`Bearer <token>`).
*   **Vulnerability Focus:** Endpoints are intentionally designed with security flaws to serve as learning examples.

## 2. Features

The application simulates basic e-commerce functionalities:

*   **User Management:**
    *   User registration (`POST /api/auth/register`)
    *   User login (`POST /api/auth/login`)
    *   Get user details (`GET /api/users/{user_id}`)
    *   Update user details (`PUT /api/users/{user_id}`)
    *   Delete user (`DELETE /api/users/{user_id}`)
*   **Product Catalog:**
    *   Create product (`POST /api/products/`)
    *   Get all products (`GET /api/products/`)
    *   Get product by ID (`GET /api/products/{product_id}`)
    *   Search products by name (`GET /api/products/search`)
    *   Update product (`PUT /api/products/{product_id}`)
    *   Delete product (`DELETE /api/products/{product_id}`)
*   **Stock Management:**
    *   Update product stock (`PUT /api/stock/{product_id}`)
*   **User Profiles (Addresses & Credit Cards):**
    *   Manage user addresses (CRUD operations under `/api/users/{user_id}/addresses`)
    *   Manage user credit cards (CRUD operations under `/api/users/{user_id}/credit-cards`) - *Note: Card numbers are "hashed" for storage simulation.*
*   **Order Management:**
    *   Create an order for a user (`POST /api/users/{user_id}/orders`)
    *   Get orders for a user (`GET /api/users/{user_id}/orders`)
    *   Get specific order details (`GET /api/users/{user_id}/orders/{order_id}`)
*   **Coupons & Discounts:**
    *   Look up a coupon (`GET /api/coupons/{coupon_code}`)
    *   Create coupon (`POST /api/admin/coupons`) – no admin check (BFLA demo)
    *   Delete coupon (`DELETE /api/admin/coupons/{coupon_code_or_id}`)
    *   Apply coupon to an order (`POST /api/users/{user_id}/orders/{order_id}/apply-coupon?coupon_code=...`)

## 3. Technical Details

*   **Language:** Python 3.9+
*   **Framework:** FastAPI
*   **Dependencies:**
    *   `fastapi`: Web framework
    *   `uvicorn[standard]`: ASGI server
    *   `pydantic`: Data validation and settings management
    *   `python-jose[cryptography]`: JWT handling
    *   `passlib[bcrypt]`: Password hashing
*   **API Specification:** OpenAPI 3.x. The schema is defined in `openapi.yaml` and also accessible interactively via:
    *   Swagger UI: `http://localhost:8000/docs`
    *   ReDoc: `http://localhost:8000/redoc`

## 4. Implemented Vulnerabilities & OWASP API Top 10 Mapping

This application intentionally includes the following vulnerabilities:

### API1:2023 - Broken Object Level Authorization (BOLA)

*   **Description:** Users can access or modify data objects belonging to other users by manipulating object IDs in the request (typically in path parameters or query parameters). The application fails to verify if the authenticated user has the right to perform the requested action on the specific object.
*   **Note:** Destructive actions on protected users themselves still return HTTP 403. Addresses and credit cards belonging to a protected user can usually be modified or removed, but attempts fail if they would delete the user's last item. Protected users are free to set any of their addresses or cards as the default; the prior default simply has `is_default` cleared.
*   **Affected Endpoints & Exploitation:**
    *   **User Details:**
        *   `GET /api/users/{user_id}`: Any authenticated user can view another user's details by providing their `user_id`.
        *   `PUT /api/users/{user_id}`: Any authenticated user can attempt to update another user's details.
    *   **User Addresses:** (Operate on `user_id` from path without matching authenticated user)
        *   `GET /api/users/{user_id}/addresses`
        *   `POST /api/users/{user_id}/addresses`
        *   `GET /api/users/{user_id}/addresses/{address_id}`
        *   `PUT /api/users/{user_id}/addresses/{address_id}`
        *   `DELETE /api/users/{user_id}/addresses/{address_id}`
    *   **User Credit Cards:** (Operate on `user_id` from path without matching authenticated user)
        *   `GET /api/users/{user_id}/credit-cards`
        *   `POST /api/users/{user_id}/credit-cards`
        *   `GET /api/users/{user_id}/credit-cards/{card_id}`
        *   `DELETE /api/users/{user_id}/credit-cards/{card_id}`
    *   **User Orders:** (Operate on `user_id` from path without matching authenticated user)
        *   `GET /api/users/{user_id}/orders`
        *   `POST /api/users/{user_id}/orders`:
            *   BOLA on `user_id` in path: An attacker can place an order for another user.
            *   BOLA on `address_id` & `credit_card_id` in query parameters: An attacker can use their own token but specify another user's address or credit card ID (if known) to place an order, potentially charging it to another user or shipping to an unauthorized address.
        *   `GET /api/users/{user_id}/orders/{order_id}`
*   **How to Test:**
    1.  Register two users, User A and User B.
    2.  Authenticate as User A.
    3.  Attempt to access/modify User B's resources using User B's `user_id` in the path or User B's `address_id`/`card_id` in query parameters where applicable.

### API3:2023 - Broken Object Property Level Authorization

This often manifests as Mass Assignment or Parameter Pollution, where users can illegitimately modify object properties.

*   **Description:** The application allows users to modify sensitive object properties (e.g., `is_admin`, `internal_status`) that they should not have control over, typically by including them as unexpected query parameters.
*   **Affected Endpoints & Exploitation:**
    *   `PUT /api/users/{user_id}?is_admin=true`: A regular user can attempt to escalate their privileges to admin by updating their own profile and adding `is_admin=true` as a query parameter. The endpoint improperly processes this parameter.
    *   `PUT /api/products/{product_id}?internal_status=discontinued`: A user (even non-admin due to BFLA) can modify a product's `internal_status` field, which should ideally be restricted.
*   **How to Test:**
    1.  Authenticate as a regular user.
    2.  Call `PUT /users/{your_user_id}` with a valid payload for updatable fields (e.g., email) and append `&is_admin=true` (or `?is_admin=true` if no other query params) to the URL. Check if the user's `is_admin` status changes.
    3.  Call `PUT /products/{product_id}` and append `&internal_status=some_value` to the URL.

### API5:2023 - Broken Function Level Authorization (BFLA)

*   **Description:** Regular users can access administrative functions or functionalities reserved for privileged users because the application does not adequately check the user's role or permissions before granting access to these functions.
*   **Affected Endpoints & Exploitation:**
    *   **Note:** Deleting or modifying protected demo entities returns HTTP 403 with a "protected for demo" message.
    *   `POST /api/products/`: Any authenticated user can create new products (typically an admin function).
    *   `DELETE /api/products/{product_id}`: Any authenticated user can delete products.
    *   `PUT /api/stock/{product_id}`: Any authenticated user can update product stock levels. If the product is protected, the action is logged but still allowed.
    *   `DELETE /api/users/{user_id}`: Any authenticated user can delete *any* other user if they know their `user_id`. This is a combination of BFLA (no admin check for delete function) and BOLA (can target any user).
*   **How to Test:**
    1.  Authenticate as a regular (non-admin) user.
    2.  Attempt to call the administrative endpoints listed above.

### API8:2023 - Security Misconfiguration

*   **Description:** This category covers security flaws resulting from improper configuration or setup.
*   **Manifestations in this project:**
    *   **Hardcoded Secrets:** The `SECRET_KEY` for JWT signing is hardcoded in `app/security.py`. In a real application, this should be sourced from environment variables or a secure configuration management system.
    *   **Verbose Errors (Potentially):** While FastAPI handles many errors gracefully, detailed stack traces might be exposed if `debug=True` were used in a production-like setting (uvicorn default is often non-debug).
    *   **Intentional Vulnerabilities by Design:** The entire application is "misconfigured" to be vulnerable for educational purposes.
*   **How to Test:** Review `app/security.py` for the hardcoded secret.

### Potential for Injection (General Category - could relate to API8 or others based on impact)

*   **Description:** The application might be vulnerable to injection attacks if user input is not properly sanitized before being used in queries or commands.
*   **Affected Endpoints & Exploitation:**
    *   `GET /api/products/search?name=<query>`: The `name` query parameter is used for searching products. While the current in-memory search is a simple string `in` check, if this were backed by a SQL database and the query constructed unsafely, it could be vulnerable to SQL Injection. The current implementation might allow for unexpected behavior depending on how the substring search is performed with special characters.
*   **How to Test:**
    1.  Try injecting various characters and sequences into the `name` parameter of the product search endpoint (e.g., `'`, `"` `*`, `;`, basic XSS payloads if it were reflected, etc.) to observe behavior. For the current in-memory setup, the impact is limited, but it demonstrates an input vector.

## 5. Setup and Running the Application

### Prerequisites

*   Docker (Recommended)
*   Python 3.9+ (if running locally without Docker)
*   Git (for cloning, though not strictly necessary if files are manually downloaded)

### Configuration via Environment Variables

The application selects its database backend based on environment variables:

* `DB_MODE` – one of `memory` (default), `sqlite`, or `external`.
* `DB_SQLITE_PATH` – location for the SQLite file when using `DB_MODE=sqlite`.
  Defaults to `/app/data/db.sqlite` in the container.
* `DB_URL` – used only when `DB_MODE=external`. Provide a full SQLAlchemy
  connection string. If the URL points to a SQLite file the built-in SQLite
  backend is reused. For other databases (e.g., PostgreSQL/MySQL) make sure the
  appropriate drivers are installed.
* `DB_SYNC_PEER` – optional base URL of another instance for database
  synchronization.
* `DB_SYNC_INTERVAL` – polling interval in seconds when `DB_SYNC_PEER` is set
  (default: 60).
* `DB_SKIP_SCHEMA_INIT` – set to `true` to skip automatic table creation. Use
  this when the database schema is managed externally.
* `DB_SKIP_AUTO_SEED` – set to `true` to skip loading `prepopulated_data.json`
  on startup. Useful when a peer or init job already seeded the data.

#### Example Configurations

**In-memory database (ephemeral)**
```sh
 docker run -d -p 8000:80 \
  -e DB_MODE=memory \
  --name radware-vuln-api vulnerable-ecommerce-api
```
Data is stored only in memory and will be lost when the container stops.

**SQLite inside the container**
```sh
docker run -d -p 8000:80 \
  -e DB_MODE=sqlite \
  -e DB_SQLITE_PATH=/data/db.sqlite \
  -v $(pwd)/data:/data \
  --name radware-vuln-api vulnerable-ecommerce-api
```
This stores the SQLite database in `./data/db.sqlite` on the host. Remove the `-v` option if you want the database kept only inside the container and discarded when it is removed.

**External database**
```sh
docker run -d -p 8000:80 \
  -e DB_MODE=external \
  -e DB_URL=postgresql+psycopg2://user:pass@dbserver/dbname \
  --name radware-vuln-api vulnerable-ecommerce-api
```
Replace the connection string with one appropriate for your database engine.

**Peer sync**
```sh
docker run -d -p 8000:80 \
  -e DB_SYNC_PEER=http://other-instance:8000 \
  -e DB_SYNC_INTERVAL=30 \
  --name radware-vuln-api vulnerable-ecommerce-api
```
The service will periodically push and pull data with the peer.

### Instructions

#### Using Docker (Recommended)

1.  **Build the Docker image:**
    Open a terminal in the project's root directory (where `Dockerfile` is located) and run:
    ```sh
    docker build -t vulnerable-ecommerce-api .
    ```

2.  **Run the Docker container:**
    ```sh
    docker run -d -p 8000:80 --name radware-vuln-api vulnerable-ecommerce-api
    ```
    The API will be accessible at `http://localhost:8000`.

    The container defaults to a single Uvicorn worker. Set `UVICORN_WORKERS`
    if you need additional workers:
    ```sh
    docker run -d -p 8000:80 -e UVICORN_WORKERS=2 \
      --name radware-vuln-api vulnerable-ecommerce-api
    ```

#### Running Locally (Alternative)

1.  **Clone the Repository (if applicable):**
    If you have the project as a git repository:
    ```sh
    git clone <repository_url>
    cd <repository_directory>
    ```
    Otherwise, ensure you are in the project's root directory.

2.  **Create and Activate a Virtual Environment:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Run the Application:**
    ```sh
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The `--reload` flag enables auto-reloading on code changes, useful for development.
    To run both the API and the demo UI together, use the provided `run_dev.sh` script instead.

### Accessing the API

*   **Base URL:** `http://localhost:8000`
*   **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
*   **Alternative API Documentation (ReDoc):** `http://localhost:8000/redoc`

## 6. Disclaimer

**⚠️ This application is intentionally vulnerable and designed for educational purposes ONLY. ⚠️**

*   **DO NOT deploy this application in a production environment or any publicly accessible network.**
*   **It contains severe security flaws by design.**
*   **Use responsibly and ethically for learning and demonstration.**

---

## 7. Implemented Vulnerabilities: Table Overview

This table summarizes the intentionally implemented vulnerabilities and their exploitation methods:

| Vulnerability Type (OWASP API 2023) | Brief Description | Example Exploitable Endpoint(s) | Exploitation Method Summary |
|-------------------------------------|-------------------|-------------------------------|----------------------------|
| **API1:2023 - Broken Object Level Authorization (BOLA)** | Users can access or modify data objects belonging to other users by manipulating object IDs in the request (path/query). Protected users themselves cannot be deleted and their usernames are immutable, but their addresses and credit cards may be edited or removed unless it would delete the last item. Setting a new default is allowed; the prior default simply becomes non‑default. Non-protected objects remain fully exploitable. | `GET /api/users/{user_id}`<br>`PUT /api/users/{user_id}`<br>`GET /api/users/{user_id}/addresses`<br>`POST /api/users/{user_id}/addresses`<br>`GET /api/users/{user_id}/credit-cards`<br>`POST /api/users/{user_id}/credit-cards`<br>`PUT /api/users/{user_id}/credit-cards/{card_id}`<br>`DELETE /api/users/{user_id}/credit-cards/{card_id}`<br>`GET /api/users/{user_id}/orders`<br>`POST /api/users/{user_id}/orders` | Manipulate `user_id` in path or use another user's `address_id`/`credit_card_id` in query to access, create, update, or delete resources for other users (subject to the protected-item rules) |
| **API3:2023 - Broken Object Property Level Authorization (Parameter Pollution / Mass Assignment)** | Users can modify sensitive object properties (e.g., `is_admin`, `internal_status`) by including them as query parameters, even if not intended. Protected fields like username or email on protected users are immutable, but attributes like `is_admin` remain modifiable for demo purposes. | `PUT /api/users/{user_id}?is_admin=true`<br>`PUT /api/products/{product_id}?internal_status=discontinued` | Add privileged or internal fields as query parameters to escalate privileges or change internal state |
| **API5:2023 - Broken Function Level Authorization (BFLA)** | Regular users can access admin-only functions (e.g., product management, user deletion) due to missing role checks. | `POST /api/products`<br>`DELETE /api/products/{product_id}`<br>`PUT /api/stock/{product_id}`<br>`DELETE /api/users/{user_id}` | Call admin endpoints as a regular user (no admin check; attempts against protected demo entities return 403 but succeed on others) |
| **API8:2023 - Security Misconfiguration** | Hardcoded secrets, verbose errors, and intentional misconfiguration for demonstration. | `app/security.py`<br>Application config | Hardcoded JWT secret, potential for verbose error output |
| **Potential for Injection** | Naive input handling in product search could allow for injection if backed by a real DB. | `GET /api/products/search?name=<query>` | Pass special characters or payloads in `name` parameter (see `homepage.spec.ts`) |

---

## 8. Example API Flows

### 8.1 Valid User Flows

#### Flow 1: Regular User Registration, Login, and Order Placement

| Step | HTTP Method | Endpoint | Purpose/Parameters |
|------|-------------|----------|--------------------|
| 1 | POST | `/api/auth/register?username=alice&email=alice@example.com&password=Password123!` | Register a new user |
| 2 | POST | `/api/auth/login?username=alice&password=Password123!` | Login, obtain JWT token |
| 3 | GET | `/api/products` | Browse product catalog |
| 4 | GET | `/api/users/{user_id}/addresses` | List addresses (empty initially) |
| 5 | POST | `/api/users/{user_id}/addresses?street=Main%20St&city=Townsville&country=USA&zip_code=12345&is_default=true` | Add a shipping address |
| 6 | GET | `/api/users/{user_id}/credit-cards` | List credit cards (empty initially) |
| 7 | POST | `/api/users/{user_id}/credit-cards?cardholder_name=Alice&card_number=4111111111111111&expiry_month=12&expiry_year=2029&cvv=123&is_default=true` | Add a credit card |
| 8 | POST | `/api/users/{user_id}/orders?address_id={address_id}&credit_card_id={card_id}&product_id_1={product_id}&quantity_1=1` | Place an order |
| 9 | GET | `/api/users/{user_id}/orders` | List user's orders |

#### Flow 2: Admin Product Management (Intended, but vulnerable to BFLA)

| Step | HTTP Method | Endpoint | Purpose/Parameters |
|------|-------------|----------|--------------------|
| 1 | POST | `/api/auth/register?username=admin&email=admin@example.com&password=AdminPass123!` | Register admin user (set is_admin via parameter pollution, see below) |
| 2 | POST | `/api/auth/login?username=admin&password=AdminPass123!` | Login as admin |
| 3 | POST | `/api/products?name=New%20Product&price=99.99&description=Demo&category=Test` | Create a new product |
| 4 | PUT | `/api/products/{product_id}?price=89.99` | Update product price |
| 5 | DELETE | `/api/products/{product_id}` | Delete product |

#### Flow 3: User Updates Profile Information

| Step | HTTP Method | Endpoint | Purpose/Parameters |
|------|-------------|----------|--------------------|
| 1 | POST | `/api/auth/login?username=alice&password=Password123!` | Login as user |
| 2 | PUT | `/api/users/{user_id}?email=newalice@example.com` | Update email address |
| 3 | GET | `/api/users/{user_id}` | Retrieve updated profile |

#### Flow 4: User Manages Multiple Addresses

| Step | HTTP Method | Endpoint | Purpose/Parameters |
|------|-------------|----------|--------------------|
| 1 | POST | `/api/auth/login?username=alice&password=Password123!` | Login as user |
| 2 | POST | `/api/users/{user_id}/addresses?street=Second%20St&city=Townsville&country=USA&zip_code=54321&is_default=false` | Add a second address |
| 3 | GET | `/api/users/{user_id}/addresses` | List all addresses |
| 4 | DELETE | `/api/users/{user_id}/addresses/{address_id}` | Remove an address |

#### Flow 5: User Adds and Removes Credit Card

| Step | HTTP Method | Endpoint | Purpose/Parameters |
|------|-------------|----------|--------------------|
| 1 | POST | `/api/auth/login?username=alice&password=Password123!` | Login as user |
| 2 | POST | `/api/users/{user_id}/credit-cards?cardholder_name=Alice%20B&card_number=4222222222222222&expiry_month=11&expiry_year=2030&cvv=456&is_default=false` | Add a second credit card |
| 3 | GET | `/api/users/{user_id}/credit-cards` | List all credit cards |
| 4 | DELETE | `/api/users/{user_id}/credit-cards/{card_id}` | Remove a credit card |

### 8.2 Malicious User Flows (Vulnerability Exploitation)

#### BOLA Exploit: Accessing Another User's Data

| Step | HTTP Method | Endpoint | Purpose/Attack |
|------|-------------|----------|----------------|
| 1 | POST | `/api/auth/login?username=attacker&password=AttackerPass!` | Attacker logs in, obtains token |
| 2 | GET | `/api/users/{victim_user_id}` | Attacker accesses victim's profile |
| 3 | GET | `/api/users/{victim_user_id}/orders` | Attacker lists victim's orders |
| 4 | POST | `/api/users/{victim_user_id}/addresses?...` | Attacker creates address for victim |
| 5 | POST | `/api/users/{victim_user_id}/orders?address_id={victim_address_id}&credit_card_id={victim_card_id}&product_id_1={product_id}&quantity_1=1` | Attacker places order for victim (using victim's address/card) |

#### BFLA Exploit: Regular User Performing Admin Actions

| Step | HTTP Method | Endpoint | Purpose/Attack |
|------|-------------|----------|----------------|
| 1 | POST | `/api/auth/login?username=regular&password=RegularPass!` | Regular user logs in |
| 2 | POST | `/api/products?name=Malicious%20Product&price=1.00` | Regular user creates a product (should be admin-only) |
| 3 | DELETE | `/api/products/{product_id}` | Regular user deletes a product |
| 4 | PUT | `/api/stock/{product_id}?quantity=100` | Regular user updates product stock |
| 5 | DELETE | `/api/users/{victim_user_id}` | Regular user deletes another user |

#### Parameter Pollution Exploit: Privilege Escalation

| Step | HTTP Method | Endpoint | Purpose/Attack |
|------|-------------|----------|----------------|
| 1 | POST | `/api/auth/register?username=evil&email=evil@example.com&password=EvilPass!` | Register as a regular user |
| 2 | POST | `/api/auth/login?username=evil&password=EvilPass!` | Login as evil user |
| 3 | PUT | `/api/users/{evil_user_id}?is_admin=true` | Escalate privileges to admin via query parameter |
| 4 | POST | `/api/products?name=Backdoor&price=0.01` | Now create a product as an admin |

#### Flow 3: BOLA Exploit - Creating Address for Another User

| Step | HTTP Method | Endpoint | Purpose/Attack |
|------|-------------|----------|----------------|
| 1 | POST | `/api/auth/login?username=attacker&password=AttackerPass!` | Attacker logs in |
| 2 | POST | `/api/users/{victim_user_id}/addresses?street=Hacked%20St&city=Exploit&country=Nowhere&zip_code=99999&is_default=false` | Attacker creates address for victim |
| 3 | GET | `/api/users/{victim_user_id}/addresses` | Attacker verifies address was created |

#### Flow 4: BOLA Exploit - Using Another User's Credit Card for Order

| Step | HTTP Method | Endpoint | Purpose/Attack |
|------|-------------|----------|----------------|
| 1 | POST | `/api/auth/login?username=attacker&password=AttackerPass!` | Attacker logs in |
| 2 | GET | `/api/users/{victim_user_id}/credit-cards` | Attacker lists victim's credit cards |
| 3 | POST | `/api/users/{attacker_user_id}/orders?address_id={attacker_address_id}&credit_card_id={victim_card_id}&product_id_1={product_id}&quantity_1=1` | Attacker places order using victim's card |

#### Flow 5: Parameter Pollution - Setting Product Internal Status

| Step | HTTP Method | Endpoint | Purpose/Attack |
|------|-------------|----------|----------------|
| 1 | POST | `/api/auth/login?username=regular&password=RegularPass!` | Regular user logs in |
| 2 | PUT | `/api/products/{product_id}?internal_status=hidden` | User sets internal status field |

#### Injection Vector Example

| Step | HTTP Method | Endpoint | Purpose/Attack |
|------|-------------|----------|----------------|
| 1 | GET | `/api/products/search?name=' OR 1=1 --` | Attempt SQL/NoSQL injection (limited impact in demo, but demonstrates input vector) |

---
