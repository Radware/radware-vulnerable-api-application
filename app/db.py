from typing import Dict, List, Any
from uuid import UUID, uuid4
import json
import os
from datetime import datetime, timezone
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
db_addresses_by_user_id: Dict[UUID, List[AddressInDBBase]] = {}
db_credit_cards_by_id: Dict[UUID, CreditCardInDBBase] = {}
db_credit_cards_by_user_id: Dict[UUID, List[CreditCardInDBBase]] = {}
db_products_by_id: Dict[UUID, ProductInDBBase] = {}
db_stock_by_product_id: Dict[UUID, StockInDBBase] = {}
db_orders_by_id: Dict[UUID, OrderInDBBase] = {}
db_orders_by_user_id: Dict[UUID, List[OrderInDBBase]] = {}
db_order_items_by_id: Dict[UUID, OrderItemInDBBase] = {}
db_order_items_by_order_id: Dict[UUID, List[OrderItemInDBBase]] = {}

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
    db_addresses_by_user_id.clear()
    db_credit_cards_by_id.clear()
    db_credit_cards_by_user_id.clear()
    db_products_by_id.clear()
    db_stock_by_product_id.clear()
    db_orders_by_id.clear()
    db_orders_by_user_id.clear()
    db_order_items_by_id.clear()
    db_order_items_by_order_id.clear()

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
        db["products"].append(product_obj) # Keep populating the old list for now, if any code still uses it directly
        db_products_by_id[product_id] = product_obj

        stock_obj = StockInDBBase(
            product_id=product_id, quantity=product_data["stock_quantity"]
        )
        db["stock"].append(stock_obj) # Keep populating the old list for now
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
        db["users"].append(user_obj) # Keep populating the old list for now
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
            db["addresses"].append(addr_obj) # Keep populating the old list for now
            db_addresses_by_id[addr_obj.address_id] = addr_obj
            db_addresses_by_user_id.setdefault(user_id, []).append(addr_obj)

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
            db["credit_cards"].append(card_obj) # Keep populating the old list for now
            db_credit_cards_by_id[card_obj.card_id] = card_obj
            db_credit_cards_by_user_id.setdefault(user_id, []).append(card_obj)

    # Load orders and order items if present (future-proofing)
    for order_data in data.get("orders", []):
        try:
            order_obj = OrderInDBBase(
                order_id=UUID(order_data["order_id"]),
                user_id=UUID(order_data["user_id"]),
                address_id=UUID(order_data["address_id"]),
                credit_card_id=UUID(order_data["credit_card_id"]),
                status=order_data.get("status", "pending"),
                total_amount=order_data.get("total_amount", 0.0),
                created_at=datetime.fromisoformat(order_data["created_at"])
                if order_data.get("created_at")
                else datetime.now(timezone.utc),
                updated_at=datetime.fromisoformat(order_data["updated_at"])
                if order_data.get("updated_at")
                else datetime.now(timezone.utc),
            )
        except Exception:
            continue
        db["orders"].append(order_obj)
        db_orders_by_id[order_obj.order_id] = order_obj
        db_orders_by_user_id.setdefault(order_obj.user_id, []).append(order_obj)

    for item_data in data.get("order_items", []):
        try:
            order_item_obj = OrderItemInDBBase(
                order_item_id=UUID(item_data["order_item_id"]),
                order_id=UUID(item_data["order_id"]),
                product_id=UUID(item_data["product_id"]),
                quantity=item_data["quantity"],
                price_at_purchase=item_data["price_at_purchase"],
            )
        except Exception:
            continue
        db["order_items"].append(order_item_obj)
        db_order_items_by_id[order_item_obj.order_item_id] = order_item_obj
        db_order_items_by_order_id.setdefault(order_item_obj.order_id, []).append(
            order_item_obj
        )
    print(f"Database initialized from {json_file_path}")


# Initialize DB from JSON when the module is loaded
initialize_database_from_json()