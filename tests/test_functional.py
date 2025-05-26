import pytest
import uuid

# Test authentication functionality
def test_register_and_login(test_client):
    """Test user registration and login."""
    # Generate unique username to avoid conflicts
    unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
    
    # Register a new user
    register_response = test_client.post(
        "/api/auth/register",
        params={"username": unique_username, "email": f"{unique_username}@example.com", "password": "TestPass123!"},
    )
    assert register_response.status_code == 201
    
    # Login with the newly created user
    login_response = test_client.post(
        "/api/auth/login",
        params={"username": unique_username, "password": "TestPass123!"},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    assert login_response.json()["token_type"] == "bearer"


def test_register_duplicate_username(test_client):
    """Attempt registration with an existing username."""
    username = f"dupuser_{uuid.uuid4().hex[:8]}"
    # Initial registration should succeed
    first = test_client.post(
        "/api/auth/register",
        params={"username": username, "email": f"{username}@example.com", "password": "TestPass123!"},
    )
    assert first.status_code == 201

    # Second registration with same username should fail
    second = test_client.post(
        "/api/auth/register",
        params={"username": username, "email": f"other_{username}@example.com", "password": "TestPass123!"},
    )
    assert second.status_code == 400
    assert second.json()["detail"] == "Username already registered"


def test_register_duplicate_email(test_client):
    """Attempt registration with an existing email."""
    email = f"dupemail_{uuid.uuid4().hex[:8]}@example.com"
    username1 = f"user1_{uuid.uuid4().hex[:8]}"
    username2 = f"user2_{uuid.uuid4().hex[:8]}"

    response1 = test_client.post(
        "/api/auth/register",
        params={"username": username1, "email": email, "password": "TestPass123!"},
    )
    assert response1.status_code == 201

    response2 = test_client.post(
        "/api/auth/register",
        params={"username": username2, "email": email, "password": "TestPass123!"},
    )
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Email already registered"


@pytest.mark.parametrize(
    "params",
    [
        {"email": "a@example.com", "password": "pwd"},
        {"username": "user", "password": "pwd"},
        {"username": "user", "email": "a@example.com"},
    ],
)
def test_register_missing_fields(test_client, params):
    """Registration missing required fields should return 422."""
    response = test_client.post("/api/auth/register", params=params)
    assert response.status_code == 422


def test_login_existing_user_success(test_client, regular_user_credentials):
    """Login succeeds with valid credentials for an existing user."""
    response = test_client.post(
        "/api/auth/login",
        params={
            "username": regular_user_credentials["username"],
            "password": regular_user_credentials["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data and data["token_type"] == "bearer"


def test_login_incorrect_username(test_client):
    """Login with a non-existent username should return 401."""
    response = test_client.post(
        "/api/auth/login",
        params={"username": "unknown_user", "password": "SomePass123!"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_incorrect_password(test_client, regular_user_credentials):
    """Login with incorrect password should return 401."""
    response = test_client.post(
        "/api/auth/login",
        params={
            "username": regular_user_credentials["username"],
            "password": "WrongPass!",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


@pytest.mark.parametrize(
    "params",
    [
        {"password": "pwd"},
        {"username": "user"},
    ],
)
def test_login_missing_fields(test_client, params):
    """Login missing required fields should return 422."""
    response = test_client.post("/api/auth/login", params=params)
    assert response.status_code == 422

# Test product listing functionality
def test_list_products(test_client):
    """Test retrieving the list of products."""
    response = test_client.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    if products:
        first_product = products[0]
        assert "product_id" in first_product
        assert "name" in first_product
        assert "price" in first_product

# Test user profile functionality
def test_get_user_profile(test_client, regular_auth_headers, regular_user_info):
    """Test retrieving a user's profile."""
    user_id = regular_user_info["user_id"]
    response = test_client.get(
        f"/api/users/{user_id}",
        headers=regular_auth_headers
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["user_id"] == user_id
    assert user_data["username"] == regular_user_info["username"]
    assert user_data["email"] == regular_user_info["email"]

# Test address management functionality
def test_address_management(test_client, regular_auth_headers, regular_user_info):
    """Test creating, listing, and deleting addresses."""
    user_id = regular_user_info["user_id"]
    
    # List addresses
    list_response = test_client.get(
        f"/api/users/{user_id}/addresses",
        headers=regular_auth_headers
    )
    assert list_response.status_code == 200
    initial_addresses = list_response.json()
    
    # Create a new address
    create_response = test_client.post(
        f"/api/users/{user_id}/addresses",
        params={
            "street": "Test Street",
            "city": "Test City",
            "country": "Test Country",
            "zip_code": "12345",
            "is_default": False,
        },
        headers=regular_auth_headers,
    )
    assert create_response.status_code == 201
    new_address = create_response.json()
    
    # Verify address was created
    list_after_create = test_client.get(
        f"/api/users/{user_id}/addresses",
        headers=regular_auth_headers
    )
    assert list_after_create.status_code == 200
    after_addresses = list_after_create.json()
    assert len(after_addresses) == len(initial_addresses) + 1
    
    # Delete the new address
    delete_response = test_client.delete(
        f"/api/users/{user_id}/addresses/{new_address['address_id']}",
        headers=regular_auth_headers
    )
    assert delete_response.status_code == 204
    
    # Verify address was deleted
    list_after_delete = test_client.get(
        f"/api/users/{user_id}/addresses",
        headers=regular_auth_headers
    )
    assert list_after_delete.status_code == 200
    after_delete_addresses = list_after_delete.json()
    assert len(after_delete_addresses) == len(initial_addresses)

# Test credit card management functionality
def test_credit_card_management(test_client, regular_auth_headers, regular_user_info):
    """Test creating and listing credit cards."""
    user_id = regular_user_info["user_id"]
    
    # List credit cards
    list_response = test_client.get(
        f"/api/users/{user_id}/credit-cards",
        headers=regular_auth_headers
    )
    assert list_response.status_code == 200
    initial_cards = list_response.json()
    
    # Create a new credit card
    create_response = test_client.post(
        f"/api/users/{user_id}/credit-cards",
        params={
            "cardholder_name": "Test User",
            "card_number": "4111111111111111",
            "expiry_month": "12",
            "expiry_year": "2029",
            "cvv": "123",
            "is_default": "false"
        },
        headers=regular_auth_headers
    )
    assert create_response.status_code == 201
    new_card = create_response.json()
    
    # Verify card was created
    list_after_create = test_client.get(
        f"/api/users/{user_id}/credit-cards",
        headers=regular_auth_headers
    )
    assert list_after_create.status_code == 200
    after_cards = list_after_create.json()
    assert len(after_cards) == len(initial_cards) + 1
    
    # Clean up - delete the new card
    delete_response = test_client.delete(
        f"/api/users/{user_id}/credit-cards/{new_card['card_id']}",
        headers=regular_auth_headers
    )
    assert delete_response.status_code == 204

# Test order functionality
def test_order_creation_and_retrieval(test_client, regular_auth_headers, regular_user_info, test_data):
    """Test creating and retrieving orders."""
    user_id = regular_user_info["user_id"]
    
    # Get user's address and credit card for the order
    user_address = regular_user_info["addresses"][0]
    user_card = regular_user_info["credit_cards"][0]
    
    # Get a product to order
    product = test_data["products"][0]
    
    # Create an order
    create_response = test_client.post(
        f"/api/users/{user_id}/orders",
        params={
            "address_id": user_address['address_id'],
            "credit_card_id": user_card['card_id'],
            "product_id_1": product['product_id'],
            "quantity_1": 1,
        },
        headers=regular_auth_headers,
    )
    assert create_response.status_code == 201
    new_order = create_response.json()
    
    # Verify order was created
    assert new_order["user_id"] == user_id
    assert new_order["address_id"] == user_address["address_id"]
    assert new_order["credit_card_id"] == user_card["card_id"]
    assert len(new_order["items"]) == 1
    assert new_order["items"][0]["product_id"] == product["product_id"]
    assert new_order["items"][0]["quantity"] == 1
    
    # Retrieve the order
    get_response = test_client.get(
        f"/api/users/{user_id}/orders/{new_order['order_id']}",
        headers=regular_auth_headers
    )
    assert get_response.status_code == 200
    retrieved_order = get_response.json()
    assert retrieved_order["order_id"] == new_order["order_id"]
    
    # List all orders
    list_response = test_client.get(
        f"/api/users/{user_id}/orders",
        headers=regular_auth_headers
    )
    assert list_response.status_code == 200
    orders = list_response.json()
    assert any(order["order_id"] == new_order["order_id"] for order in orders)

# Test product search functionality
def test_product_search(test_client):
    """Test searching for products by name."""
    # Search for a product with a common term
    response = test_client.get("/api/products/search", params={"name": "pro"})
    assert response.status_code == 200
    results = response.json()
    
    # Verify results contain products with 'pro' in the name
    assert isinstance(results, list)
    if len(results) > 0:
        for product in results:
            assert "pro" in product["name"].lower()
    
    # Test with a more specific search term
    specific_response = test_client.get("/api/products/search", params={"name": "laptop"})
    assert specific_response.status_code == 200
    specific_results = specific_response.json()
    
    # Verify specific results
    if len(specific_results) > 0:
        for product in specific_results:
            assert "laptop" in product["name"].lower()


# --- User Router Tests ---

def test_create_user_success(test_client):
    """Create a new user with unique credentials."""
    uname = f"user_{uuid.uuid4().hex[:8]}"
    resp = test_client.post(
        "/api/users",
        params={"username": uname, "email": f"{uname}@example.com", "password": "Pass123!"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == uname
    assert data["email"] == f"{uname}@example.com"
    assert "user_id" in data


def test_create_user_duplicate_username(test_client, regular_user_info):
    """Creating a user with an existing username should fail."""
    resp = test_client.post(
        "/api/users",
        params={
            "username": regular_user_info["username"],
            "email": f"dup_{uuid.uuid4().hex[:8]}@example.com",
            "password": "Pass123!",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == f"Username '{regular_user_info['username']}' already registered"


def test_create_user_duplicate_email(test_client, regular_user_info):
    """Creating a user with an existing email should fail."""
    resp = test_client.post(
        "/api/users",
        params={
            "username": f"dup_{uuid.uuid4().hex[:8]}",
            "email": regular_user_info["email"],
            "password": "Pass123!",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == f"Email '{regular_user_info['email']}' already registered"


@pytest.mark.parametrize(
    "params",
    [
        {"email": "a@example.com", "password": "pwd"},
        {"username": "user", "password": "pwd"},
        {"username": "user", "email": "a@example.com"},
    ],
)
def test_create_user_missing_fields(test_client, params):
    """Missing required fields should return 422."""
    resp = test_client.post("/api/users", params=params)
    assert resp.status_code == 422


def test_create_user_invalid_email(test_client):
    """Invalid email format should return 422."""
    resp = test_client.post(
        "/api/users",
        params={"username": "bademail", "email": "not-an-email", "password": "x"},
    )
    assert resp.status_code == 422


def test_list_users_requires_auth(test_client):
    """Listing users without auth should fail."""
    resp = test_client.get("/api/users")
    assert resp.status_code == 401


def test_list_users_authenticated(test_client, regular_auth_headers):
    """Authenticated user can list all users."""
    resp = test_client.get("/api/users", headers=regular_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_user_no_auth_required(test_client, regular_user_info):
    """Retrieving a user does not require authentication."""
    user_id = regular_user_info["user_id"]
    resp = test_client.get(f"/api/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["user_id"] == user_id


def test_get_user_not_found(test_client):
    resp = test_client.get(f"/api/users/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_user_invalid_uuid(test_client):
    resp = test_client.get("/api/users/not-a-uuid")
    assert resp.status_code == 422


def test_update_non_protected_user(test_client):
    """Update username, email and is_admin on a newly created user."""
    base = f"edit_{uuid.uuid4().hex[:8]}"
    create_resp = test_client.post(
        "/api/users",
        params={"username": base, "email": f"{base}@example.com", "password": "Pass123!"},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["user_id"]

    new_name = base + "_upd"
    new_email = f"{new_name}@example.com"
    resp = test_client.put(
        f"/api/users/{user_id}",
        params={"username": new_name, "email": new_email, "is_admin": "true"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == new_name
    assert data["email"] == new_email
    assert data["is_admin"] is True


def test_update_protected_user_username_forbidden(test_client, test_data):
    """Changing username of a protected user is forbidden."""
    alice = next(u for u in test_data["users"] if u["username"] == "AliceSmith")
    resp = test_client.put(
        f"/api/users/{alice['user_id']}", params={"username": "newalice"}
    )
    assert resp.status_code == 403
    expected = (
        f"User '{alice['username']}' is protected. "
        "Username and email cannot be changed. Other fields might be modifiable for demo purposes."
    )
    assert resp.json()["detail"] == expected


def test_update_protected_user_is_admin_allowed(test_client, test_data):
    """is_admin can be changed on a protected user."""
    alice = next(u for u in test_data["users"] if u["username"] == "AliceSmith")
    resp = test_client.put(
        f"/api/users/{alice['user_id']}", params={"is_admin": "true"}
    )
    assert resp.status_code == 200
    assert resp.json()["is_admin"] is True


def test_update_user_duplicate_username(test_client, test_data):
    grace = next(u for u in test_data["users"] if u["username"] == "GraceWilson")
    henry = next(u for u in test_data["users"] if u["username"] == "HenryMoore")
    resp = test_client.put(
        f"/api/users/{henry['user_id']}", params={"username": grace["username"]}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == f"Username '{grace['username']}' already in use."


def test_update_user_duplicate_email(test_client, test_data):
    grace = next(u for u in test_data["users"] if u["username"] == "GraceWilson")
    henry = next(u for u in test_data["users"] if u["username"] == "HenryMoore")
    resp = test_client.put(
        f"/api/users/{henry['user_id']}", params={"email": grace["email"]}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == f"Email '{grace['email']}' already in use."


def test_update_user_no_data(test_client, test_data):
    henry = next(u for u in test_data["users"] if u["username"] == "HenryMoore")
    resp = test_client.put(f"/api/users/{henry['user_id']}")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "No update data provided"


def test_update_user_not_found(test_client):
    resp = test_client.put(
        f"/api/users/{uuid.uuid4()}", params={"username": "nouser"}
    )
    assert resp.status_code == 404


def test_update_user_invalid_uuid(test_client):
    resp = test_client.put("/api/users/not-a-uuid", params={"username": "x"})
    assert resp.status_code == 422


def test_delete_protected_user_forbidden(test_client, test_data):
    alice = next(u for u in test_data["users"] if u["username"] == "AliceSmith")
    resp = test_client.delete(f"/api/users/{alice['user_id']}")
    assert resp.status_code == 403
    expected = (
        f"User '{alice['username']}' is protected for demo purposes and cannot be deleted. "
        "Please try with a non-protected user or one you created."
    )
    assert resp.json()["detail"] == expected


def test_delete_non_protected_user_success(test_client):
    uname = f"del_{uuid.uuid4().hex[:8]}"
    create_resp = test_client.post(
        "/api/users",
        params={"username": uname, "email": f"{uname}@example.com", "password": "Pass123!"},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["user_id"]

    delete_resp = test_client.delete(f"/api/users/{user_id}")
    assert delete_resp.status_code == 204

    get_resp = test_client.get(f"/api/users/{user_id}")
    assert get_resp.status_code == 404


def test_delete_user_not_found(test_client):
    resp = test_client.delete(f"/api/users/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_user_invalid_uuid(test_client):
    resp = test_client.delete("/api/users/not-a-uuid")
    assert resp.status_code == 422
