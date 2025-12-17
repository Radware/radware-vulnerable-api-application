from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
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
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager
from sqlalchemy.pool import NullPool, QueuePool

from .db_base import DatabaseBackend
from .models.user_models import UserInDBBase, AddressInDBBase, CreditCardInDBBase
from .models.product_models import ProductInDBBase, StockInDBBase
from .models.order_models import OrderInDBBase, OrderItemInDBBase
from .models.coupon_models import CouponInDBBase
from .security import get_password_hash

DB_SQLITE_PATH = os.getenv("DB_SQLITE_PATH", "/app/data/db.sqlite")


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@contextmanager
def _startup_lock(engine):
    """Best-effort cross-process lock for DB bootstrap.

    When multiple Uvicorn workers start simultaneously and point at the same
    external database, table creation and auto-seeding can race. For databases
    that support it, we acquire an advisory lock to serialize those operations.
    """

    if not _env_flag("DB_STARTUP_LOCK", default=True):
        yield
        return

    dialect = getattr(engine.dialect, "name", "")
    if dialect == "postgresql":
        # Use a long timeout for the lock to handle slow startups
        with engine.connect() as conn:
            # Use a transaction to ensure the lock is held properly
            trans = conn.begin()
            try:
                conn.execute(text("SELECT pg_advisory_lock(:key)"), {"key": 424242})
                yield
            finally:
                conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": 424242})
                trans.commit()
        return

    if dialect in {"mysql", "mariadb"}:
        with engine.connect() as conn:
            conn.execute(
                text("SELECT GET_LOCK(:name, :timeout)"),
                {"name": "rva_bootstrap", "timeout": 60},
            )
            try:
                yield
            finally:
                conn.execute(
                    text("SELECT RELEASE_LOCK(:name)"),
                    {"name": "rva_bootstrap"},
                )
        return

    yield

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


# ------------------------------------------------------------------
# Dictionary-like proxy classes for backward compatibility
# ------------------------------------------------------------------
class DictLikeProxy:
    """Base class for dictionary-like proxies that maintain MemoryBackend compatibility."""
    
    def __init__(self, backend: 'SQLiteBackend'):
        self.backend = backend
    
    def get(self, key, default=None):
        try:
            result = self._get_item(key)
            return result if result is not None else default
        except (KeyError, ValueError):
            return default
    
    def __getitem__(self, key):
        result = self._get_item(key)
        if result is None:
            raise KeyError(key)
        return result
    
    def __setitem__(self, key, value):
        self._set_item(key, value)
    
    def pop(self, key, default=None):
        try:
            result = self._get_item(key)
            if result is not None:
                self._delete_item(key)
                return result
        except (KeyError, ValueError):
            pass
        return default
    
    def _get_item(self, key):
        raise NotImplementedError
    
    def _set_item(self, key, value):
        raise NotImplementedError
    
    def _delete_item(self, key):
        raise NotImplementedError


class UsersByUsernameProxy(DictLikeProxy):
    def _get_item(self, username: str):
        return self.backend.get_user_by_username(username)
    
    def _set_item(self, username: str, user: UserInDBBase):
        # This is called after user creation/update, no-op for SQLAlchemy backend
        pass
    
    def _delete_item(self, username: str):
        # Called during user deletion, actual deletion handled elsewhere
        pass


class UsersByEmailProxy(DictLikeProxy):
    def _get_item(self, email: str):
        return self.backend.get_user_by_email(email)
    
    def _set_item(self, email: str, user: UserInDBBase):
        pass
    
    def _delete_item(self, email: str):
        pass


class ProductsByIdProxy(DictLikeProxy):
    def _get_item(self, product_id):
        if isinstance(product_id, str):
            product_id = UUID(product_id)
        return self.backend.get_product(product_id)
    
    def _set_item(self, product_id, product: ProductInDBBase):
        pass
    
    def _delete_item(self, product_id):
        pass


class CouponsByCodeProxy(DictLikeProxy):
    def _get_item(self, code: str):
        return self.backend.get_coupon_by_code(code)
    
    def _set_item(self, code: str, coupon: CouponInDBBase):
        pass
    
    def _delete_item(self, code: str):
        pass


