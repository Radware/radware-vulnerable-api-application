# Testing Documentation for Radware Vulnerable API

This document provides instructions for setting up, testing, and verifying the Radware Vulnerable API application.

## 1. Environment Setup

### Prerequisites
- Python 3.9+ 
- Git (for cloning the repository)

### Setting Up the Virtual Environment

1. Create a Python virtual environment:
   ```sh
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - On macOS/Linux:
     ```sh
     source .venv/bin/activate
     ```
   - On Windows:
     ```sh
     .venv\Scripts\activate
     ```

3. Install dependencies:
   ```sh
   pip install -r requirements.txt pytest httpx pytest-asyncio
   ```

## 2. Running the API

Start the application using uvicorn:

```sh
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be accessible at:
- Base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 3. Running Tests

The test suite has been designed to verify both the functional aspects of the API and confirm that the intentional vulnerabilities are exploitable.

### Running All Tests

```sh
cd /path/to/radware_vulnerable_api
pytest tests/
```

### Running Specific Test Categories

- Functional tests only:
  ```sh
  pytest tests/test_functional.py
  ```

- Vulnerability tests only:
  ```sh
  pytest tests/test_vulnerabilities.py
  ```

### Test Structure

- `tests/conftest.py`: Common fixtures and setup for all tests
- `tests/test_functional.py`: Basic API functionality tests
- `tests/test_vulnerabilities.py`: Specific tests to confirm exploitability of vulnerabilities

## 4. Generating Traffic

A traffic generator script is provided to simulate continuous legitimate API usage. This helps test the application's stability under load.

### Running the Traffic Generator

```sh
python traffic_generator.py --rps 3 --duration 60
```

Parameters:
- `--rps`: Requests per second (default: 3.0)
- `--duration`: Duration in seconds (default: 60)

The script simulates various user interactions including:
- User registration and login
- Product browsing and searching
- User profile management
- Address and credit card management
- Order creation and viewing

## 5. Application Stability

A health monitor script is provided to ensure the API remains stable during continuous operation:

### Running the Health Monitor

```sh
python health_monitor.py --interval 30 --max-failures 3
```

Parameters:
- `--interval`: Health check interval in seconds (default: 30)
- `--max-failures`: Maximum consecutive failures before restart (default: 3)

The health monitor will:
1. Periodically check if the API server is responsive
2. Automatically restart the server if it fails health checks repeatedly
3. Log all activities for troubleshooting

For optimal stability during extended testing, run both the traffic generator and health monitor:

```sh
# In terminal 1
python health_monitor.py

# In terminal 2
python traffic_generator.py --rps 3
```

## 6. Vulnerability Confirmation

The test suite confirms that the following vulnerabilities are exploitable:

### Broken Object Level Authorization (BOLA)
- Accessing other users' details, addresses, credit cards, and orders
- Creating addresses and orders for other users
- Using another user's address or credit card in your own orders

### Broken Function Level Authorization (BFLA)
- Creating, updating, and deleting products as non-admin users
- Updating product stock as non-admin users
- Deleting users as non-admin users

### Parameter Pollution
- Escalating a regular user to admin status via query parameters
- Setting internal product status flags via query parameters

### Injection Points
- Product search with special characters

## 7. Summary of Actions Taken

1. **Environment Setup**: Created a virtual environment with all necessary dependencies
2. **Test Development**: 
   - Created comprehensive test fixtures for consistent testing
   - Implemented functional tests for all API capabilities
   - Developed vulnerability tests to verify that the intentional security issues are exploitable
3. **Traffic Generation**: 
   - Created a script to simulate steady legitimate traffic
   - Added configuration options for request rate and duration
4. **Stability Enhancement**:
   - Implemented a health monitor to detect and recover from application failures
   - Added robust error handling to prevent application crashes
   - Ensured the application can run continuously without degradation
5. **Documentation**:
   - Added clear instructions for environment setup
   - Documented test running procedures
   - Explained traffic generation and monitoring capabilities
   - Confirmed the integrity of all vulnerabilities

All intentional vulnerabilities remain intact and exploitable as designed. The stability enhancements ensure the application can handle continuous traffic without disruption, making it suitable for extended demonstration and testing sessions.
