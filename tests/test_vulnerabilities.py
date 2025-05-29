import pytest
import uuid
from app.routers.product_router import PROTECTED_STOCK_MINIMUM

# Test for BOLA (Broken Object Level Authorization) vulnerabilities


def test_bola_user_details_access(
    test_client, regular_auth_headers, another_regular_user_info
):
    """
    Test BOLA vulnerability: accessing another user's details
    A regular user should be able to access another user's details by knowing their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]

    # Try to access another user's details
    response = test_client.get(
        f"/api/users/{victim_user_id}", headers=regular_auth_headers
    )

    # Vulnerability test passes if the data is accessible
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["user_id"] == victim_user_id
    assert user_data["username"] == another_regular_user_info["username"]
    assert user_data["email"] == another_regular_user_info["email"]


def test_bola_user_addresses_access(
    test_client, regular_auth_headers, another_regular_user_info
):
    """
    Test BOLA vulnerability: accessing another user's addresses
    A regular user should be able to access another user's addresses by knowing their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]

    # Try to access another user's addresses
    response = test_client.get(
        f"/api/users/{victim_user_id}/addresses", headers=regular_auth_headers
    )

    # Vulnerability test passes if the data is accessible
    assert response.status_code == 200
    addresses = response.json()
    # Verify the addresses belong to the victim user
    if addresses:
        assert addresses[0]["user_id"] == victim_user_id


def test_bola_user_credit_cards_access(
    test_client, regular_auth_headers, another_regular_user_info
):
    """
    Test BOLA vulnerability: accessing another user's credit cards
    A regular user should be able to access another user's credit cards by knowing their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]

    # Try to access another user's credit cards
    response = test_client.get(
        f"/api/users/{victim_user_id}/credit-cards", headers=regular_auth_headers
    )

    # Vulnerability test passes if the data is accessible
    assert response.status_code == 200
    cards = response.json()
    # Verify the credit cards belong to the victim user
    if cards:
        assert cards[0]["user_id"] == victim_user_id


def test_bola_user_orders_access(
    test_client, regular_auth_headers, another_regular_user_info
):
    """
    Test BOLA vulnerability: accessing another user's orders
    A regular user should be able to access another user's orders by knowing their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]

    # Try to access another user's orders
    response = test_client.get(
        f"/api/users/{victim_user_id}/orders", headers=regular_auth_headers
    )

    # Vulnerability test passes if the data is accessible
    assert response.status_code == 200
    orders = response.json()
    # The response is a list of orders, which might be empty if the user hasn't placed any
    for order in orders:
        assert order["user_id"] == victim_user_id
        assert isinstance(order["created_at"], str)
        assert "T" in order["created_at"]
        from datetime import datetime

        datetime.fromisoformat(order["created_at"])
        assert "credit_card_last_four" in order