class UsersByIdProxy(DictLikeProxy):
    def _get_item(self, user_id):
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return self.backend.get_user(user_id)
    
    def _set_item(self, user_id, user: UserInDBBase):
        pass
    
    def _delete_item(self, user_id):
        pass


class AddressesByIdProxy(DictLikeProxy):
    def _get_item(self, address_id):
        if isinstance(address_id, str):
            address_id = UUID(address_id)
        return self.backend.get_address(address_id)
    
    def _set_item(self, address_id, address: AddressInDBBase):
        pass
    
    def _delete_item(self, address_id):
        pass


class AddressesByUserIdProxy(DictLikeProxy):
    """Proxy for addresses grouped by user_id."""
    def _get_item(self, user_id):
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return self.backend.list_addresses_for_user(user_id)
    
    def _set_item(self, user_id, addresses):
        # This is complex, not used in write operations
        pass
    
    def _delete_item(self, user_id):
        pass
    
    def setdefault(self, key, default=None):
        """Special method for setdefault used in address creation."""
        result = self.get(key, default)
        return result if result is not None else default


class CreditCardsByIdProxy(DictLikeProxy):
    def _get_item(self, card_id):
        if isinstance(card_id, str):
            card_id = UUID(card_id)
        return self.backend.get_credit_card(card_id)
    
    def _set_item(self, card_id, card: CreditCardInDBBase):
        pass
    
    def _delete_item(self, card_id):
        pass


class CreditCardsByUserIdProxy(DictLikeProxy):
    """Proxy for credit cards grouped by user_id."""
    def _get_item(self, user_id):
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return self.backend.list_credit_cards_for_user(user_id)
    
    def _set_item(self, user_id, cards):
        pass
    
    def _delete_item(self, user_id):
        pass
    
    def setdefault(self, key, default=None):
        """Special method for setdefault used in credit card creation."""
        result = self.get(key, default)
        return result if result is not None else default


class StockByProductIdProxy(DictLikeProxy):
    def _get_item(self, product_id):
        if isinstance(product_id, str):
            product_id = UUID(product_id)
        return self.backend.get_stock(product_id)
    
    def _set_item(self, product_id, stock: StockInDBBase):
        # Stock updates go through update_stock
        pass
    
    def _delete_item(self, product_id):
        pass


class OrdersByIdProxy(DictLikeProxy):
    def _get_item(self, order_id):
        if isinstance(order_id, str):
            order_id = UUID(order_id)
        return self.backend.get_order(order_id)
    
    def _set_item(self, order_id, order: OrderInDBBase):
        pass
    
    def _delete_item(self, order_id):
        pass


class OrdersByUserIdProxy(DictLikeProxy):
    """Proxy for orders grouped by user_id."""
    def _get_item(self, user_id):
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return self.backend.list_orders_for_user(user_id)
    
    def _set_item(self, user_id, orders):
        pass
    
    def _delete_item(self, user_id):
        pass
    
    def setdefault(self, key, default=None):
        """Special method for setdefault used in order creation."""
        result = self.get(key, default)
        return result if result is not None else default


class OrderItemsByIdProxy(DictLikeProxy):
    def _get_item(self, item_id):
        # Order items are usually accessed by order_id, not item_id
        # This is a simplified implementation
        return None
    
    def _set_item(self, item_id, item: OrderItemInDBBase):
        pass
    
    def _delete_item(self, item_id):
        pass


class OrderItemsByOrderIdProxy(DictLikeProxy):
    """Proxy for order items grouped by order_id."""
    def _get_item(self, order_id):
        if isinstance(order_id, str):
            order_id = UUID(order_id)
        return self.backend.list_order_items(order_id)
    
    def _set_item(self, order_id, items):
        pass
    
    def _delete_item(self, order_id):
        pass
    
    def setdefault(self, key, default=None):
        """Special method for setdefault used in order item creation."""
        result = self.get(key, default)
        return result if result is not None else default


