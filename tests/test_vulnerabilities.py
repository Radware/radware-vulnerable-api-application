import pytest
import json
import uuid

# Test for BOLA (Broken Object Level Authorization) vulnerabilities

def test_bola_user_details_access(http_client, regular_auth_headers, another_regular_user_info):
    """
    Test BOLA vulnerability: accessing another user's details
    A regular user should be able to access another user's details by knowing their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]
    
    # Try to access another user's details
    response = http_client.get(
        f"/api/users/{victim_user_id}",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the data is accessible
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["user_id"] == victim_user_id
    assert user_data["username"] == another_regular_user_info["username"]
    assert user_data["email"] == another_regular_user_info["email"]

def test_bola_user_addresses_access(http_client, regular_auth_headers, another_regular_user_info):
    """
    Test BOLA vulnerability: accessing another user's addresses
    A regular user should be able to access another user's addresses by knowing their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]
    
    # Try to access another user's addresses
    response = http_client.get(
        f"/api/users/{victim_user_id}/addresses",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the data is accessible
    assert response.status_code == 200
    addresses = response.json()
    # Verify the addresses belong to the victim user
    if addresses:
        assert addresses[0]["user_id"] == victim_user_id

def test_bola_user_credit_cards_access(http_client, regular_auth_headers, another_regular_user_info):
    """
    Test BOLA vulnerability: accessing another user's credit cards
    A regular user should be able to access another user's credit cards by knowing their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]
    
    # Try to access another user's credit cards
    response = http_client.get(
        f"/api/users/{victim_user_id}/credit-cards",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the data is accessible
    assert response.status_code == 200
    cards = response.json()
    # Verify the credit cards belong to the victim user
    if cards:
        assert cards[0]["user_id"] == victim_user_id

def test_bola_user_orders_access(http_client, regular_auth_headers, another_regular_user_info):
    """
    Test BOLA vulnerability: accessing another user's orders
    A regular user should be able to access another user's orders by knowing their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]
    
    # Try to access another user's orders
    response = http_client.get(
        f"/api/users/{victim_user_id}/orders",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the data is accessible
    assert response.status_code == 200
    # The response is a list of orders, which might be empty if the user hasn't placed any

def test_bola_create_address_for_another_user(http_client, regular_auth_headers, another_regular_user_info):
    """
    Test BOLA vulnerability: creating an address for another user
    A regular user should be able to create an address for another user by using their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]
    
    # Try to create an address for another user
    response = http_client.post(
        f"/api/users/{victim_user_id}/addresses?street=Hacked%20Street&city=Exploit%20City&country=Vulnerabilia&zip_code=31337&is_default=false",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the address is created
    assert response.status_code == 201
    new_address = response.json()
    assert new_address["user_id"] == victim_user_id
    
    # Clean up the created address
    http_client.delete(
        f"/api/users/{victim_user_id}/addresses/{new_address['address_id']}",
        headers=regular_auth_headers
    )

def test_bola_cross_user_order_creation(http_client, regular_auth_headers, another_regular_user_info, test_data):
    """
    Test BOLA vulnerability: creating an order for another user
    A regular user should be able to create an order for another user by using their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]
    victim_address = another_regular_user_info["addresses"][0]
    victim_card = another_regular_user_info["credit_cards"][0]
    product = test_data["products"][0]
    
    # Try to create an order for another user
    response = http_client.post(
        f"/api/users/{victim_user_id}/orders?address_id={victim_address['address_id']}&credit_card_id={victim_card['card_id']}&product_id_1={product['product_id']}&quantity_1=1",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the order is created
    assert response.status_code == 201
    new_order = response.json()
    assert new_order["user_id"] == victim_user_id
    assert new_order["address_id"] == victim_address["address_id"]
    assert new_order["credit_card_id"] == victim_card["card_id"]

def test_bola_using_another_users_address_for_order(http_client, regular_auth_headers, regular_user_info, another_regular_user_info, test_data):
    """
    Test BOLA vulnerability: using another user's address for an order
    A regular user should be able to use another user's address for their own order
    """
    user_id = regular_user_info["user_id"]
    user_card = regular_user_info["credit_cards"][0]
    victim_address = another_regular_user_info["addresses"][0]
    product = test_data["products"][0]
    
    # Try to create an order with another user's address
    response = http_client.post(
        f"/api/users/{user_id}/orders?address_id={victim_address['address_id']}&credit_card_id={user_card['card_id']}&product_id_1={product['product_id']}&quantity_1=1",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the order is created
    assert response.status_code == 201
    new_order = response.json()
    assert new_order["user_id"] == user_id
    assert new_order["address_id"] == victim_address["address_id"]

# Test for BFLA (Broken Function Level Authorization) vulnerabilities

def test_bfla_product_creation_by_regular_user(http_client, regular_auth_headers):
    """
    Test BFLA vulnerability: product creation by regular user
    A regular user should be able to create products (an admin-only function)
    """
    # Generate a unique product name
    product_name = f"Test Product {uuid.uuid4().hex[:8]}"
    
    # Try to create a product as a regular user
    response = http_client.post(
        f"/api/products?name={product_name}&price=99.99&description=This%20should%20not%20be%20allowed&category=Test",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the product is created
    assert response.status_code == 201
    new_product = response.json()
    assert new_product["name"] == product_name

def test_bfla_product_deletion_by_regular_user(http_client, regular_auth_headers):
    """
    Test BFLA vulnerability: product deletion by regular user
    A regular user should be able to delete products (an admin-only function)
    """
    # First create a product to delete
    product_name = f"Delete Test Product {uuid.uuid4().hex[:8]}"
    create_response = http_client.post(
        f"/api/products?name={product_name}&price=99.99&description=To%20be%20deleted&category=Test",
        headers=regular_auth_headers
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["product_id"]
    
    # Try to delete the product as a regular user
    delete_response = http_client.delete(
        f"/api/products/{product_id}",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the product is deleted
    assert delete_response.status_code == 204
    
    # Verify deletion
    get_response = http_client.get(f"/api/products/{product_id}")
    assert get_response.status_code == 404

def test_bfla_stock_update_by_regular_user(http_client, regular_auth_headers, test_data):
    """
    Test BFLA vulnerability: stock update by regular user
    A regular user should be able to update product stock (an admin-only function)
    """
    # Get a product ID to update its stock
    product_id = test_data["products"][0]["product_id"]
    
    # Get current stock
    get_stock_response = http_client.get(f"/api/products/{product_id}/stock")
    assert get_stock_response.status_code == 200
    current_stock = get_stock_response.json()["quantity"]
    
    # Update stock to a new value
    new_stock = current_stock + 1000
    update_response = http_client.put(
        f"/api/products/{product_id}/stock?quantity={new_stock}",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the stock is updated
    assert update_response.status_code == 200
    updated_stock = update_response.json()
    assert updated_stock["quantity"] == new_stock
    
    # Reset stock to original value
    http_client.put(
        f"/api/products/{product_id}/stock?quantity={current_stock}",
        headers=regular_auth_headers
    )

def test_bfla_user_deletion_by_regular_user(http_client, regular_auth_headers, test_data):
    """
    Test BFLA vulnerability: user deletion by regular user
    A regular user should be able to delete other users (an admin-only function)
    """
    # First create a test user to delete
    unique_username = f"delete_victim_{uuid.uuid4().hex[:8]}"
    register_response = http_client.post(
        f"/api/auth/register?username={unique_username}&email={unique_username}@example.com&password=DeleteMe123!"
    )
    assert register_response.status_code == 201
    victim_user_id = register_response.json()["user_id"]
    
    # Try to delete the user as a regular user
    delete_response = http_client.delete(
        f"/api/users/{victim_user_id}",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the user is deleted
    assert delete_response.status_code == 204
    
    # Verify deletion
    get_response = http_client.get(
        f"/api/users/{victim_user_id}",
        headers=regular_auth_headers
    )
    assert get_response.status_code == 404

# Test for Parameter Pollution vulnerabilities

def test_parameter_pollution_admin_escalation(http_client, regular_auth_headers, regular_user_info):
    """
    Test Parameter Pollution vulnerability: regular user escalating to admin
    A regular user should be able to become admin by adding the is_admin parameter
    """
    user_id = regular_user_info["user_id"]
    
    # Try to update user with is_admin parameter
    response = http_client.put(
        f"/api/users/{user_id}?email={regular_user_info['email']}&is_admin=true",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the update succeeds
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["is_admin"] == True
    
    # Reset the user to non-admin
    http_client.put(
        f"/api/users/{user_id}?email={regular_user_info['email']}&is_admin=false",
        headers=regular_auth_headers
    )

def test_parameter_pollution_product_internal_status(http_client, regular_auth_headers, test_data):
    """
    Test Parameter Pollution vulnerability: setting internal product status
    A regular user should be able to set a product's internal_status
    """
    product_id = test_data["products"][0]["product_id"]
    
    # Try to update product with internal_status parameter
    response = http_client.put(
        f"/api/products/{product_id}?name=Same%20Name&internal_status=hacked",
        headers=regular_auth_headers
    )
    
    # Vulnerability test passes if the update succeeds
    assert response.status_code == 200
    updated_product = response.json()
    assert updated_product["internal_status"] == "hacked"
    
    # Reset the internal_status
    http_client.put(
        f"/api/products/{product_id}?internal_status=",
        headers=regular_auth_headers
    )

# Test for Injection vulnerabilities

def test_sql_injection_in_product_search(http_client):
    """
    Test for potential SQL Injection: manipulating the product search
    Using special characters in the search might cause unexpected behavior
    """
    # Try a search with SQL injection characters
    injection_string = "' OR '1'='1"
    response = http_client.get(f"/api/products/search/?name={injection_string}")
    
    # The vulnerability is present if the search doesn't error out and potentially returns unexpected results
    assert response.status_code == 200
    
    # Since this is a simulation, we don't expect a real SQL injection to succeed
    # but we're verifying that the API accepts and processes the injection attempt