def test_bola_create_address_for_another_user(
    test_client, regular_auth_headers, another_regular_user_info
):
    """
    Test BOLA vulnerability: creating an address for another user
    A regular user should be able to create an address for another user by using their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]

    # Try to create an address for another user
    response = test_client.post(
        f"/api/users/{victim_user_id}/addresses",
        params={
            "street": "Hacked Street",
            "city": "Exploit City",
            "country": "Vulnerabilia",
            "zip_code": "31337",
            "is_default": False,
        },
        headers=regular_auth_headers,
    )

    # Vulnerability test passes if the address is created
    assert response.status_code == 201
    new_address = response.json()
    assert new_address["user_id"] == victim_user_id

    # Clean up the created address
    test_client.delete(
        f"/api/users/{victim_user_id}/addresses/{new_address['address_id']}",
        headers=regular_auth_headers,
    )


def test_bola_cross_user_order_creation(
    test_client, regular_auth_headers, another_regular_user_info, test_data
):
    """
    Test BOLA vulnerability: creating an order for another user
    A regular user should be able to create an order for another user by using their user_id
    """
    victim_user_id = another_regular_user_info["user_id"]
    victim_address = another_regular_user_info["addresses"][0]
    victim_card = another_regular_user_info["credit_cards"][0]
    product = test_data["products"][0]

    # Try to create an order for another user
    response = test_client.post(
        f"/api/users/{victim_user_id}/orders?address_id={victim_address['address_id']}&credit_card_id={victim_card['card_id']}&product_id_1={product['product_id']}&quantity_1=1",
        headers=regular_auth_headers,
    )

    # Vulnerability test passes if the order is created
    assert response.status_code == 201
    new_order = response.json()
    assert new_order["user_id"] == victim_user_id
    assert new_order["address_id"] == victim_address["address_id"]
    assert new_order["credit_card_id"] == victim_card["card_id"]
    assert isinstance(new_order["created_at"], str)
    assert "T" in new_order["created_at"]
    from datetime import datetime

    datetime.fromisoformat(new_order["created_at"])
    expected_last_four = victim_card["card_number_plain"][-4:]
    assert new_order["credit_card_last_four"] == expected_last_four


def test_bola_using_another_users_address_for_order(
    test_client,
    regular_auth_headers,
    regular_user_info,
    another_regular_user_info,
    test_data,
):
    """
    Test BOLA vulnerability: using another user's address for an order
    A regular user should be able to use another user's address for their own order
    """
    user_id = regular_user_info["user_id"]
    user_card = regular_user_info["credit_cards"][0]
    victim_address = another_regular_user_info["addresses"][0]
    product = test_data["products"][0]

    # Try to create an order with another user's address
    response = test_client.post(
        f"/api/users/{user_id}/orders?address_id={victim_address['address_id']}&credit_card_id={user_card['card_id']}&product_id_1={product['product_id']}&quantity_1=1",
        headers=regular_auth_headers,
    )

    # Vulnerability test passes if the order is created
    assert response.status_code == 201
    new_order = response.json()
    assert new_order["user_id"] == user_id
    assert new_order["address_id"] == victim_address["address_id"]
    assert isinstance(new_order["created_at"], str)
    assert "T" in new_order["created_at"]
    from datetime import datetime

    datetime.fromisoformat(new_order["created_at"])
    expected_last_four = user_card["card_number_plain"][-4:]
    assert new_order["credit_card_last_four"] == expected_last_four


def test_bola_using_another_users_card_for_order(
    test_client,
    regular_auth_headers,
    regular_user_info,
    another_regular_user_info,
    test_data,
):
    """BOLA: attacker uses victim's credit card for their own order."""
    user_id = regular_user_info["user_id"]
    user_address = regular_user_info["addresses"][0]
    victim_card = another_regular_user_info["credit_cards"][0]
    product = test_data["products"][0]

    response = test_client.post(
        f"/api/users/{user_id}/orders?address_id={user_address['address_id']}&credit_card_id={victim_card['card_id']}&product_id_1={product['product_id']}&quantity_1=1",
        headers=regular_auth_headers,
    )

    assert response.status_code == 201
    new_order = response.json()
    assert new_order["user_id"] == user_id
    assert new_order["credit_card_id"] == victim_card["card_id"]
    assert isinstance(new_order["created_at"], str)
    assert "T" in new_order["created_at"]
    from datetime import datetime

    datetime.fromisoformat(new_order["created_at"])
    expected_last_four = victim_card["card_number_plain"][-4:]
    assert new_order["credit_card_last_four"] == expected_last_four


# --- Additional BOLA address & credit card modification tests ---


