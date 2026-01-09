import pytest
import asyncio
import json
import os
import importlib
from pathlib import Path
from fastapi.testclient import TestClient
from pydantic import BaseModel

# Provide minimal compatibility with Pydantic v2 API when running on
# environments that still ship Pydantic v1.
if not hasattr(BaseModel, "model_validate"):

    @classmethod
    def _model_validate(cls, data):
        return cls.parse_obj(data)

    BaseModel.model_validate = _model_validate  # type: ignore

if not hasattr(BaseModel, "model_dump"):

    def _model_dump(self, *args, **kwargs):
        return self.dict(*args, **kwargs)

    BaseModel.model_dump = _model_dump  # type: ignore

# Global variables for test configuration


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client():
    """Create a FastAPI TestClient for in-memory testing."""
    import app as app_package
    import app.main as app_main

    importlib.reload(app_package)
    importlib.reload(app_main)
    return TestClient(app_main.app)


@pytest.fixture(scope="session")
def sqlite_test_client(tmp_path_factory):
    """Create a FastAPI TestClient using the SQLite backend."""
    db_file = tmp_path_factory.mktemp("sqlite") / "test.sqlite"
    os.environ["DB_MODE"] = "sqlite"
    os.environ["DB_SQLITE_PATH"] = str(db_file)
    import app as app_package
    import app.main as app_main

    importlib.reload(app_package)
    importlib.reload(app_main)
    client = TestClient(app_main.app)
    yield client
    client.close()
    # Cleanup
    if db_file.exists():
        db_file.unlink()
    os.environ.pop("DB_MODE", None)
    os.environ.pop("DB_SQLITE_PATH", None)
    importlib.reload(app_package)
    importlib.reload(app_main)


@pytest.fixture(scope="session")
def http_client(test_client):
    """Backward compatible fixture that yields the TestClient."""
    return test_client


@pytest.fixture(scope="session")
def test_data():
    """Load test data from prepopulated_data.json."""
    project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_file_path = project_root / "prepopulated_data.json"

    with open(json_file_path, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture
def admin_credentials(test_data):
    """Return credentials for the admin user."""
    admin = next(user for user in test_data["users"] if user["is_admin"])
    return {"username": admin["username"], "password": admin["password_plain"]}


@pytest.fixture
def regular_user_credentials(test_data):
    """Return credentials for a regular (non-admin) user."""
    regular_user = next(user for user in test_data["users"] if not user["is_admin"])
    return {
        "username": regular_user["username"],
        "password": regular_user["password_plain"],
    }


@pytest.fixture
def admin_token(test_client, admin_credentials):
    """Get authentication token for the admin user."""
    response = test_client.post(
        "/api/auth/login",
        params={
            "username": admin_credentials["username"],
            "password": admin_credentials["password"],
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def regular_token(test_client, regular_user_credentials):
    """Get authentication token for a regular user."""
    response = test_client.post(
        "/api/auth/login",
        params={
            "username": regular_user_credentials["username"],
            "password": regular_user_credentials["password"],
        },
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


@pytest.fixture
def non_protected_user_info(test_data):
    """Return a user that is not marked as protected."""
    return next(user for user in test_data["users"] if not user["is_protected"])


@pytest.fixture
def non_protected_token(test_client, non_protected_user_info):
    """Authentication token for a non-protected user."""
    response = test_client.post(
        "/api/auth/login",
        params={
            "username": non_protected_user_info["username"],
            "password": non_protected_user_info["password_plain"],
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def non_protected_auth_headers(non_protected_token):
    """Return auth headers for a non-protected user."""
    return {"Authorization": f"Bearer {non_protected_token}"}


@pytest.fixture
def sample_coupon(test_data):
    """Return the first coupon from prepopulated test data."""
    return test_data["coupons"][0]