class CouponsByIdProxy(DictLikeProxy):
    def _get_item(self, coupon_id):
        if isinstance(coupon_id, str):
            coupon_id = UUID(coupon_id)
        return self.backend.get_coupon(coupon_id)
    
    def _set_item(self, coupon_id, coupon: CouponInDBBase):
        pass
    
    def _delete_item(self, coupon_id):
        pass


class DatabaseProxy:
    """Proxy that provides db['collection'] access pattern for SQLiteBackend."""
    
    def __init__(self, backend: 'SQLiteBackend'):
        self.backend = backend
    
    def __getitem__(self, key: str):
        """Return a collection proxy that mimics list operations."""
        return CollectionProxy(self.backend, key)


class CollectionProxy:
    """Proxy for a specific collection (e.g., 'users', 'products') that mimics list operations."""
    
    def __init__(self, backend: 'SQLiteBackend', collection: str):
        self.backend = backend
        self.collection = collection
    
    def append(self, item):
        """Add item to collection. Actual persistence handled by specific methods."""
        # Items are persisted through specific create methods, this is just for compatibility
        pass
    
    def remove(self, item):
        """Remove item from collection. Actual deletion handled by specific methods."""
        # Deletions are handled through specific delete methods, this is just for compatibility
        pass
    
    def __contains__(self, item):
        """Check if item exists in collection."""
        # This is used for existence checks before operations
        if self.collection == "users" and hasattr(item, 'user_id'):
            return self.backend.get_user(item.user_id) is not None
        elif self.collection == "addresses" and hasattr(item, 'address_id'):
            return self.backend.get_address(item.address_id) is not None
        elif self.collection == "credit_cards" and hasattr(item, 'card_id'):
            return self.backend.get_credit_card(item.card_id) is not None
        elif self.collection == "products" and hasattr(item, 'product_id'):
            return self.backend.get_product(item.product_id) is not None
        elif self.collection == "orders" and hasattr(item, 'order_id'):
            return self.backend.get_order(item.order_id) is not None
        elif self.collection == "order_items" and hasattr(item, 'order_item_id'):
            # Order items don't have a direct get method, return True for now
            return True
        elif self.collection == "stock" and hasattr(item, 'product_id'):
            return self.backend.get_stock(item.product_id) is not None
        return False
    
    def __iter__(self):
        """Iterate over all items in collection."""
        if self.collection == "users":
            return iter(self.backend.list_users())
        elif self.collection == "products":
            return iter(self.backend.list_products())
        elif self.collection == "orders":
            # This would need a list_all_orders method, for now return empty
            return iter([])
        elif self.collection == "addresses":
            # This would need a list_all_addresses method, for now return empty
            return iter([])
        elif self.collection == "credit_cards":
            # This would need a list_all_credit_cards method, for now return empty
            return iter([])
        elif self.collection == "stock":
            # This would need a list_all_stock method, for now return empty
            return iter([])
        elif self.collection == "order_items":
            return iter([])
        return iter([])
    
    def __setitem__(self, key, value):
        """Assignment to collection (e.g., db['stock'] = [...])."""
        # This is used for bulk operations like filtering stock
        # In SQLite backend, we don't support this pattern directly
        pass


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
        
        # Determine if we're using SQLite or an external DB
        is_sqlite = database_url.startswith("sqlite")
        
        # Configure connection arguments and pooling based on database type
        if is_sqlite:
            connect_args = {"check_same_thread": False}
            # SQLite doesn't benefit from connection pooling with multiple workers
            poolclass = NullPool
        else:
            connect_args = {}
            # Use connection pooling for external databases (PostgreSQL, MySQL)
            poolclass = QueuePool
        
        # Create engine with appropriate configuration
        engine_kwargs = {
            "connect_args": connect_args,
            "poolclass": poolclass,
        }
        
        # Additional pool settings for external databases
        if not is_sqlite:
            engine_kwargs.update({
                "pool_size": 10,  # Number of connections to keep open
                "max_overflow": 20,  # Additional connections when pool is exhausted
                "pool_pre_ping": True,  # Verify connections before using them
                "pool_recycle": 3600,  # Recycle connections after 1 hour
            })
        
        self.engine = create_engine(database_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

        # Initialize dictionary-like proxies for backward compatibility with MemoryBackend
        self.db = DatabaseProxy(self)  # For db["collection"] access pattern
        self.db_users_by_id = UsersByIdProxy(self)
        self.db_users_by_username = UsersByUsernameProxy(self)
        self.db_users_by_email = UsersByEmailProxy(self)
        self.db_addresses_by_id = AddressesByIdProxy(self)
        self.db_addresses_by_user_id = AddressesByUserIdProxy(self)
        self.db_credit_cards_by_id = CreditCardsByIdProxy(self)
        self.db_credit_cards_by_user_id = CreditCardsByUserIdProxy(self)
        self.db_products_by_id = ProductsByIdProxy(self)
        self.db_stock_by_product_id = StockByProductIdProxy(self)
        self.db_orders_by_id = OrdersByIdProxy(self)
        self.db_orders_by_user_id = OrdersByUserIdProxy(self)
        self.db_order_items_by_id = OrderItemsByIdProxy(self)
        self.db_order_items_by_order_id = OrderItemsByOrderIdProxy(self)
        self.db_coupons_by_id = CouponsByIdProxy(self)
        self.db_coupons_by_code = CouponsByCodeProxy(self)

        skip_schema = _env_flag("DB_SKIP_SCHEMA_INIT")
        skip_seed = _env_flag("DB_SKIP_AUTO_SEED")

        with _startup_lock(self.engine):
            if not skip_schema:
                Base.metadata.create_all(self.engine)
            if not skip_seed:
                self._initialize_if_empty()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------
    def _initialize_if_empty(self) -> None:
        """Initialize database from JSON only if it's empty."""
        try:
            with self.SessionLocal() as session:
                has_users = session.query(UserModel).first() is not None
            if not has_users:
                print("📋 Database is empty, initializing from prepopulated_data.json...")
                self.initialize_database_from_json()
            else:
                print("✓ Database already initialized, skipping seed data")
        except Exception as e:
            print(f"⚠️  Error checking if database is empty: {e}")
            import traceback
            traceback.print_exc()

    def initialize(self, prepopulated_path: str) -> None:
        """Initialize database from JSON file. Drops and recreates all tables."""
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

        # Drop and recreate tables
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        
        with self.SessionLocal() as session:
            # Insert products and stock
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

            # Insert users and their related data
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
                        card_number_hash=get_password_hash(
                            card_data["card_number_plain"]
                        ),
                        cvv_hash=get_password_hash(card_data["cvv_plain"]),
                        card_last_four=card_data["card_number_plain"][-4:],
                        cardholder_name=card_data["cardholder_name"],
                        expiry_month=card_data["expiry_month"],
                        expiry_year=card_data["expiry_year"],
                        is_default=card_data["is_default"],
                        is_protected=card_data.get("is_protected", False),
                    )
                    session.add(card)

            # Insert orders
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

            # Insert order items
            for item_data in data.get("order_items", []):
                item = OrderItemModel(
                    order_item_id=item_data["order_item_id"],
                    order_id=item_data["order_id"],
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                    price_at_purchase=item_data["price_at_purchase"],
                )
                session.add(item)

            # Insert coupons - commit each separately to handle potential duplicates
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
            
            # Commit all changes at once
            try:
                session.commit()
                print(f"✅ Database successfully initialized from {prepopulated_path}")
            except IntegrityError as e:
                session.rollback()
                print(f"⚠️  Integrity error during initialization (may be normal in multi-worker setup): {e}")
                # Check if data was partially inserted
                with self.SessionLocal() as check_session:
                    user_count = check_session.query(UserModel).count()
                    if user_count > 0:
                        print(f"✓ Database has {user_count} users, initialization appears successful despite error")
            except Exception as e:
                session.rollback()
                print(f"❌ Error during database initialization: {e}")
                import traceback
                traceback.print_exc()
                raise

    def initialize_database_from_json(self) -> None:
        """Initialize database from the default prepopulated_data.json file."""
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

    def update_credit_card(
        self, card_id: UUID, update_data: dict
    ) -> CreditCardInDBBase:
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
