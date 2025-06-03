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
    "stock": [],  # Stock will be closely tied to products; could be a field in product or separate
    "orders": [],
    "order_items": [],
}

# Dictionary-based indexes for quick lookups
db_users_by_id: Dict[UUID, UserInDBBase] = {}
db_users_by_username: Dict[str, UserInDBBase] = {}
db_users_by_email: Dict[str, UserInDBBase] = {}
db_addresses_by_id: Dict[UUID, AddressInDBBase] = {}
db_credit_cards_by_id: Dict[UUID, CreditCardInDBBase] = {}
db_products_by_id: Dict[UUID, ProductInDBBase] = {}
db_stock_by_product_id: Dict[UUID, StockInDBBase] = {}

# Helper functions to simulate DB operations could be added here later if needed,
# e.g., find_user_by_username, find_product_by_id, etc.


def initialize_database_from_json():
    """Initializes the in-memory database from a predefined JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    json_file_path = os.path.join(root_dir, "prepopulated_data.json")

    try:
        with open(json_file_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file_path} not found. Cannot initialize database.")
        return
    except json.JSONDecodeError:
        print(
            f"Error: Could not decode JSON from {json_file_path}. Cannot initialize database."
        )
        return

    # Clear existing data
    for key in db:
        db[key].clear()
    db_users_by_id.clear()
    db_users_by_username.clear()
    db_users_by_email.clear()
    db_addresses_by_id.clear()
    db_credit_cards_by_id.clear()
    db_products_by_id.clear()
    db_stock_by_product_id.clear()

    # Load products and stock
    for product_data in data.get("products", []):
        product_id = UUID(product_data["product_id"])
        product_obj = ProductInDBBase(
            product_id=product_id,
            name=product_data["name"],
            description=product_data["description"],
            price=product_data["price"],
            category=product_data["category"],
            is_protected=product_data.get("is_protected", False),
        )
        db["products"].append(product_obj)
        db_products_by_id[product_id] = product_obj

        stock_obj = StockInDBBase(
            product_id=product_id, quantity=product_data["stock_quantity"]
        )
        db["stock"].append(stock_obj)
        db_stock_by_product_id[product_id] = stock_obj

    # Load users, addresses, and credit cards
    for user_data in data.get("users", []):
        user_id = UUID(user_data["user_id"])
        hashed_password = get_password_hash(user_data["password_plain"])
        user_obj = UserInDBBase(
            user_id=user_id,
            username=user_data["username"],
            email=user_data["email"],
            password_hash=hashed_password,
            is_admin=user_data["is_admin"],
            is_protected=user_data.get("is_protected", False),
        )
        db["users"].append(user_obj)
        db_users_by_id[user_id] = user_obj
        db_users_by_username[user_obj.username] = user_obj
        db_users_by_email[user_obj.email] = user_obj

        for addr_data in user_data.get("addresses", []):
            addr_obj = AddressInDBBase(
                address_id=UUID(addr_data["address_id"]),
                user_id=user_id,
                street=addr_data["street"],
                city=addr_data["city"],
                country=addr_data["country"],
                zip_code=addr_data["zip_code"],
                is_default=addr_data["is_default"],
                is_protected=addr_data.get("is_protected", False),
            )
            db["addresses"].append(addr_obj)
            db_addresses_by_id[addr_obj.address_id] = addr_obj

        for card_data in user_data.get("credit_cards", []):
            card_last_four = card_data["card_number_plain"][-4:]

            card_obj = CreditCardInDBBase(
                card_id=UUID(card_data["card_id"]),
                user_id=user_id,
                cardholder_name=card_data["cardholder_name"],
                expiry_month=card_data["expiry_month"],
                expiry_year=card_data["expiry_year"],
                card_number_hash=get_password_hash(card_data["card_number_plain"]),
                card_last_four=card_last_four,
                cvv_hash=get_password_hash(card_data["cvv_plain"]),
                is_default=card_data["is_default"],
                is_protected=card_data.get("is_protected", False),
            )
            db["credit_cards"].append(card_obj)
            db_credit_cards_by_id[card_obj.card_id] = card_obj
    print(f"Database initialized from {json_file_path}")


# Initialize DB from JSON when the module is loaded
initialize_database_from_json()
