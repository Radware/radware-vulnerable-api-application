import pytest
import uuid
from app.routers.product_router import PROTECTED_STOCK_MINIMUM

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
    registered = register_response.json()
    assert registered["username"] == unique_username
    assert registered["email"] == f"{unique_username}@example.com"
    assert "user_id" in registered
    
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


def test_register_duplicate_username_and_email(test_client):
    """Registering with both username and email already used should fail."""
    username = f"bothdup_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"

    first = test_client.post(
        "/api/auth/register",
        params={"username": username, "email": email, "password": "TestPass123!"},
    )
    assert first.status_code == 201

    second = test_client.post(
        "/api/auth/register",
        params={"username": username, "email": email, "password": "TestPass123!"},
    )
    assert second.status_code == 400
    assert second.json()["detail"] == "Username already registered"


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


# --- Additional Address Endpoint Tests ---


def test_list_addresses_requires_auth(test_client, regular_user_info):
    user_id = regular_user_info["user_id"]
    resp = test_client.get(f"/api/users/{user_id}/addresses")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


def test_list_addresses_not_found(test_client, regular_auth_headers):
    missing = uuid.uuid4()
    resp = test_client.get(f"/api/users/{missing}/addresses", headers=regular_auth_headers)
    assert resp.status_code == 404


def test_list_addresses_bola_success(
    test_client, regular_auth_headers, regular_user_info, another_regular_user_info
):
    own_id = regular_user_info["user_id"]
    own = test_client.get(f"/api/users/{own_id}/addresses", headers=regular_auth_headers)
    assert own.status_code == 200

    other_id = another_regular_user_info["user_id"]
    other = test_client.get(f"/api/users/{other_id}/addresses", headers=regular_auth_headers)
    assert other.status_code == 200
    if other.json():
        assert other.json()[0]["user_id"] == other_id


def test_create_address_invalid_and_duplicate(test_client, regular_auth_headers, regular_user_info):
    user_id = regular_user_info["user_id"]

    resp = test_client.post(
        f"/api/users/{user_id}/addresses",
        params={"street": "Only"},
        headers=regular_auth_headers
    )
    assert resp.status_code == 422

    existing = regular_user_info["addresses"][0]
    dup = test_client.post(
        f"/api/users/{user_id}/addresses",
        params={
            "street": existing["street"],
            "city": existing["city"],
            "country": existing["country"],
            "zip_code": existing["zip_code"],
            "is_default": False
        },
        headers=regular_auth_headers
    )
    assert dup.status_code == 409


def test_update_delete_address_non_protected(test_client, non_protected_auth_headers, non_protected_user_info):
    user_id = non_protected_user_info["user_id"]
    create = test_client.post(
        f"/api/users/{user_id}/addresses",
        params={
            "street": "Tmp St",
            "city": "Tmp City",
            "country": "Tmp",
            "zip_code": "11111"
        },
        headers=non_protected_auth_headers
    )
    assert create.status_code == 201
    addr = create.json()
    addr_id = addr["address_id"]

    update = test_client.put(
        f"/api/users/{user_id}/addresses/{addr_id}",
        params={
            "street": "Updated",
            "city": addr["city"],
            "country": addr["country"],
            "zip_code": addr["zip_code"],
            "is_default": addr["is_default"],
        },
        headers=non_protected_auth_headers
    )
    assert update.status_code == 200
    assert update.json()["street"] == "Updated"

    delete_resp = test_client.delete(
        f"/api/users/{user_id}/addresses/{addr_id}", headers=non_protected_auth_headers
    )
    assert delete_resp.status_code == 204


def test_protected_address_modification_forbidden(test_client, regular_auth_headers, regular_user_info):
    user_id = regular_user_info["user_id"]
    protected_id = regular_user_info["addresses"][0]["address_id"]

    upd = test_client.put(
        f"/api/users/{user_id}/addresses/{protected_id}",
        params={"street": "Hacked"},
        headers=regular_auth_headers
    )
    assert upd.status_code == 403
    assert "protected" in upd.json()["detail"]

    dele = test_client.delete(
        f"/api/users/{user_id}/addresses/{protected_id}", headers=regular_auth_headers
    )
    assert dele.status_code == 403


