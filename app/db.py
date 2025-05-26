from typing import Dict, List, Any
from uuid import UUID, uuid4
import json
import os
from .models.user_models import UserInDBBase, AddressInDBBase, CreditCardInDBBase
from .models.product_models import ProductInDBBase, StockInDBBase
from .models.order_models import OrderInDBBase, OrderItemInDBBase
from .security import get_password_hash
import random

# In-memory "database"
# We use lists to store items, acting like tables. For simplicity.
db: Dict[str, List[Any]] = {
    "users": [],
    "addresses": [],
    "credit_cards": [],
    "products": [],
    "stock": [], # Stock will be closely tied to products; could be a field in product or separate
    "orders": [],
    "order_items": []
}

# Helper functions to simulate DB operations could be added here later if needed,
# e.g., find_user_by_username, find_product_by_id, etc.

def initialize_database_from_json():
    """Initializes the in-memory database from a predefined JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    json_file_path = os.path.join(root_dir, "prepopulated_data.json")

    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file_path} not found. Cannot initialize database.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}. Cannot initialize database.")
        return

    # Clear existing data
    for key in db:
        db[key].clear()

    # Load products and stock
    for product_data in data.get("products", []):
        product_id = UUID(product_data["product_id"])
        db["products"].append(
            ProductInDBBase(
                product_id=product_id,
                name=product_data["name"],
                description=product_data["description"],
                price=product_data["price"],
                category=product_data["category"],
                is_protected=product_data.get("is_protected", False),
            )
        )
        db["stock"].append(StockInDBBase(
            product_id=product_id,
            quantity=product_data["stock_quantity"]
        ))

    # Load users, addresses, and credit cards
    for user_data in data.get("users", []):
        user_id = UUID(user_data["user_id"])
        hashed_password = get_password_hash(user_data["password_plain"])
        db["users"].append(
            UserInDBBase(
                user_id=user_id,
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hashed_password,
                is_admin=user_data["is_admin"],
                is_protected=user_data.get("is_protected", False),
            )
        )

        for addr_data in user_data.get("addresses", []):
            db["addresses"].append(
                AddressInDBBase(
                    address_id=UUID(addr_data["address_id"]),
                    user_id=user_id,  # Link to the current user
                    street=addr_data["street"],
                    city=addr_data["city"],
                    country=addr_data["country"],
                    zip_code=addr_data["zip_code"],
                    is_default=addr_data["is_default"],
                    is_protected=addr_data.get("is_protected", False),
                )
            )

        for card_data in user_data.get("credit_cards", []):
            # Extract last four digits of the card number
            card_last_four = card_data["card_number_plain"][-4:]

            db["credit_cards"].append(
                CreditCardInDBBase(
                    card_id=UUID(card_data["card_id"]),
                    user_id=user_id,  # Link to the current user
                    cardholder_name=card_data["cardholder_name"],
                    expiry_month=card_data["expiry_month"],
                    expiry_year=card_data["expiry_year"],
                    card_number_hash=get_password_hash(card_data["card_number_plain"]),
                    card_last_four=card_last_four,
                    cvv_hash=get_password_hash(card_data["cvv_plain"]),
                    is_default=card_data["is_default"],
                    is_protected=card_data.get("is_protected", False),
                )
            )
    print(f"Database initialized from {json_file_path}")


# Initialize DB from JSON when the module is loaded
initialize_database_from_json()
