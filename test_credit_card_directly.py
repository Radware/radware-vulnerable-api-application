import httpx
import json
from uuid import UUID
import pytest

def run_single_test():
    """Run just the credit card test to see if it's fixed."""
    BASE_URL = "http://localhost:8000"
    
    # Login with test user to get token
    login_resp = httpx.post(
        f"{BASE_URL}/api/auth/login",
        params={"username": "AliceSmith", "password": "Password123"}
    )
    
    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.status_code} - {login_resp.text}")
        return False
        
    token_data = login_resp.json()
    token = token_data["access_token"]
    
    # Get user info
    auth_headers = {"Authorization": f"Bearer {token}"}
    user_id = "00000002-0000-0000-0000-000000000002"  # Alice's ID from test data
    
    # List initial cards
    list_resp = httpx.get(
        f"{BASE_URL}/api/users/{user_id}/credit-cards",
        headers=auth_headers
    )
    
    if list_resp.status_code != 200:
        print(f"List cards failed: {list_resp.status_code} - {list_resp.text}")
        return False
        
    initial_cards = list_resp.json()
    
    # Create new card using params dict
    create_resp = httpx.post(
        f"{BASE_URL}/api/users/{user_id}/credit-cards",
        params={
            "cardholder_name": "Test User",
            "card_number": "4111111111111111",
            "expiry_month": "12",
            "expiry_year": "2029",
            "cvv": "123",
            "is_default": "false"
        },
        headers=auth_headers
    )
    
    print(f"Create card status: {create_resp.status_code}")
    print(f"Create card response: {create_resp.text}")
    
    if create_resp.status_code != 201:
        return False
    
    new_card = create_resp.json()
    
    # Check card was created
    list_after_resp = httpx.get(
        f"{BASE_URL}/api/users/{user_id}/credit-cards",
        headers=auth_headers
    )
    
    after_cards = list_after_resp.json()
    print(f"Initial count: {len(initial_cards)}, After count: {len(after_cards)}")
    
    # Clean up - delete the card
    if "card_id" in new_card:
        delete_resp = httpx.delete(
            f"{BASE_URL}/api/users/{user_id}/credit-cards/{new_card['card_id']}",
            headers=auth_headers
        )
        print(f"Delete status: {delete_resp.status_code}")
    
    return True

if __name__ == "__main__":
    success = run_single_test()
    print(f"Test {'passed' if success else 'failed'}")
    exit(0 if success else 1)