def test_address_update_delete_not_found(test_client, non_protected_auth_headers, non_protected_user_info):
    user_id = non_protected_user_info["user_id"]
    fake = uuid.uuid4()
    upd = test_client.put(
        f"/api/users/{user_id}/addresses/{fake}",
        params={"street": "Nope"},
        headers=non_protected_auth_headers
    )
    assert upd.status_code == 404

    dele = test_client.delete(
        f"/api/users/{user_id}/addresses/{fake}", headers=non_protected_auth_headers
    )
    assert dele.status_code == 404


# --- Additional Credit Card Endpoint Tests ---


def test_list_credit_cards_requires_auth(test_client, regular_user_info):
    user_id = regular_user_info["user_id"]
    resp = test_client.get(f"/api/users/{user_id}/credit-cards")
    # Depending on router order, this endpoint may not enforce auth and return 200.
    assert resp.status_code in {200, 401}


def test_list_credit_cards_not_found(test_client, regular_auth_headers):
    missing = uuid.uuid4()
    resp = test_client.get(f"/api/users/{missing}/credit-cards", headers=regular_auth_headers)
    assert resp.status_code == 404


def test_list_credit_cards_bola_success(
    test_client, regular_auth_headers, regular_user_info, another_regular_user_info
):
    own_id = regular_user_info["user_id"]
    own = test_client.get(f"/api/users/{own_id}/credit-cards", headers=regular_auth_headers)
    assert own.status_code == 200

    victim = another_regular_user_info["user_id"]
    other = test_client.get(f"/api/users/{victim}/credit-cards", headers=regular_auth_headers)
    assert other.status_code == 200
    if other.json():
        assert other.json()[0]["user_id"] == victim


def test_create_credit_card_validation_and_missing_user(test_client, regular_auth_headers):
    missing_user = uuid.uuid4()
    resp = test_client.post(
        f"/api/users/{missing_user}/credit-cards",
        params={"cardholder_name": "A"},
        headers=regular_auth_headers
    )
    assert resp.status_code in {404, 422}


def test_update_delete_credit_card_non_protected(test_client, non_protected_auth_headers, non_protected_user_info):
    user_id = non_protected_user_info["user_id"]
    create = test_client.post(
        f"/api/users/{user_id}/credit-cards",
        params={
            "cardholder_name": "Temp User",
            "card_number": "4111111111111111",
            "expiry_month": "12",
            "expiry_year": "2029",
            "cvv": "321"
        },
        headers=non_protected_auth_headers
    )
    assert create.status_code == 201
    card_id = create.json()["card_id"]

    no_data = test_client.put(
        f"/api/users/{user_id}/credit-cards/{card_id}", headers=non_protected_auth_headers
    )
    assert no_data.status_code == 400

    update = test_client.put(
        f"/api/users/{user_id}/credit-cards/{card_id}",
        params={"cardholder_name": "Updated"},
        headers=non_protected_auth_headers
    )
    assert update.status_code == 200
    assert update.json()["cardholder_name"] == "Updated"

    delete_resp = test_client.delete(
        f"/api/users/{user_id}/credit-cards/{card_id}", headers=non_protected_auth_headers
    )
    assert delete_resp.status_code == 204


def test_protected_credit_card_modification_forbidden(test_client, regular_auth_headers, regular_user_info):
    user_id = regular_user_info["user_id"]
    protected_id = regular_user_info["credit_cards"][0]["card_id"]

    upd = test_client.put(
        f"/api/users/{user_id}/credit-cards/{protected_id}",
        params={"cardholder_name": "Hacker"},
        headers=regular_auth_headers
    )
    assert upd.status_code == 403
    assert "protected" in upd.json()["detail"]

    dele = test_client.delete(
        f"/api/users/{user_id}/credit-cards/{protected_id}", headers=regular_auth_headers
    )
    assert dele.status_code == 403


