import pytest
import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
import httpx

# Global variables for test configuration
BASE_URL = "http://localhost:8000"
API_PROCESS = None

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def start_api_server():
    """Start the API server for testing."""
    # Get the project root directory
    project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Check if the server is already running
    try:
        response = httpx.get("http://localhost:8000", timeout=2)
        if response.status_code == 200:
            print("API server is already running, using the existing instance")
            yield
            return
    except:
        pass
    
    # Start the server process
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            response = httpx.get("http://localhost:8000", timeout=2)
            if response.status_code == 200:
                print("API server started for testing")
                break
        except:
            pass
        retries += 1
        time.sleep(2)
    
    if retries == max_retries:
        process.terminate()
        process.wait()
        raise Exception("Failed to start API server")
    
    # Yield control back to the tests
    yield
    
    # Cleanup after tests
    process.terminate()
    process.wait()
    print("API server stopped")

@pytest.fixture(scope="session")
def http_client():
    """Create a httpx client for testing."""
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        yield client

@pytest.fixture(scope="session")
def async_client():
    """Create an async httpx client for testing."""
    return httpx.AsyncClient(base_url=BASE_URL, timeout=10.0)

@pytest.fixture(scope="session")
def test_data():
    """Load test data from prepopulated_data.json."""
    project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_file_path = project_root / "prepopulated_data.json"
    
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    return data

@pytest.fixture
def admin_credentials(test_data):
    """Return credentials for the admin user."""
    admin = next(user for user in test_data["users"] if user["is_admin"])
    return {
        "username": admin["username"],
        "password": admin["password_plain"]
    }

@pytest.fixture
def regular_user_credentials(test_data):
    """Return credentials for a regular (non-admin) user."""
    regular_user = next(user for user in test_data["users"] if not user["is_admin"])
    return {
        "username": regular_user["username"],
        "password": regular_user["password_plain"]
    }

@pytest.fixture
def admin_token(http_client, admin_credentials):
    """Get authentication token for the admin user."""
    response = http_client.post(
        f"/auth/login?username={admin_credentials['username']}&password={admin_credentials['password']}"
    )
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def regular_token(http_client, regular_user_credentials):
    """Get authentication token for a regular user."""
    response = http_client.post(
        f"/auth/login?username={regular_user_credentials['username']}&password={regular_user_credentials['password']}"
    )
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def admin_auth_headers(admin_token):
    """Return headers with admin token for authenticated requests."""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def regular_auth_headers(regular_token):
    """Return headers with regular user token for authenticated requests."""
    return {"Authorization": f"Bearer {regular_token}"}

@pytest.fixture
def admin_user_info(test_data):
    """Return admin user information."""
    return next(user for user in test_data["users"] if user["is_admin"])

@pytest.fixture
def regular_user_info(test_data):
    """Return information about the first non-admin user."""
    return next(user for user in test_data["users"] if not user["is_admin"])

@pytest.fixture
def another_regular_user_info(test_data):
    """Return information about a second non-admin user."""
    regular_users = [user for user in test_data["users"] if not user["is_admin"]]
    if len(regular_users) >= 2:
        return regular_users[1]
    else:
        pytest.skip("Not enough regular users in test data")