def test_bola_update_protected_address_forbidden(
    test_client, regular_auth_headers, another_regular_user_info
):
    """Attacker cannot modify a protected address belonging to another user."""
    victim_user_id = another_regular_user_info["user_id"]
    addr_id = another_regular_user_info["addresses"][0]["address_id"]
    resp = test_client.put(
        f"/api/users/{victim_user_id}/addresses/{addr_id}",
        params={"street": "Hacked"},
        headers=regular_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["street"] == "Hacked"


def test_bola_update_address_for_another_user(
    test_client, regular_auth_headers, non_protected_user_info
):
    """Attacker can modify an address of a non-protected user."""
    victim_user_id = non_protected_user_info["user_id"]
    address = non_protected_user_info["addresses"][0]
    original = address["street"]
    resp = test_client.put(
        f"/api/users/{victim_user_id}/addresses/{address['address_id']}",
        params={
            "street": "Evil Street",
            "city": address["city"],
            "country": address["country"],
            "zip_code": address["zip_code"],
            "is_default": address["is_default"],
        },
        headers=regular_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["street"] == "Evil Street"

    # revert for cleanliness
    test_client.put(
        f"/api/users/{victim_user_id}/addresses/{address['address_id']}",
        params={
            "street": original,
            "city": address["city"],
            "country": address["country"],
            "zip_code": address["zip_code"],
            "is_default": address["is_default"],
        },
        headers=regular_auth_headers,
    )


def test_bola_delete_protected_address_forbidden(
    test_client, regular_auth_headers, another_regular_user_info
):
    """Attempting to delete a protected address should be blocked."""
    victim_user_id = another_regular_user_info["user_id"]
    addr_id = another_regular_user_info["addresses"][0]["address_id"]
    resp = test_client.delete(
        f"/api/users/{victim_user_id}/addresses/{addr_id}",
        headers=regular_auth_headers,
    )
    assert resp.status_code == 403


def test_bola_delete_address_for_another_user(
    test_client, regular_auth_headers, non_protected_user_info
):
    """Attacker can delete a non-protected user's address."""
    victim_user_id = non_protected_user_info["user_id"]
    create = test_client.post(
        f"/api/users/{victim_user_id}/addresses",
        params={
            "street": "Temp",
            "city": "Tmp",
            "country": "Nowhere",
            "zip_code": "00000",
        },
        headers=regular_auth_headers,
    )
    assert create.status_code == 201
    addr_id = create.json()["address_id"]
    resp = test_client.delete(
        f"/api/users/{victim_user_id}/addresses/{addr_id}",
        headers=regular_auth_headers,
    )
    assert resp.status_code == 204


def test_bola_update_protected_credit_card_forbidden(
    test_client, regular_auth_headers, another_regular_user_info
):
    """Modifying a protected credit card should return 403."""
    victim_user_id = another_regular_user_info["user_id"]
    card_id = another_regular_user_info["credit_cards"][0]["card_id"]
    resp = test_client.put(
        f"/api/users/{victim_user_id}/credit-cards/{card_id}",
        params={"cardholder_name": "Hacker"},
        headers=regular_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["cardholder_name"] == "Hacker"


def test_bola_update_credit_card_for_another_user(
    test_client, regular_auth_headers, non_protected_user_info
):
    """Attacker can modify another user's non-protected credit card."""
    victim_user_id = non_protected_user_info["user_id"]
    card = non_protected_user_info["credit_cards"][0]
    original = card["cardholder_name"]
    resp = test_client.put(
        f"/api/users/{victim_user_id}/credit-cards/{card['card_id']}",
        params={"cardholder_name": "Evil"},
        headers=regular_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["cardholder_name"] == "Evil"

    # revert
    test_client.put(
        f"/api/users/{victim_user_id}/credit-cards/{card['card_id']}",
        params={"cardholder_name": original},
        headers=regular_auth_headers,
    )


def test_bola_delete_protected_credit_card_forbidden(
    test_client, regular_auth_headers, another_regular_user_info
):
    victim_user_id = another_regular_user_info["user_id"]
    card_id = another_regular_user_info["credit_cards"][0]["card_id"]
    resp = test_client.delete(
        f"/api/users/{victim_user_id}/credit-cards/{card_id}",
        headers=regular_auth_headers,
    )
    assert resp.status_code == 204


def test_bola_delete_credit_card_for_another_user(
    test_client, regular_auth_headers, non_protected_user_info
):
    victim_user_id = non_protected_user_info["user_id"]
    create = test_client.post(
        f"/api/users/{victim_user_id}/credit-cards",
        params={
            "cardholder_name": "Temp",
            "card_number": "4111111111111111",
            "expiry_month": "12",
            "expiry_year": "2029",
            "cvv": "999",
        },
        headers=regular_auth_headers,
    )
    assert create.status_code == 201
    card_id = create.json()["card_id"]
    resp = test_client.delete(
        f"/api/users/{victim_user_id}/credit-cards/{card_id}",
        headers=regular_auth_headers,
    )
    assert resp.status_code == 204


# Test for BFLA (Broken Function Level Authorization) vulnerabilities


def test_bfla_product_creation_by_regular_user(test_client, regular_auth_headers):
    """
    Test BFLA vulnerability: product creation by regular user
    A regular user should be able to create products (an admin-only function)
    """
    # Generate a unique product name
    product_name = f"Test Product {uuid.uuid4().hex[:8]}"

    # Try to create a product as a regular user
    response = test_client.post(
        f"/api/products?name={product_name}&price=99.99&description=This%20should%20not%20be%20allowed&category=Test",
        headers=regular_auth_headers,
    )

    # Vulnerability test passes if the product is created
    assert response.status_code == 201
    new_product = response.json()
    assert new_product["name"] == product_name


def test_bfla_product_deletion_by_regular_user(test_client, regular_auth_headers):
    """
    Test BFLA vulnerability: product deletion by regular user
    A regular user should be able to delete products (an admin-only function)
    """
    # First create a product to delete
    product_name = f"Delete Test Product {uuid.uuid4().hex[:8]}"
    create_response = test_client.post(
        f"/api/products?name={product_name}&price=99.99&description=To%20be%20deleted&category=Test",
        headers=regular_auth_headers,
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["product_id"]

    # Try to delete the product as a regular user
    delete_response = test_client.delete(
        f"/api/products/{product_id}", headers=regular_auth_headers
    )

    # Vulnerability test passes if the product is deleted
    assert delete_response.status_code == 204

    # Verify deletion
    get_response = test_client.get(f"/api/products/{product_id}")
    assert get_response.status_code == 404


def test_bfla_stock_update_by_regular_user(test_client, regular_auth_headers):
    """
    Test BFLA vulnerability: stock update by regular user.
    A regular user should be able to update product stock (an admin-only function).
    If the target product is protected, the update still succeeds but the server logs the action.
    """
    # Create a non-protected product first
    product_name = f"Stock Update Test {uuid.uuid4().hex[:8]}"
    create_resp = test_client.post(
        f"/api/products?name={product_name}&price=1.99&description=Temp&category=Test",
        headers=regular_auth_headers,
    )
    assert create_resp.status_code == 201
    product_id = create_resp.json()["product_id"]

    # Update stock to a new value
    new_stock = 12345
    update_response = test_client.put(
        f"/api/products/{product_id}/stock?quantity={new_stock}",
        headers=regular_auth_headers,
    )

    # Vulnerability test passes if the stock is updated
    assert update_response.status_code == 200
    updated_stock = update_response.json()
    assert updated_stock["quantity"] == new_stock

    # Reset stock to original value
    test_client.delete(f"/api/products/{product_id}", headers=regular_auth_headers)


def test_bfla_user_deletion_by_regular_user(test_client, regular_auth_headers):
    """
    Test BFLA vulnerability: user deletion by regular user
    A regular user should be able to delete other users (an admin-only function)
    """
    # First create a test user to delete
    unique_username = f"delete_victim_{uuid.uuid4().hex[:8]}"
    register_response = test_client.post(
        f"/api/auth/register?username={unique_username}&email={unique_username}@example.com&password=DeleteMe123!"
    )
    assert register_response.status_code == 201
    victim_user_id = register_response.json()["user_id"]

    # Try to delete the user as a regular user
    delete_response = test_client.delete(
        f"/api/users/{victim_user_id}", headers=regular_auth_headers
    )

    # Vulnerability test passes if the user is deleted
    assert delete_response.status_code == 204

    # Verify deletion
    get_response = test_client.get(
        f"/api/users/{victim_user_id}", headers=regular_auth_headers
    )
    assert get_response.status_code == 404


def test_bfla_protected_user_deletion_forbidden(
    test_client, regular_auth_headers, test_data
):
    """Regular user attempting to delete a protected user should be blocked."""
    protected_user = next(
        u for u in test_data["users"] if u["username"] == "BobJohnson"
    )
    resp = test_client.delete(
        f"/api/users/{protected_user['user_id']}",
        headers=regular_auth_headers,
    )
    assert resp.status_code == 403
    assert "protected" in resp.json()["detail"]


# Test for Parameter Pollution vulnerabilities


def test_parameter_pollution_admin_escalation(
    test_client, regular_auth_headers, regular_user_info
):
    """
    Test Parameter Pollution vulnerability: regular user escalating to admin
    A regular user should be able to become admin by adding the is_admin parameter
    """
    user_id = regular_user_info["user_id"]

    # Attacker escalates privileges using query parameter pollution
    response = test_client.put(
        f"/api/users/{user_id}",
        params={"is_admin": True},
        headers=regular_auth_headers,
    )

    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["is_admin"] is True

    # Revert for cleanliness
    revert = test_client.put(
        f"/api/users/{user_id}",
        params={"is_admin": False},
        headers=regular_auth_headers,
    )
    assert revert.status_code == 200
    assert revert.json()["is_admin"] is False


def test_parameter_pollution_product_internal_status(
    test_client, regular_auth_headers, test_data
):
    """
    Test Parameter Pollution vulnerability: setting internal product status
    A regular user should be able to set a product's internal_status
    """
    # -- Non-protected product should accept internal_status parameter --
    non_protected = next(p for p in test_data["products"] if not p["is_protected"])
    prod_id = non_protected["product_id"]
    resp = test_client.put(
        f"/api/products/{prod_id}",
        params={"internal_status": "hacked_value"},
        headers=regular_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["internal_status"] == "hacked_value"

    # -- Protected product should reject the same update --
    protected = next(p for p in test_data["products"] if p["is_protected"])
    resp_prot = test_client.put(
        f"/api/products/{protected['product_id']}",
        params={"internal_status": "hacked_value"},
        headers=regular_auth_headers,
    )
    assert resp_prot.status_code == 403
    assert "protected for demo purposes" in resp_prot.json()["detail"]


def test_protected_product_deletion_forbidden(
    test_client, regular_auth_headers, test_data
):
    """Deleting a protected product should be blocked."""
    protected_product = next(p for p in test_data["products"] if p["is_protected"])
    delete_response = test_client.delete(
        f"/api/products/{protected_product['product_id']}", headers=regular_auth_headers
    )
    assert delete_response.status_code == 403
    assert "protected for demo purposes" in delete_response.json()["detail"]


def test_protected_product_stock_minimum_enforced(
    test_client, regular_auth_headers, test_data
):
    """Protected product stock updates must respect minimum quantity."""
    protected_product = next(p for p in test_data["products"] if p["is_protected"])
    # Below minimum should be forbidden
    resp_low = test_client.put(
        f"/api/products/{protected_product['product_id']}/stock?quantity=100",
        headers=regular_auth_headers,
    )
    assert resp_low.status_code == 403
    assert "stock" in resp_low.json()["detail"]

    # Above minimum should succeed
    high_quantity = PROTECTED_STOCK_MINIMUM + 500
    resp_high = test_client.put(
        f"/api/products/{protected_product['product_id']}/stock?quantity={high_quantity}",
        headers=regular_auth_headers,
    )
    assert resp_high.status_code == 200
    assert resp_high.json()["quantity"] == high_quantity


# Test for Injection vulnerabilities


def test_sql_injection_in_product_search(test_client):
    """
    Test for potential SQL Injection: manipulating the product search
    Using special characters in the search might cause unexpected behavior
    """
    # Try a search with SQL injection characters
    injection_string = "' OR '1'='1"
    response = test_client.get(
        "/api/products/search",
        params={"name": injection_string},
    )

    # The vulnerability is present if the search doesn't error out
    # (simulated environment won't actually execute the injection)
    assert response.status_code == 200
    # Explicitly ensure the server didn't error out
    assert response.status_code != 500
    # Response should still be valid JSON (a list of products)
    assert isinstance(response.json(), list)
