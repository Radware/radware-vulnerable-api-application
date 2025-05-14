#!/usr/bin/env python3
"""
Traffic Generator for Radware Vulnerable API

This script generates legitimate API traffic to test the stability of the API.
It simulates user actions like login, registration, product browsing, order creation,
and address/card management.

Usage:
    python traffic_generator.py [--rps REQUESTS_PER_SECOND] [--duration DURATION_IN_SECONDS]
"""

import argparse
import json
import random
import time
import uuid
import sys
import requests
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_ENDPOINTS = {
    "register": "/auth/register",
    "login": "/auth/login",
    "products": "/products",
    "product_search": "/products/search/",
    "users": "/users",
    # Additional endpoint patterns for authenticated requests
    "user_profile": "/users/{user_id}",
    "user_addresses": "/users/{user_id}/addresses",
    "user_creditcards": "/users/{user_id}/credit-cards",
    "user_orders": "/users/{user_id}/orders"
}

# Track active sessions
active_users = []

class User:
    def __init__(self, username, password, user_id=None, token=None):
        self.username = username
        self.password = password
        self.user_id = user_id
        self.token = token
        self.addresses = []
        self.credit_cards = []
        self.orders = []

    def get_auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

def load_test_data():
    """Load test data from prepopulated_data.json."""
    try:
        project_root = Path(__file__).parent
        json_file_path = project_root / "prepopulated_data.json"
        
        with open(json_file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading test data: {e}")
        return {"users": [], "products": []}

def log_event(message, is_error=False):
    """Log an event with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_type = "ERROR" if is_error else "INFO"
    print(f"[{timestamp}] [{log_type}] {message}")

def make_request(method, endpoint, params=None, headers=None, is_authenticated=False):
    """Make a request to the API and handle errors."""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = None
        if method == "GET":
            response = requests.get(url, params=params, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, params=params, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, params=params, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, params=params, headers=headers, timeout=10)
        
        if response and response.status_code >= 400:
            log_event(f"Request failed: {method} {url} - Status Code: {response.status_code} - Response: {response.text}", True)
        else:
            log_event(f"Request successful: {method} {url} - Status Code: {response.status_code}")
        
        return response
    except Exception as e:
        log_event(f"Request error: {method} {url} - {str(e)}", True)
        return None

def register_new_user():
    """Register a new user and return a User object."""
    unique_id = uuid.uuid4().hex[:8]
    username = f"traffic_user_{unique_id}"
    password = f"Traffic123!{unique_id}"
    email = f"{username}@example.com"
    
    params = {
        "username": username,
        "email": email,
        "password": password
    }
    
    response = make_request("POST", API_ENDPOINTS["register"], params=params)
    if response and response.status_code == 201:
        user_data = response.json()
        user = User(username, password, user_id=user_data.get("user_id"))
        log_event(f"Registered new user: {username}")
        return user
    return None

def login_user(user):
    """Log in a user and update their token."""
    params = {
        "username": user.username,
        "password": user.password
    }
    
    response = make_request("POST", API_ENDPOINTS["login"], params=params)
    if response and response.status_code == 200:
        token_data = response.json()
        user.token = token_data.get("access_token")
        log_event(f"Logged in user: {user.username}")
        return True
    return False

def browse_products(user=None):
    """Browse products, optionally as an authenticated user."""
    headers = user.get_auth_headers() if user else None
    
    response = make_request("GET", API_ENDPOINTS["products"], headers=headers)
    if response and response.status_code == 200:
        return response.json()
    return []

def search_products(search_term, user=None):
    """Search for products, optionally as an authenticated user."""
    headers = user.get_auth_headers() if user else None
    params = {"name": search_term}
    
    response = make_request("GET", API_ENDPOINTS["product_search"], params=params, headers=headers)
    if response and response.status_code == 200:
        return response.json()
    return []

def manage_addresses(user):
    """Create, list, and manage user addresses."""
    if not user or not user.token or not user.user_id:
        return False
    
    # List addresses
    endpoint = API_ENDPOINTS["user_addresses"].format(user_id=user.user_id)
    response = make_request("GET", endpoint, headers=user.get_auth_headers())
    
    if response and response.status_code == 200:
        user.addresses = response.json()
    
    # Create a new address if user has fewer than 3
    if len(user.addresses) < 3:
        street = f"Traffic Street {uuid.uuid4().hex[:6]}"
        city = random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"])
        country = "USA"
        zip_code = f"{random.randint(10000, 99999)}"
        
        params = {
            "street": street,
            "city": city,
            "country": country,
            "zip_code": zip_code,
            "is_default": False
        }
        
        create_response = make_request("POST", endpoint, params=params, headers=user.get_auth_headers())
        if create_response and create_response.status_code == 201:
            new_address = create_response.json()
            user.addresses.append(new_address)
            log_event(f"Created new address for user {user.username}")
    
    return True

def manage_credit_cards(user):
    """Create and list user credit cards."""
    if not user or not user.token or not user.user_id:
        return False
    
    # List credit cards
    endpoint = API_ENDPOINTS["user_creditcards"].format(user_id=user.user_id)
    response = make_request("GET", endpoint, headers=user.get_auth_headers())
    
    if response and response.status_code == 200:
        user.credit_cards = response.json()
    
    # Create a new credit card if user has fewer than 2
    if len(user.credit_cards) < 2:
        cardholder_name = f"{user.username.title()}"
        card_number = "4" + "".join([str(random.randint(0, 9)) for _ in range(15)])
        expiry_month = f"{random.randint(1, 12):02d}"
        expiry_year = str(random.randint(2026, 2030))
        cvv = f"{random.randint(100, 999)}"
        
        params = {
            "cardholder_name": cardholder_name,
            "card_number": card_number,
            "expiry_month": expiry_month,
            "expiry_year": expiry_year,
            "cvv": cvv,
            "is_default": False
        }
        
        create_response = make_request("POST", endpoint, params=params, headers=user.get_auth_headers())
        if create_response and create_response.status_code == 201:
            new_card = create_response.json()
            user.credit_cards.append(new_card)
            log_event(f"Created new credit card for user {user.username}")
    
    return True

def create_order(user, products):
    """Create an order for a user."""
    if not user or not user.token or not user.user_id or not user.addresses or not user.credit_cards:
        return False
    
    # Get a random product
    if not products:
        return False
    product = random.choice(products)
    
    # Select a random address and credit card
    address = random.choice(user.addresses)
    credit_card = random.choice(user.credit_cards)
    
    # Create order parameters
    endpoint = API_ENDPOINTS["user_orders"].format(user_id=user.user_id)
    params = {
        "address_id": address["address_id"],
        "credit_card_id": credit_card["card_id"],
        "product_id_1": product["product_id"],
        "quantity_1": random.randint(1, 3)
    }
    
    # Add a second product occasionally
    if len(products) > 1 and random.random() < 0.3:
        second_product = random.choice([p for p in products if p["product_id"] != product["product_id"]])
        params["product_id_2"] = second_product["product_id"]
        params["quantity_2"] = random.randint(1, 2)
    
    response = make_request("POST", endpoint, params=params, headers=user.get_auth_headers())
    if response and response.status_code == 201:
        new_order = response.json()
        user.orders.append(new_order)
        log_event(f"Created new order for user {user.username}")
        return True
    
    return False

def view_user_orders(user):
    """View a user's orders."""
    if not user or not user.token or not user.user_id:
        return False
    
    endpoint = API_ENDPOINTS["user_orders"].format(user_id=user.user_id)
    response = make_request("GET", endpoint, headers=user.get_auth_headers())
    
    if response and response.status_code == 200:
        orders = response.json()
        user.orders = orders
        log_event(f"Retrieved {len(orders)} orders for user {user.username}")
        
        # View a specific order if available
        if orders and random.random() < 0.5:
            order = random.choice(orders)
            order_endpoint = f"{endpoint}/{order['order_id']}"
            make_request("GET", order_endpoint, headers=user.get_auth_headers())
        
        return True
    
    return False

def generate_traffic(rps, duration):
    """Generate traffic to the API at the specified rate for the specified duration."""
    log_event(f"Starting traffic generation: {rps} requests per second for {duration} seconds")
    
    # Load test data
    test_data = load_test_data()
    products = test_data.get("products", [])
    
    # Pre-register some users
    for _ in range(5):
        user = register_new_user()
        if user and login_user(user):
            active_users.append(user)
            # Set up user profile
            manage_addresses(user)
            manage_credit_cards(user)
    
    start_time = time.time()
    request_count = 0
    
    # Generate traffic for the specified duration
    while time.time() - start_time < duration:
        # Determine the type of request to make
        request_type = random.choices(
            ["browse", "search", "register", "login", "profile", "address", "card", "order", "view_orders"],
            weights=[0.2, 0.15, 0.05, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
            k=1
        )[0]
        
        if request_type == "browse":
            # Anonymous browsing
            browse_products()
        
        elif request_type == "search":
            # Product search with random terms
            search_terms = ["laptop", "phone", "headphone", "mouse", "keyboard", "monitor", "speaker"]
            search_products(random.choice(search_terms))
        
        elif request_type == "register":
            # Register a new user
            user = register_new_user()
            if user:
                login_user(user)
                active_users.append(user)
        
        elif request_type == "login":
            # Log in an existing user or create a new one if no users exist
            if active_users:
                user = random.choice(active_users)
                login_user(user)
            else:
                user = register_new_user()
                if user:
                    login_user(user)
                    active_users.append(user)
        
        elif request_type == "profile" and active_users:
            # View/update user profile
            user = random.choice(active_users)
            endpoint = API_ENDPOINTS["user_profile"].format(user_id=user.user_id)
            make_request("GET", endpoint, headers=user.get_auth_headers())
        
        elif request_type == "address" and active_users:
            # Manage addresses
            user = random.choice(active_users)
            manage_addresses(user)
        
        elif request_type == "card" and active_users:
            # Manage credit cards
            user = random.choice(active_users)
            manage_credit_cards(user)
        
        elif request_type == "order" and active_users:
            # Create an order
            user = random.choice(active_users)
            # Ensure user has addresses and credit cards
            if not user.addresses:
                manage_addresses(user)
            if not user.credit_cards:
                manage_credit_cards(user)
            if user.addresses and user.credit_cards:
                create_order(user, products)
        
        elif request_type == "view_orders" and active_users:
            # View orders
            user = random.choice(active_users)
            view_user_orders(user)
        
        request_count += 1
        
        # Calculate sleep time to maintain the desired RPS
        elapsed = time.time() - start_time
        expected_requests = int(elapsed * rps)
        if request_count > expected_requests:
            time.sleep(1/rps)
    
    log_event(f"Traffic generation completed. Made {request_count} requests over {duration} seconds")

def main():
    parser = argparse.ArgumentParser(description="Generate traffic for the Radware Vulnerable API")
    parser.add_argument("--rps", type=float, default=3.0, help="Requests per second (default: 3.0)")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds (default: 60)")
    args = parser.parse_args()
    
    try:
        generate_traffic(args.rps, args.duration)
    except KeyboardInterrupt:
        log_event("Traffic generation interrupted by user")
    except Exception as e:
        log_event(f"Error in traffic generation: {str(e)}", True)

if __name__ == "__main__":
    main()