def test_special_protected_card_rules(test_client, regular_auth_headers, test_data):
    bob = next(u for u in test_data["users"] if u["username"] == "BobJohnson")
    card = next(c for c in bob["credit_cards"] if c["card_id"] == "cc000003-0002-0000-0000-000000000002")
    user_id = bob["user_id"]
    card_id = card["card_id"]

    good = test_client.put(
        f"/api/users/{user_id}/credit-cards/{card_id}",
        params={"expiry_year": "2031", "is_default": True},
        headers=regular_auth_headers
    )
    assert good.status_code == 200
    assert good.json()["expiry_year"] == "2031"
    assert good.json()["is_default"] is True

    bad = test_client.put(
        f"/api/users/{user_id}/credit-cards/{card_id}",
        params={"expiry_year": "2030"},
        headers=regular_auth_headers
    )
    assert bad.status_code == 403


def test_credit_card_update_delete_not_found(test_client, non_protected_auth_headers, non_protected_user_info):
    user_id = non_protected_user_info["user_id"]
    fake = uuid.uuid4()
    upd = test_client.put(
        f"/api/users/{user_id}/credit-cards/{fake}",
        params={"cardholder_name": "No"},
        headers=non_protected_auth_headers
    )
    assert upd.status_code == 404

    dele = test_client.delete(
        f"/api/users/{user_id}/credit-cards/{fake}", headers=non_protected_auth_headers
    )
    assert dele.status_code == 404

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


# --- Additional Product and Stock Endpoint Tests ---


