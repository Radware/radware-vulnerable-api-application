from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID
import json
import os
from datetime import datetime, timezone

from .db_base import DatabaseBackend
from .models.user_models import UserInDBBase, AddressInDBBase, CreditCardInDBBase
from .models.product_models import ProductInDBBase, StockInDBBase
from .models.order_models import OrderInDBBase, OrderItemInDBBase
from .models.coupon_models import CouponInDBBase
from .security import get_password_hash


class MemoryBackend(DatabaseBackend):
    """In-memory implementation of :class:`DatabaseBackend`."""

    def __init__(self) -> None:
        # tables like structures
        self.db: Dict[str, List[Any]] = {
            "users": [],
            "addresses": [],
            "credit_cards": [],
            "products": [],
            "stock": [],
            "orders": [],
            "order_items": [],
        }
        # quick lookup indexes
        self.db_users_by_id: Dict[UUID, UserInDBBase] = {}
        self.db_users_by_username: Dict[str, UserInDBBase] = {}
        self.db_users_by_email: Dict[str, UserInDBBase] = {}
        self.db_addresses_by_id: Dict[UUID, AddressInDBBase] = {}
        self.db_addresses_by_user_id: Dict[UUID, List[AddressInDBBase]] = {}
        self.db_credit_cards_by_id: Dict[UUID, CreditCardInDBBase] = {}
        self.db_credit_cards_by_user_id: Dict[UUID, List[CreditCardInDBBase]] = {}
        self.db_products_by_id: Dict[UUID, ProductInDBBase] = {}
        self.db_stock_by_product_id: Dict[UUID, StockInDBBase] = {}
        self.db_orders_by_id: Dict[UUID, OrderInDBBase] = {}
        self.db_orders_by_user_id: Dict[UUID, List[OrderInDBBase]] = {}
        self.db_order_items_by_id: Dict[UUID, OrderItemInDBBase] = {}
        self.db_order_items_by_order_id: Dict[UUID, List[OrderItemInDBBase]] = {}
        self.db_coupons_by_id: Dict[UUID, CouponInDBBase] = {}
        self.db_coupons_by_code: Dict[str, CouponInDBBase] = {}

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------
    def initialize(self, prepopulated_path: str) -> None:
        """Load data from ``prepopulated_path`` into the in-memory store."""
        try:
            with open(prepopulated_path, "r") as fh:
                data = json.load(fh)
        except FileNotFoundError:
            print(f"Error: {prepopulated_path} not found. Cannot initialize database.")
            return
        except json.JSONDecodeError:
            print(
                f"Error: Could not decode JSON from {prepopulated_path}. Cannot initialize database."
            )
            return

        # clear existing
        for key in self.db:
            self.db[key].clear()
        self.db_users_by_id.clear()
        self.db_users_by_username.clear()
        self.db_users_by_email.clear()
        self.db_addresses_by_id.clear()
        self.db_addresses_by_user_id.clear()
        self.db_credit_cards_by_id.clear()
        self.db_credit_cards_by_user_id.clear()
        self.db_products_by_id.clear()
        self.db_stock_by_product_id.clear()
        self.db_orders_by_id.clear()
        self.db_orders_by_user_id.clear()
        self.db_order_items_by_id.clear()
        self.db_order_items_by_order_id.clear()
        self.db_coupons_by_id.clear()
        self.db_coupons_by_code.clear()

        # ----------------------------------------
        # Load products and stock
        # ----------------------------------------
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
            self.db["products"].append(product_obj)
            self.db_products_by_id[product_id] = product_obj

            stock_obj = StockInDBBase(
                product_id=product_id, quantity=product_data["stock_quantity"]
            )
            self.db["stock"].append(stock_obj)
            self.db_stock_by_product_id[product_id] = stock_obj

        # ----------------------------------------
        # Load users, addresses and credit cards
        # ----------------------------------------
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
            self.db["users"].append(user_obj)
            self.db_users_by_id[user_id] = user_obj
            self.db_users_by_username[user_obj.username] = user_obj
            self.db_users_by_email[user_obj.email] = user_obj

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
                self.db["addresses"].append(addr_obj)
                self.db_addresses_by_id[addr_obj.address_id] = addr_obj
                self.db_addresses_by_user_id.setdefault(user_id, []).append(addr_obj)

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
                self.db["credit_cards"].append(card_obj)
                self.db_credit_cards_by_id[card_obj.card_id] = card_obj
                self.db_credit_cards_by_user_id.setdefault(user_id, []).append(card_obj)

        # ----------------------------------------
        # Load orders and order items
        # ----------------------------------------
        for order_data in data.get("orders", []):
            try:
                order_obj = OrderInDBBase(
                    order_id=UUID(order_data["order_id"]),
                    user_id=UUID(order_data["user_id"]),
                    address_id=UUID(order_data["address_id"]),
                    credit_card_id=UUID(order_data["credit_card_id"]),
                    status=order_data.get("status", "pending"),
                    total_amount=order_data.get("total_amount", 0.0),
                    created_at=(
                        datetime.fromisoformat(order_data["created_at"])
                        if order_data.get("created_at")
                        else datetime.now(timezone.utc)
                    ),
                    updated_at=(
                        datetime.fromisoformat(order_data["updated_at"])
                        if order_data.get("updated_at")
                        else datetime.now(timezone.utc)
                    ),
                )
            except Exception:
                continue
            self.db["orders"].append(order_obj)
            self.db_orders_by_id[order_obj.order_id] = order_obj
            self.db_orders_by_user_id.setdefault(order_obj.user_id, []).append(
                order_obj
            )

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
            self.db["order_items"].append(order_item_obj)
            self.db_order_items_by_id[order_item_obj.order_item_id] = order_item_obj
            self.db_order_items_by_order_id.setdefault(
                order_item_obj.order_id, []
            ).append(order_item_obj)

        for coupon_data in data.get("coupons", []):
            try:
                coupon_obj = CouponInDBBase(
                    coupon_id=UUID(coupon_data["coupon_id"]),
                    code=coupon_data["code"],
                    discount_type=coupon_data["discount_type"],
                    discount_value=coupon_data["discount_value"],
                    is_active=coupon_data.get("is_active", True),
                    usage_limit=coupon_data.get("usage_limit"),
                    expiration_date=(
                        datetime.fromisoformat(coupon_data["expiration_date"])
                        if coupon_data.get("expiration_date")
                        else None
                    ),
                    usage_count=coupon_data.get("usage_count", 0),
                    is_protected=coupon_data.get("is_protected", False),
                    created_at=(
                        datetime.fromisoformat(coupon_data["created_at"])
                        if coupon_data.get("created_at")
                        else datetime.now(timezone.utc)
                    ),
                    updated_at=(
                        datetime.fromisoformat(coupon_data["updated_at"])
                        if coupon_data.get("updated_at")
                        else datetime.now(timezone.utc)
                    ),
                )
            except Exception:
                continue
            self.db_coupons_by_id[coupon_obj.coupon_id] = coupon_obj
            self.db_coupons_by_code[coupon_obj.code] = coupon_obj
        print(f"Coupons initialized: {len(self.db_coupons_by_code)} coupons loaded.")
        print(f"Database initialized from {prepopulated_path}")

    def initialize_database_from_json(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        json_file_path = os.path.join(root_dir, "prepopulated_data.json")
        self.initialize(json_file_path)

    # ------------------------------------------------------------------
    # Helper CRUD methods required by DatabaseBackend
    # ------------------------------------------------------------------
    def create_user(self, user: UserInDBBase) -> UserInDBBase:
        self.db["users"].append(user)
        self.db_users_by_id[user.user_id] = user
        self.db_users_by_username[user.username] = user
        self.db_users_by_email[user.email] = user
        return user

    def get_user(self, user_id: UUID) -> Optional[UserInDBBase]:
        return self.db_users_by_id.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[UserInDBBase]:
        return self.db_users_by_username.get(username)

    def get_user_by_email(self, email: str) -> Optional[UserInDBBase]:
        return self.db_users_by_email.get(email)

    def update_user(self, user_id: UUID, update_data: dict) -> UserInDBBase:
        user = self.db_users_by_id[user_id]
        for k, v in update_data.items():
            setattr(user, k, v)
        user.updated_at = datetime.now(timezone.utc)
        return user

    def delete_user(self, user_id: UUID) -> None:
        user = self.db_users_by_id.pop(user_id, None)
        if not user:
            return
        self.db_users_by_username.pop(user.username, None)
        self.db_users_by_email.pop(user.email, None)
        self.db["users"] = [u for u in self.db["users"] if u.user_id != user_id]

    def list_users(self) -> List[UserInDBBase]:
        return list(self.db_users_by_id.values())

    def create_address(self, address: AddressInDBBase) -> AddressInDBBase:
        self.db["addresses"].append(address)
        self.db_addresses_by_id[address.address_id] = address
        self.db_addresses_by_user_id.setdefault(address.user_id, []).append(address)
        return address

    def get_address(self, address_id: UUID) -> Optional[AddressInDBBase]:
        return self.db_addresses_by_id.get(address_id)

    def list_addresses_for_user(self, user_id: UUID) -> List[AddressInDBBase]:
        return list(self.db_addresses_by_user_id.get(user_id, []))

    def update_address(self, address_id: UUID, update_data: dict) -> AddressInDBBase:
        addr = self.db_addresses_by_id[address_id]
        for k, v in update_data.items():
            setattr(addr, k, v)
        addr.updated_at = datetime.now(timezone.utc)
        return addr

    def delete_address(self, address_id: UUID) -> None:
        addr = self.db_addresses_by_id.pop(address_id, None)
        if not addr:
            return
        user_list = self.db_addresses_by_user_id.get(addr.user_id, [])
        self.db_addresses_by_user_id[addr.user_id] = [
            a for a in user_list if a.address_id != address_id
        ]
        self.db["addresses"] = [
            a for a in self.db["addresses"] if a.address_id != address_id
        ]

    def create_credit_card(self, card: CreditCardInDBBase) -> CreditCardInDBBase:
        self.db["credit_cards"].append(card)
        self.db_credit_cards_by_id[card.card_id] = card
        self.db_credit_cards_by_user_id.setdefault(card.user_id, []).append(card)
        return card

    def get_credit_card(self, card_id: UUID) -> Optional[CreditCardInDBBase]:
        return self.db_credit_cards_by_id.get(card_id)

    def list_credit_cards_for_user(self, user_id: UUID) -> List[CreditCardInDBBase]:
        return list(self.db_credit_cards_by_user_id.get(user_id, []))

    def update_credit_card(
        self, card_id: UUID, update_data: dict
    ) -> CreditCardInDBBase:
        card = self.db_credit_cards_by_id[card_id]
        for k, v in update_data.items():
            setattr(card, k, v)
        card.updated_at = datetime.now(timezone.utc)
        return card

    def delete_credit_card(self, card_id: UUID) -> None:
        card = self.db_credit_cards_by_id.pop(card_id, None)
        if not card:
            return
        lst = self.db_credit_cards_by_user_id.get(card.user_id, [])
        self.db_credit_cards_by_user_id[card.user_id] = [
            c for c in lst if c.card_id != card_id
        ]
        self.db["credit_cards"] = [
            c for c in self.db["credit_cards"] if c.card_id != card_id
        ]

    def create_product(self, product: ProductInDBBase) -> ProductInDBBase:
        self.db["products"].append(product)
        self.db_products_by_id[product.product_id] = product
        return product

    def get_product(self, product_id: UUID) -> Optional[ProductInDBBase]:
        return self.db_products_by_id.get(product_id)

    def list_products(self) -> List[ProductInDBBase]:
        return list(self.db_products_by_id.values())

    def update_product(self, product_id: UUID, update_data: dict) -> ProductInDBBase:
        prod = self.db_products_by_id[product_id]
        for k, v in update_data.items():
            setattr(prod, k, v)
        prod.updated_at = datetime.now(timezone.utc)
        return prod

    def delete_product(self, product_id: UUID) -> None:
        prod = self.db_products_by_id.pop(product_id, None)
        if not prod:
            return
        self.db["products"] = [
            p for p in self.db["products"] if p.product_id != product_id
        ]
        self.db_stock_by_product_id.pop(product_id, None)
        self.db["stock"] = [s for s in self.db["stock"] if s.product_id != product_id]

    def get_stock(self, product_id: UUID) -> Optional[StockInDBBase]:
        return self.db_stock_by_product_id.get(product_id)

    def update_stock(self, product_id: UUID, quantity: int) -> StockInDBBase:
        stock = self.db_stock_by_product_id.get(product_id)
        if not stock:
            stock = StockInDBBase(product_id=product_id, quantity=quantity)
            self.db_stock_by_product_id[product_id] = stock
            self.db["stock"].append(stock)
        else:
            stock.quantity = quantity
        return stock

    def list_stock_for_products(
        self, product_ids: List[UUID]
    ) -> Dict[UUID, StockInDBBase]:
        stock_map: Dict[UUID, StockInDBBase] = {}
        for product_id in product_ids:
            stock_obj = self.db_stock_by_product_id.get(product_id)
            if stock_obj is not None:
                stock_map[product_id] = stock_obj
        return stock_map

    def create_order(self, order: OrderInDBBase) -> OrderInDBBase:
        self.db["orders"].append(order)
        self.db_orders_by_id[order.order_id] = order
        self.db_orders_by_user_id.setdefault(order.user_id, []).append(order)
        return order

    def get_order(self, order_id: UUID) -> Optional[OrderInDBBase]:
        return self.db_orders_by_id.get(order_id)

    def list_orders_for_user(self, user_id: UUID) -> List[OrderInDBBase]:
        return list(self.db_orders_by_user_id.get(user_id, []))

    def update_order(self, order_id: UUID, update_data: dict) -> OrderInDBBase:
        order = self.db_orders_by_id[order_id]
        for k, v in update_data.items():
            setattr(order, k, v)
        order.updated_at = datetime.now(timezone.utc)
        return order

    def delete_order(self, order_id: UUID) -> None:
        order = self.db_orders_by_id.pop(order_id, None)
        if not order:
            return
        self.db_orders_by_user_id[order.user_id] = [
            o
            for o in self.db_orders_by_user_id.get(order.user_id, [])
            if o.order_id != order_id
        ]
        self.db["orders"] = [o for o in self.db["orders"] if o.order_id != order_id]
        self.db_order_items_by_order_id.pop(order_id, None)

    def create_order_item(self, item: OrderItemInDBBase) -> OrderItemInDBBase:
        self.db["order_items"].append(item)
        self.db_order_items_by_id[item.order_item_id] = item
        self.db_order_items_by_order_id.setdefault(item.order_id, []).append(item)
        return item

    def list_order_items(self, order_id: UUID) -> List[OrderItemInDBBase]:
        return list(self.db_order_items_by_order_id.get(order_id, []))

    def create_coupon(self, coupon: CouponInDBBase) -> CouponInDBBase:
        self.db_coupons_by_id[coupon.coupon_id] = coupon
        self.db_coupons_by_code[coupon.code] = coupon
        return coupon

    def get_coupon(self, coupon_id: UUID) -> Optional[CouponInDBBase]:
        return self.db_coupons_by_id.get(coupon_id)

    def get_coupon_by_code(self, code: str) -> Optional[CouponInDBBase]:
        return self.db_coupons_by_code.get(code)

    def update_coupon(self, coupon_id: UUID, update_data: dict) -> CouponInDBBase:
        coupon = self.db_coupons_by_id[coupon_id]
        for k, v in update_data.items():
            setattr(coupon, k, v)
        coupon.updated_at = datetime.now(timezone.utc)
        return coupon

    def delete_coupon(self, coupon_id: UUID) -> None:
        coupon = self.db_coupons_by_id.pop(coupon_id, None)
        if not coupon:
            return
        self.db_coupons_by_code.pop(coupon.code, None)

    def list_coupons(self) -> List[CouponInDBBase]:
        return list(self.db_coupons_by_id.values())
