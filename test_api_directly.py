import requests
import uuid
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

def log_step(step_description):
    """Log a step with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {step_description}")

def make_request(method, endpoint, params=None, headers=None, expected_status=None):
    """Make a request to the API and handle errors."""
    url = f"{BASE_URL}{endpoint}"
    
    response = None
    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, params=params, headers=headers)
        elif method == "PUT":
            response = requests.put(url, params=params, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, params=params, headers=headers)
        
        status = "✅" if (expected_status is None or response.status_code == expected_status) else "❌"
        print(f"{status} {method} {url} - Status: {response.status_code}")
        
        if response.status_code >= 400:
            print(f"Error response: {response.text}")
        
        return response
    except Exception as e:
        print(f"❌ Error with {method} {url}: {str(e)}")
        return None

def test_server_running():
    """Test if the server is running."""
    log_step("Testing if server is running")
    response = make_request("GET", "/", expected_status=200)
    return response is not None and response.status_code == 200

def test_functional_endpoints():
    """Test core functional endpoints."""
    log_step("Testing functional endpoints")
    
    # Generate unique user credentials
    username = f"test_user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "TestPass123!"
    
    # Test user registration
    register_response = make_request(
        "POST", 
        f"/auth/register?username={username}&email={email}&password={password}",
        expected_status=201
    )
    if not register_response or register_response.status_code != 201:
        print("❌ Registration failed")
        return False
    
    user_id = register_response.json().get("user_id")
    print(f"📌 Created user with ID: {user_id}")
    
    # Test user login
    login_response = make_request(
        "POST",
        f"/auth/login?username={username}&password={password}",
        expected_status=200
    )
    if not login_response or login_response.status_code != 200:
        print("❌ Login failed")
        return False
    
    token = login_response.json().get("access_token")
    auth_headers = {"Authorization": f"Bearer {token}"}
    print(f"📌 Login successful, got token")
    
    # Test retrieving user profile
    make_request("GET", f"/users/{user_id}", headers=auth_headers, expected_status=200)
    
    # Test listing products
    products_response = make_request("GET", "/products", expected_status=200)
    if products_response and products_response.status_code == 200:
        products = products_response.json()
        print(f"📌 Retrieved {len(products)} products")
    
    # Test product search
    make_request("GET", "/products/search/?name=laptop", expected_status=200)
    
    # Create address for user
    address_response = make_request(
        "POST",
        f"/users/{user_id}/addresses?street=Test%20Street&city=Test%20City&country=Test%20Country&zip_code=12345&is_default=false",
        headers=auth_headers,
        expected_status=201
    )
    if address_response and address_response.status_code == 201:
        address_id = address_response.json().get("address_id")
        print(f"📌 Created address with ID: {address_id}")
    
    # Create credit card for user
    card_response = make_request(
        "POST",
        f"/users/{user_id}/credit-cards?cardholder_name=Test%20User&card_number=4111111111111111&expiry_month=12&expiry_year=2028&cvv=123&is_default=false",
        headers=auth_headers,
        expected_status=201
    )
    if card_response and card_response.status_code == 201:
        card_id = card_response.json().get("card_id")
        print(f"📌 Created credit card with ID: {card_id}")
    
    return True

def test_vulnerabilities():
    """Test some key vulnerabilities."""
    log_step("Testing vulnerability endpoints")
    
    # Create two users for testing BOLA
    user1_username = f"user1_{uuid.uuid4().hex[:8]}"
    user1_email = f"{user1_username}@example.com"
    user1_password = "User1Pass123!"
    
    user2_username = f"user2_{uuid.uuid4().hex[:8]}"
    user2_email = f"{user2_username}@example.com"
    user2_password = "User2Pass123!"
    
    # Register users
    user1_reg = make_request(
        "POST", 
        f"/auth/register?username={user1_username}&email={user1_email}&password={user1_password}",
        expected_status=201
    )
    user2_reg = make_request(
        "POST", 
        f"/auth/register?username={user2_username}&email={user2_email}&password={user2_password}",
        expected_status=201
    )
    
    if not user1_reg or not user2_reg:
        print("❌ Failed to create test users for vulnerability testing")
        return False
    
    user1_id = user1_reg.json().get("user_id")
    user2_id = user2_reg.json().get("user_id")
    
    # Login users
    user1_login = make_request(
        "POST",
        f"/auth/login?username={user1_username}&password={user1_password}",
        expected_status=200
    )
    user1_token = user1_login.json().get("access_token")
    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    
    # Test BOLA - User 1 accessing User 2's profile
    bola_test = make_request("GET", f"/users/{user2_id}", headers=user1_headers, expected_status=200)
    if bola_test and bola_test.status_code == 200:
        print("✅ BOLA vulnerability confirmed: User 1 can access User 2's profile")
    else:
        print("❌ BOLA test failed - could not access other user's profile")
    
    # Test BFLA - Regular user creating a product (admin function)
    product_name = f"Test Product {uuid.uuid4().hex[:8]}"
    bfla_test = make_request(
        "POST",
        f"/products?name={product_name}&price=99.99&description=Test%20Product&category=Test",
        headers=user1_headers,
        expected_status=201
    )
    if bfla_test and bfla_test.status_code == 201:
        print("✅ BFLA vulnerability confirmed: Regular user can create products (admin function)")
    else:
        print("❌ BFLA test failed - could not create product as regular user")
    
    # Test Parameter Pollution - Set is_admin flag
    param_poll_test = make_request(
        "PUT",
        f"/users/{user1_id}?email={user1_email}&is_admin=true",
        headers=user1_headers,
        expected_status=200
    )
    if param_poll_test and param_poll_test.status_code == 200:
        user_data = param_poll_test.json()
        if user_data.get("is_admin") == True:
            print("✅ Parameter Pollution vulnerability confirmed: User could set is_admin=true")
        else:
            print("❌ Parameter Pollution test failed - is_admin not set to true")
    else:
        print("❌ Parameter Pollution test failed")
    
    return True

def main():
    """Main test function."""
    print("\n" + "="*50)
    print("RADWARE VULNERABLE API DIRECT TEST")
    print("="*50 + "\n")
    
    # Test if server is running
    if not test_server_running():
        print("❌ Server is not running. Tests cannot proceed.")
        return
    
    # Run functional tests
    print("\n" + "-"*50)
    print("FUNCTIONAL TESTS")
    print("-"*50)
    test_functional_endpoints()
    
    # Run vulnerability tests
    print("\n" + "-"*50)
    print("VULNERABILITY TESTS")
    print("-"*50)
    test_vulnerabilities()
    
    print("\n" + "="*50)
    print("TEST COMPLETED")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