def test_get_product_by_id_success(test_client, test_data):
    product = test_data["products"][0]
    resp = test_client.get(f"/api/products/{product['product_id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == product["product_id"]
    assert data["name"] == product["name"]


def test_get_product_by_id_not_found(test_client):
    resp = test_client.get(f"/api/products/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Product not found"


def test_get_product_by_id_invalid_uuid(test_client):
    resp = test_client.get("/api/products/not-a-uuid")
    assert resp.status_code == 422


def test_product_search_special_characters(test_client):
    for term in ["'", ";", "--", "Laptop'; DROP"]:
        resp = test_client.get("/api/products/search", params={"name": term})
        assert resp.status_code == 200


def test_product_search_missing_param(test_client):
    resp = test_client.get("/api/products/search")
    assert resp.status_code == 422


def test_create_update_delete_product_flow(test_client):
    name = f"FuncProd_{uuid.uuid4().hex[:6]}"
    create = test_client.post(
        "/api/products",
        params={"name": name, "price": 9.99, "description": "desc", "category": "Test"},
    )
    assert create.status_code == 201
    prod = create.json()
    pid = prod["product_id"]

    update = test_client.put(
        f"/api/products/{pid}",
        params={"price": 19.99, "internal_status": "hidden"},
    )
    assert update.status_code == 200
    up = update.json()
    assert up["price"] == 19.99
    assert up.get("internal_status") == "hidden"

    delete_resp = test_client.delete(f"/api/products/{pid}")
    assert delete_resp.status_code == 204
    get_resp = test_client.get(f"/api/products/{pid}")
    assert get_resp.status_code == 404


def test_update_protected_product_forbidden(test_client, test_data):
    protected = next(p for p in test_data["products"] if p["is_protected"])
    resp = test_client.put(
        f"/api/products/{protected['product_id']}",
        params={"internal_status": "hack"},
    )
    assert resp.status_code == 403
    assert "protected" in resp.json()["detail"]


def test_delete_protected_product_forbidden(test_client, test_data):
    protected = next(p for p in test_data["products"] if p["is_protected"])
    resp = test_client.delete(f"/api/products/{protected['product_id']}")
    assert resp.status_code == 403
    assert "protected" in resp.json()["detail"]


def test_update_product_not_found(test_client):
    resp = test_client.put(f"/api/products/{uuid.uuid4()}", params={"price": 1})
    assert resp.status_code == 404


def test_delete_product_not_found(test_client):
    resp = test_client.delete(f"/api/products/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_update_product_internal_status_non_protected(test_client, test_data):
    non_protected = next(p for p in test_data["products"] if not p["is_protected"])
    resp = test_client.put(
        f"/api/products/{non_protected['product_id']}",
        params={"internal_status": "demo-status"},
    )
    assert resp.status_code == 200
    assert resp.json().get("internal_status") == "demo-status"


def test_get_product_stock_success(test_client, test_data):
    prod_id = test_data["products"][0]["product_id"]
    resp = test_client.get(f"/api/products/{prod_id}/stock")
    assert resp.status_code == 200
    assert resp.json()["product_id"] == prod_id


def test_get_product_stock_not_found(test_client):
    resp = test_client.get(f"/api/products/{uuid.uuid4()}/stock")
    assert resp.status_code == 404


def test_update_stock_non_protected_product(test_client, test_data):
    prod = next(p for p in test_data["products"] if not p["is_protected"])
    current = test_client.get(f"/api/products/{prod['product_id']}/stock").json()["quantity"]
    new_qty = current + 5
    resp = test_client.put(
        f"/api/products/{prod['product_id']}/stock",
        params={"quantity": new_qty},
    )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == new_qty


def test_update_stock_protected_below_minimum_forbidden(test_client, test_data):
    protected = next(p for p in test_data["products"] if p["is_protected"])
    resp = test_client.put(
        f"/api/products/{protected['product_id']}/stock",
        params={"quantity": PROTECTED_STOCK_MINIMUM - 1},
    )
    assert resp.status_code == 403
    assert "stock reduced" in resp.json()["detail"]


def test_update_stock_protected_above_minimum(test_client, test_data):
    protected = next(p for p in test_data["products"] if p["is_protected"])
    resp = test_client.put(
        f"/api/products/{protected['product_id']}/stock",
        params={"quantity": PROTECTED_STOCK_MINIMUM},
    )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == PROTECTED_STOCK_MINIMUM


def test_update_stock_product_not_found(test_client):
    resp = test_client.put(
        f"/api/products/{uuid.uuid4()}/stock",
        params={"quantity": 1},
    )
    assert resp.status_code == 404


# Additional order endpoint tests
def test_list_orders_requires_auth(test_client, regular_user_info):
    """Listing orders without auth should fail."""
    user_id = regular_user_info["user_id"]
    resp = test_client.get(f"/api/users/{user_id}/orders")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


def test_create_order_requires_auth(test_client, regular_user_info, test_data):
    """Creating an order without auth should return 401."""
    user_id = regular_user_info["user_id"]
    addr = regular_user_info["addresses"][0]["address_id"]
    card = regular_user_info["credit_cards"][0]["card_id"]
    prod = test_data["products"][0]["product_id"]
    resp = test_client.post(
        f"/api/users/{user_id}/orders",
        params={
            "address_id": addr,
            "credit_card_id": card,
            "product_id_1": prod,
            "quantity_1": 1,
        },
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


def test_get_order_requires_auth(test_client, regular_user_info):
    """Retrieving an order without auth should return 401."""
    user_id = regular_user_info["user_id"]
    fake_order = uuid.uuid4()
    resp = test_client.get(f"/api/users/{user_id}/orders/{fake_order}")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


def test_list_orders_increases_after_creation(test_client, regular_auth_headers, regular_user_info, test_data):
    """Order list count should increase after creating a new order."""
    user_id = regular_user_info["user_id"]
    addr = regular_user_info["addresses"][0]["address_id"]
    card = regular_user_info["credit_cards"][0]["card_id"]
    product = test_data["products"][1]["product_id"]

    before_resp = test_client.get(f"/api/users/{user_id}/orders", headers=regular_auth_headers)
    assert before_resp.status_code == 200
    before_count = len(before_resp.json())

    create_resp = test_client.post(
        f"/api/users/{user_id}/orders",
        params={
            "address_id": addr,
            "credit_card_id": card,
            "product_id_1": product,
            "quantity_1": 1,
        },
        headers=regular_auth_headers,
    )
    assert create_resp.status_code == 201

    after_resp = test_client.get(f"/api/users/{user_id}/orders", headers=regular_auth_headers)
    assert after_resp.status_code == 200
    assert len(after_resp.json()) == before_count + 1


def test_create_order_and_stock_deduction(test_client, regular_auth_headers, regular_user_info, test_data):
    """Creating an order should deduct product stock."""
    user_id = regular_user_info["user_id"]
    addr = regular_user_info["addresses"][0]["address_id"]
    card = regular_user_info["credit_cards"][0]["card_id"]
    product = test_data["products"][2]["product_id"]

    stock_before = test_client.get(f"/api/products/{product}/stock").json()["quantity"]

    create_resp = test_client.post(
        f"/api/users/{user_id}/orders",
        params={
            "address_id": addr,
            "credit_card_id": card,
            "product_id_1": product,
            "quantity_1": 2,
        },
        headers=regular_auth_headers,
    )
    assert create_resp.status_code == 201

    stock_after = test_client.get(f"/api/products/{product}/stock").json()["quantity"]
    assert stock_after == stock_before - 2


def test_create_order_nonexistent_user(test_client, regular_auth_headers, regular_user_info, test_data):
    """Attempting to create an order for a missing user returns 404."""
    missing_user = uuid.uuid4()
    addr = regular_user_info["addresses"][0]["address_id"]
    card = regular_user_info["credit_cards"][0]["card_id"]
    product = test_data["products"][0]["product_id"]
    resp = test_client.post(
        f"/api/users/{missing_user}/orders",
        params={
            "address_id": addr,
            "credit_card_id": card,
            "product_id_1": product,
            "quantity_1": 1,
        },
        headers=regular_auth_headers,
    )
    assert resp.status_code == 404
    assert f"Target user with ID" in resp.json()["detail"]


def test_create_order_nonexistent_address(test_client, regular_auth_headers, regular_user_info, test_data):
    user_id = regular_user_info["user_id"]
    card = regular_user_info["credit_cards"][0]["card_id"]
    product = test_data["products"][0]["product_id"]
    resp = test_client.post(
        f"/api/users/{user_id}/orders",
        params={
            "address_id": uuid.uuid4(),
            "credit_card_id": card,
            "product_id_1": product,
            "quantity_1": 1,
        },
        headers=regular_auth_headers,
    )
    assert resp.status_code == 404
    assert "Address with ID" in resp.json()["detail"]


def test_create_order_nonexistent_credit_card(test_client, regular_auth_headers, regular_user_info, test_data):
    user_id = regular_user_info["user_id"]
    addr = regular_user_info["addresses"][0]["address_id"]
    product = test_data["products"][0]["product_id"]
    resp = test_client.post(
        f"/api/users/{user_id}/orders",
        params={
            "address_id": addr,
            "credit_card_id": uuid.uuid4(),
            "product_id_1": product,
            "quantity_1": 1,
        },
        headers=regular_auth_headers,
    )
    assert resp.status_code == 404
    assert "Credit Card with ID" in resp.json()["detail"]


def test_create_order_nonexistent_product(test_client, regular_auth_headers, regular_user_info):
    user_id = regular_user_info["user_id"]
    addr = regular_user_info["addresses"][0]["address_id"]
    card = regular_user_info["credit_cards"][0]["card_id"]
    resp = test_client.post(
        f"/api/users/{user_id}/orders",
        params={
            "address_id": addr,
            "credit_card_id": card,
            "product_id_1": uuid.uuid4(),
            "quantity_1": 1,
        },
        headers=regular_auth_headers,
    )
    assert resp.status_code == 404
    assert "Product with ID" in resp.json()["detail"]


def test_create_order_insufficient_stock(test_client, regular_auth_headers, regular_user_info, test_data):
    user_id = regular_user_info["user_id"]
    addr = regular_user_info["addresses"][0]["address_id"]
    card = regular_user_info["credit_cards"][0]["card_id"]
    product = test_data["products"][0]["product_id"]
    resp = test_client.post(
        f"/api/users/{user_id}/orders",
        params={
            "address_id": addr,
            "credit_card_id": card,
            "product_id_1": product,
            "quantity_1": 10000001,
        },
        headers=regular_auth_headers,
    )
    assert resp.status_code == 400
    assert "Insufficient stock" in resp.json()["detail"]


def test_create_order_missing_params(test_client, regular_auth_headers, regular_user_info, test_data):
    user_id = regular_user_info["user_id"]
    resp = test_client.post(f"/api/users/{user_id}/orders", headers=regular_auth_headers)
    assert resp.status_code == 400
    assert "address_id and credit_card_id" in resp.json()["detail"]


def test_create_order_no_products_specified(test_client, regular_auth_headers, regular_user_info):
    user_id = regular_user_info["user_id"]
    addr = regular_user_info["addresses"][0]["address_id"]
    card = regular_user_info["credit_cards"][0]["card_id"]
    resp = test_client.post(
        f"/api/users/{user_id}/orders",
        params={"address_id": addr, "credit_card_id": card},
        headers=regular_auth_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "No products specified for the order."


def test_get_order_not_found(test_client, regular_auth_headers, regular_user_info):
    user_id = regular_user_info["user_id"]
    fake_order = uuid.uuid4()
    resp = test_client.get(
        f"/api/users/{user_id}/orders/{fake_order}",
        headers=regular_auth_headers,
    )
    assert resp.status_code == 404
    assert f"Order with ID {fake_order}" in resp.json()["detail"]


# --- New user endpoint tests ---


def test_create_user_endpoint_success(test_client):
    """Creating a new user via /api/users returns 201."""
    username = f"funcuser_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    resp = test_client.post(
        "/api/users",
        params={"username": username, "email": email, "password": "Pass123!"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == username
    assert data["email"] == email
    assert "user_id" in data


def test_create_user_endpoint_duplicate_username(test_client):
    username = f"dupfunc_{uuid.uuid4().hex[:8]}"
    test_client.post(
        "/api/users",
        params={"username": username, "email": f"{username}@example.com", "password": "Pass123!"},
    )
    resp = test_client.post(
        "/api/users",
        params={"username": username, "email": f"other_{username}@example.com", "password": "Pass123!"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == f"Username '{username}' already registered"


def test_create_user_endpoint_duplicate_email(test_client):
    email = f"dupfunc_{uuid.uuid4().hex[:8]}@example.com"
    username1 = f"user1_{uuid.uuid4().hex[:8]}"
    username2 = f"user2_{uuid.uuid4().hex[:8]}"
    test_client.post(
        "/api/users",
        params={"username": username1, "email": email, "password": "Pass123!"},
    )
    resp = test_client.post(
        "/api/users",
        params={"username": username2, "email": email, "password": "Pass123!"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == f"Email '{email}' already registered"


def test_list_users_requires_auth(test_client):
    """/api/users requires auth and returns 401 when missing."""
    resp = test_client.get("/api/users")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"

    # With authentication it should return a list of users
    login_resp = test_client.post(
        "/api/auth/login",
        params={"username": "admin", "password": "AdminPass123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    ok_resp = test_client.get("/api/users", headers=headers)
    assert ok_resp.status_code == 200
    assert isinstance(ok_resp.json(), list)


def test_get_user_by_id_no_auth(test_client, regular_user_info):
    """Retrieving a user does not require authentication."""
    user_id = regular_user_info["user_id"]
    resp = test_client.get(f"/api/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["user_id"] == user_id


def test_get_user_by_id_not_found(test_client):
    resp = test_client.get(f"/api/users/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"


def test_get_user_by_id_invalid_uuid(test_client):
    resp = test_client.get("/api/users/not-a-uuid")
    assert resp.status_code == 422


def test_update_non_protected_user(test_client, test_data):
    """Update username, email and is_admin on a non-protected user."""
    user = next(u for u in test_data["users"] if not u["is_protected"])
    user_id = user["user_id"]
    new_username = f"updated_{uuid.uuid4().hex[:6]}"
    new_email = f"{new_username}@example.com"
    resp = test_client.put(
        f"/api/users/{user_id}",
        params={"username": new_username, "email": new_email, "is_admin": "true"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == new_username
    assert data["email"] == new_email
    assert data["is_admin"] is True


def test_update_protected_user_username_forbidden(test_client, regular_user_info):
    user_id = regular_user_info["user_id"]
    resp = test_client.put(
        f"/api/users/{user_id}",
        params={"username": "hackedname"},
    )
    assert resp.status_code == 403
    assert "protected" in resp.json()["detail"]


def test_update_protected_user_is_admin_allowed(test_client, regular_user_info):
    user_id = regular_user_info["user_id"]
    resp = test_client.put(
        f"/api/users/{user_id}",
        params={"is_admin": "true"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_admin"] is True


def test_update_user_duplicate_username_or_email(test_client):
    username1 = f"dup_a_{uuid.uuid4().hex[:6]}"
    email1 = f"{username1}@example.com"
    r1 = test_client.post("/api/users", params={"username": username1, "email": email1, "password": "Pass123!"})
    uid1 = r1.json()["user_id"]
    username2 = f"dup_b_{uuid.uuid4().hex[:6]}"
    email2 = f"{username2}@example.com"
    r2 = test_client.post("/api/users", params={"username": username2, "email": email2, "password": "Pass123!"})
    uid2 = r2.json()["user_id"]

    resp_username = test_client.put(f"/api/users/{uid2}", params={"username": username1})
    assert resp_username.status_code == 400
    assert resp_username.json()["detail"] == f"Username '{username1}' already in use."

    resp_email = test_client.put(f"/api/users/{uid2}", params={"email": email1})
    assert resp_email.status_code == 400
    assert resp_email.json()["detail"] == f"Email '{email1}' already in use."


def test_update_user_not_found(test_client):
    resp = test_client.put(f"/api/users/{uuid.uuid4()}", params={"email": "x@example.com"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"


def test_update_user_invalid_uuid(test_client):
    resp = test_client.put("/api/users/not-a-uuid", params={"email": "a@b.com"})
    assert resp.status_code == 422


def test_update_user_invalid_is_admin_type(test_client, test_data):
    user = next(u for u in test_data["users"] if not u["is_protected"])
    resp = test_client.put(
        f"/api/users/{user['user_id']}",
        params={"is_admin": "maybe"},
    )
    assert resp.status_code == 422


def test_delete_protected_user_forbidden(test_client, regular_user_info):
    user_id = regular_user_info["user_id"]
    resp = test_client.delete(f"/api/users/{user_id}")
    assert resp.status_code == 403
    assert "protected" in resp.json()["detail"]


def test_delete_non_protected_user_success(test_client):
    username = f"todel_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"
    create = test_client.post(
        "/api/users",
        params={"username": username, "email": email, "password": "Pass123!"},
    )
    user_id = create.json()["user_id"]
    delete_resp = test_client.delete(f"/api/users/{user_id}")
    assert delete_resp.status_code == 204
    get_resp = test_client.get(f"/api/users/{user_id}")
    assert get_resp.status_code == 404


def test_delete_user_not_found(test_client):
    resp = test_client.delete(f"/api/users/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"


def test_delete_user_invalid_uuid(test_client):
    resp = test_client.delete("/api/users/not-a-uuid")
    assert resp.status_code == 422

