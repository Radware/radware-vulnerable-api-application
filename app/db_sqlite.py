from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from .db_base import DatabaseBackend
from .models.user_models import UserInDBBase, AddressInDBBase, CreditCardInDBBase
from .models.product_models import ProductInDBBase, StockInDBBase
from .models.order_models import OrderInDBBase, OrderItemInDBBase
from .models.coupon_models import CouponInDBBase
from .security import get_password_hash

DB_SQLITE_PATH = os.getenv("DB_SQLITE_PATH", "/app/data/db.sqlite")

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_protected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AddressModel(Base):
    __tablename__ = "addresses"
    address_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)
    is_protected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CreditCardModel(Base):
    __tablename__ = "credit_cards"
    card_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    card_number_hash = Column(String, nullable=False)
    cvv_hash = Column(String)
    card_last_four = Column(String, nullable=False)
    cardholder_name = Column(String, nullable=False)
    expiry_month = Column(String, nullable=False)
    expiry_year = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)
    is_protected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProductModel(Base):
    __tablename__ = "products"
    product_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String)
    internal_status = Column(String)
    is_protected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class StockModel(Base):
    __tablename__ = "stock"
    product_id = Column(String, primary_key=True)
    quantity = Column(Integer, default=0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OrderModel(Base):
    __tablename__ = "orders"
    order_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    address_id = Column(String, nullable=False)
    credit_card_id = Column(String, nullable=False)
    status = Column(String, default="pending")
    applied_coupon_id = Column(String)
    applied_coupon_code = Column(String)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OrderItemModel(Base):
    __tablename__ = "order_items"
    order_item_id = Column(String, primary_key=True)
    order_id = Column(String, nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)


class CouponModel(Base):
    __tablename__ = "coupons"
    coupon_id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    discount_type = Column(String, nullable=False)
    discount_value = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    usage_limit = Column(Integer)
    expiration_date = Column(DateTime)
    usage_count = Column(Integer, default=0)
    is_protected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SQLiteBackend(DatabaseBackend):
    """SQLAlchemy implementation of :class:`DatabaseBackend`.

    The name is kept for backward compatibility, but this class can now
    connect to any database supported by SQLAlchemy. If ``database_url`` is
    not provided, it falls back to using the ``DB_SQLITE_PATH`` location and
    SQLite.
    """

    def __init__(self, database_url: str | None = None) -> None:
        if database_url is None:
            db_path = DB_SQLITE_PATH
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            database_url = f"sqlite:///{db_path}"
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)
        self._initialize_if_empty()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------
    def _initialize_if_empty(self) -> None:
        with self.SessionLocal() as session:
            has_users = session.query(UserModel).first() is not None
        if not has_users:
            self.initialize_database_from_json()

    def initialize(self, prepopulated_path: str) -> None:
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

        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        with self.SessionLocal() as session:
            for product_data in data.get("products", []):
                prod = ProductModel(
                    product_id=product_data["product_id"],
                    name=product_data["name"],
                    description=product_data["description"],
                    price=product_data["price"],
                    category=product_data.get("category"),
                    is_protected=product_data.get("is_protected", False),
                )
                session.add(prod)
                stock = StockModel(
                    product_id=product_data["product_id"],
                    quantity=product_data["stock_quantity"],
                )
                session.add(stock)

            for user_data in data.get("users", []):
                user = UserModel(
                    user_id=user_data["user_id"],
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password_plain"]),
                    is_admin=user_data["is_admin"],
                    is_protected=user_data.get("is_protected", False),
                )
                session.add(user)
                for addr_data in user_data.get("addresses", []):
                    addr = AddressModel(
                        address_id=addr_data["address_id"],
                        user_id=user_data["user_id"],
                        street=addr_data["street"],
                        city=addr_data["city"],
                        country=addr_data["country"],
                        zip_code=addr_data["zip_code"],
                        is_default=addr_data["is_default"],
                        is_protected=addr_data.get("is_protected", False),
                    )
                    session.add(addr)
                for card_data in user_data.get("credit_cards", []):
                    card = CreditCardModel(
                        card_id=card_data["card_id"],
                        user_id=user_data["user_id"],
                        card_number_hash=get_password_hash(card_data["card_number_plain"]),
                        cvv_hash=get_password_hash(card_data["cvv_plain"]),
                        card_last_four=card_data["card_number_plain"][-4:],
                        cardholder_name=card_data["cardholder_name"],
                        expiry_month=card_data["expiry_month"],
                        expiry_year=card_data["expiry_year"],
                        is_default=card_data["is_default"],
                        is_protected=card_data.get("is_protected", False),
                    )
                    session.add(card)

            for order_data in data.get("orders", []):
                order = OrderModel(
                    order_id=order_data["order_id"],
                    user_id=order_data["user_id"],
                    address_id=order_data["address_id"],
                    credit_card_id=order_data["credit_card_id"],
                    status=order_data.get("status", "pending"),
                    total_amount=order_data.get("total_amount", 0.0),
                )
                session.add(order)

            for item_data in data.get("order_items", []):
                item = OrderItemModel(
                    order_item_id=item_data["order_item_id"],
                    order_id=item_data["order_id"],
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                    price_at_purchase=item_data["price_at_purchase"],
                )
                session.add(item)

            for coupon_data in data.get("coupons", []):
                coupon = CouponModel(
                    coupon_id=coupon_data["coupon_id"],
                    code=coupon_data["code"],
                    discount_type=coupon_data["discount_type"],
                    discount_value=coupon_data["discount_value"],
                    is_active=coupon_data.get("is_active", True),
                    usage_limit=coupon_data.get("usage_limit"),
                    expiration_date=coupon_data.get("expiration_date"),
                    usage_count=coupon_data.get("usage_count", 0),
                    is_protected=coupon_data.get("is_protected", False),
                )
                session.add(coupon)
            session.commit()
        print(f"Database initialized from {prepopulated_path}")

    def initialize_database_from_json(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        json_file_path = os.path.join(root_dir, "prepopulated_data.json")
        self.initialize(json_file_path)

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------
    def _session(self):
        return self.SessionLocal()

    def create_user(self, user: UserInDBBase) -> UserInDBBase:
        with self._session() as session:
            obj = UserModel(**user.model_dump())
            session.add(obj)
            session.commit()
        return user

    def get_user(self, user_id: UUID) -> Optional[UserInDBBase]:
        with self._session() as session:
            row = session.get(UserModel, str(user_id))
            if not row:
                return None
            return UserInDBBase.model_validate(row)

    def get_user_by_username(self, username: str) -> Optional[UserInDBBase]:
        with self._session() as session:
            row = session.query(UserModel).filter_by(username=username).first()
            return UserInDBBase.model_validate(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[UserInDBBase]:
        with self._session() as session:
            row = session.query(UserModel).filter_by(email=email).first()
            return UserInDBBase.model_validate(row) if row else None

    def update_user(self, user_id: UUID, update_data: dict) -> UserInDBBase:
        with self._session() as session:
            row = session.get(UserModel, str(user_id))
            for k, v in update_data.items():
                setattr(row, k, v)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return UserInDBBase.model_validate(row)

    def delete_user(self, user_id: UUID) -> None:
        with self._session() as session:
            row = session.get(UserModel, str(user_id))
            if row:
                session.delete(row)
                session.commit()

    def list_users(self) -> List[UserInDBBase]:
        with self._session() as session:
            rows = session.query(UserModel).all()
            return [UserInDBBase.model_validate(r) for r in rows]

    def create_address(self, address: AddressInDBBase) -> AddressInDBBase:
        with self._session() as session:
            obj = AddressModel(**address.model_dump())
            session.add(obj)
            session.commit()
        return address

    def get_address(self, address_id: UUID) -> Optional[AddressInDBBase]:
        with self._session() as session:
            row = session.get(AddressModel, str(address_id))
            return AddressInDBBase.model_validate(row) if row else None

    def list_addresses_for_user(self, user_id: UUID) -> List[AddressInDBBase]:
        with self._session() as session:
            rows = session.query(AddressModel).filter_by(user_id=str(user_id)).all()
            return [AddressInDBBase.model_validate(r) for r in rows]

    def update_address(self, address_id: UUID, update_data: dict) -> AddressInDBBase:
        with self._session() as session:
            row = session.get(AddressModel, str(address_id))
            for k, v in update_data.items():
                setattr(row, k, v)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return AddressInDBBase.model_validate(row)

    def delete_address(self, address_id: UUID) -> None:
        with self._session() as session:
            row = session.get(AddressModel, str(address_id))
            if row:
                session.delete(row)
                session.commit()

    def create_credit_card(self, card: CreditCardInDBBase) -> CreditCardInDBBase:
        with self._session() as session:
            obj = CreditCardModel(**card.model_dump())
            session.add(obj)
            session.commit()
        return card

    def get_credit_card(self, card_id: UUID) -> Optional[CreditCardInDBBase]:
        with self._session() as session:
            row = session.get(CreditCardModel, str(card_id))
            return CreditCardInDBBase.model_validate(row) if row else None

    def list_credit_cards_for_user(self, user_id: UUID) -> List[CreditCardInDBBase]:
        with self._session() as session:
            rows = session.query(CreditCardModel).filter_by(user_id=str(user_id)).all()
            return [CreditCardInDBBase.model_validate(r) for r in rows]

    def update_credit_card(self, card_id: UUID, update_data: dict) -> CreditCardInDBBase:
        with self._session() as session:
            row = session.get(CreditCardModel, str(card_id))
            for k, v in update_data.items():
                setattr(row, k, v)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return CreditCardInDBBase.model_validate(row)

    def delete_credit_card(self, card_id: UUID) -> None:
        with self._session() as session:
            row = session.get(CreditCardModel, str(card_id))
            if row:
                session.delete(row)
                session.commit()

    def create_product(self, product: ProductInDBBase) -> ProductInDBBase:
        with self._session() as session:
            obj = ProductModel(**product.model_dump())
            session.add(obj)
            stock = StockModel(product_id=str(product.product_id), quantity=0)
            session.add(stock)
            session.commit()
        return product

    def get_product(self, product_id: UUID) -> Optional[ProductInDBBase]:
        with self._session() as session:
            row = session.get(ProductModel, str(product_id))
            return ProductInDBBase.model_validate(row) if row else None

    def list_products(self) -> List[ProductInDBBase]:
        with self._session() as session:
            rows = session.query(ProductModel).all()
            return [ProductInDBBase.model_validate(r) for r in rows]

    def update_product(self, product_id: UUID, update_data: dict) -> ProductInDBBase:
        with self._session() as session:
            row = session.get(ProductModel, str(product_id))
            for k, v in update_data.items():
                setattr(row, k, v)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return ProductInDBBase.model_validate(row)

    def delete_product(self, product_id: UUID) -> None:
        with self._session() as session:
            row = session.get(ProductModel, str(product_id))
            if row:
                session.delete(row)
                stock = session.get(StockModel, str(product_id))
                if stock:
                    session.delete(stock)
                session.commit()

    def get_stock(self, product_id: UUID) -> Optional[StockInDBBase]:
        with self._session() as session:
            row = session.get(StockModel, str(product_id))
            return StockInDBBase.model_validate(row) if row else None

    def update_stock(self, product_id: UUID, quantity: int) -> StockInDBBase:
        with self._session() as session:
            row = session.get(StockModel, str(product_id))
            if not row:
                row = StockModel(product_id=str(product_id), quantity=quantity)
                session.add(row)
            else:
                row.quantity = quantity
                row.last_updated = datetime.now(timezone.utc)
            session.commit()
            return StockInDBBase.model_validate(row)

    def create_order(self, order: OrderInDBBase) -> OrderInDBBase:
        with self._session() as session:
            obj = OrderModel(**order.model_dump())
            session.add(obj)
            session.commit()
        return order

    def get_order(self, order_id: UUID) -> Optional[OrderInDBBase]:
        with self._session() as session:
            row = session.get(OrderModel, str(order_id))
            return OrderInDBBase.model_validate(row) if row else None

    def list_orders_for_user(self, user_id: UUID) -> List[OrderInDBBase]:
        with self._session() as session:
            rows = session.query(OrderModel).filter_by(user_id=str(user_id)).all()
            return [OrderInDBBase.model_validate(r) for r in rows]

    def update_order(self, order_id: UUID, update_data: dict) -> OrderInDBBase:
        with self._session() as session:
            row = session.get(OrderModel, str(order_id))
            for k, v in update_data.items():
                setattr(row, k, v)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return OrderInDBBase.model_validate(row)

    def delete_order(self, order_id: UUID) -> None:
        with self._session() as session:
            row = session.get(OrderModel, str(order_id))
            if row:
                session.delete(row)
                session.commit()

    def create_order_item(self, item: OrderItemInDBBase) -> OrderItemInDBBase:
        with self._session() as session:
            obj = OrderItemModel(**item.model_dump())
            session.add(obj)
            session.commit()
        return item

    def list_order_items(self, order_id: UUID) -> List[OrderItemInDBBase]:
        with self._session() as session:
            rows = session.query(OrderItemModel).filter_by(order_id=str(order_id)).all()
            return [OrderItemInDBBase.model_validate(r) for r in rows]

    def create_coupon(self, coupon: CouponInDBBase) -> CouponInDBBase:
        with self._session() as session:
            obj = CouponModel(**coupon.model_dump())
            session.add(obj)
            session.commit()
        return coupon

    def get_coupon(self, coupon_id: UUID) -> Optional[CouponInDBBase]:
        with self._session() as session:
            row = session.get(CouponModel, str(coupon_id))
            return CouponInDBBase.model_validate(row) if row else None

    def get_coupon_by_code(self, code: str) -> Optional[CouponInDBBase]:
        with self._session() as session:
            row = session.query(CouponModel).filter_by(code=code).first()
            return CouponInDBBase.model_validate(row) if row else None

    def update_coupon(self, coupon_id: UUID, update_data: dict) -> CouponInDBBase:
        with self._session() as session:
            row = session.get(CouponModel, str(coupon_id))
            for k, v in update_data.items():
                setattr(row, k, v)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return CouponInDBBase.model_validate(row)

    def delete_coupon(self, coupon_id: UUID) -> None:
        with self._session() as session:
            row = session.get(CouponModel, str(coupon_id))
            if row:
                session.delete(row)
                session.commit()

    def list_coupons(self) -> List[CouponInDBBase]:
        with self._session() as session:
            rows = session.query(CouponModel).all()
            return [CouponInDBBase.model_validate(r) for r in rows]
