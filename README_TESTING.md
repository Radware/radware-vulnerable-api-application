# Testing and Quality Assurance Documentation

This document provides comprehensive information about the testing suite, traffic generation capabilities, and stability enhancements for the Radware Vulnerable API.

## Table of Contents
1. [Testing Framework](#1-testing-framework)
2. [Test Suite Structure](#2-test-suite-structure)
3. [Running Tests](#3-running-tests)
4. [Traffic Generation](#4-traffic-generation)
5. [Application Stability](#5-application-stability)
6. [Vulnerability Verification](#6-vulnerability-verification)

## 1. Testing Framework

The testing framework uses:
- **pytest**: For test organization and execution
- **httpx**: For HTTP requests
- **pytest-asyncio**: For asynchronous test support

The tests verify both the functional correctness of the API and confirm that all intentional vulnerabilities are properly exploitable.

## 2. Test Suite Structure

The test suite is organized as follows:

```
tests/
├── __init__.py
├── conftest.py             # Common fixtures and setup
├── test_functional.py      # Basic API functionality tests 
└── test_vulnerabilities.py # Tests for exploiting intentional vulnerabilities
```

Key components:
- **conftest.py**: Provides fixtures for starting the API server, user authentication, and test data access
- **test_functional.py**: Verifies basic e-commerce functionality (users, products, orders, etc.)
- **test_vulnerabilities.py**: Confirms all security vulnerabilities are exploitable

## 3. Running Tests

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

Run all tests:
```sh
python -m pytest tests/
```

Run only functional tests:
```sh
python -m pytest tests/test_functional.py
```

Run only vulnerability tests:
```sh
python -m pytest tests/test_vulnerabilities.py
```

Run with verbose output:
```sh
python -m pytest tests/ -v
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

## 4. Traffic Generation

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

## 5. Application Stability

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

## 6. Vulnerability Verification

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
