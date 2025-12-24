from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from .models.user_models import UserInDBBase, AddressInDBBase, CreditCardInDBBase
from .models.product_models import ProductInDBBase, StockInDBBase
from .models.order_models import OrderInDBBase, OrderItemInDBBase
from .models.coupon_models import CouponInDBBase


class DatabaseBackend(ABC):
    """Abstract interface for database backends."""

    @abstractmethod
    def initialize(self, prepopulated_path: str) -> None:
        """Initialize the datastore from the given JSON path."""
        raise NotImplementedError

    # --- User operations ---
    @abstractmethod
    def create_user(self, user: UserInDBBase) -> UserInDBBase:
        raise NotImplementedError

    @abstractmethod
    def get_user(self, user_id: UUID) -> Optional[UserInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[UserInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[UserInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def update_user(self, user_id: UUID, update_data: dict) -> UserInDBBase:
        raise NotImplementedError

    @abstractmethod
    def delete_user(self, user_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_users(self) -> List[UserInDBBase]:
        raise NotImplementedError

    # --- Address operations ---
    @abstractmethod
    def create_address(self, address: AddressInDBBase) -> AddressInDBBase:
        raise NotImplementedError

    @abstractmethod
    def get_address(self, address_id: UUID) -> Optional[AddressInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def list_addresses_for_user(self, user_id: UUID) -> List[AddressInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def update_address(self, address_id: UUID, update_data: dict) -> AddressInDBBase:
        raise NotImplementedError

    @abstractmethod
    def delete_address(self, address_id: UUID) -> None:
        raise NotImplementedError

    # --- Credit card operations ---
    @abstractmethod
    def create_credit_card(self, card: CreditCardInDBBase) -> CreditCardInDBBase:
        raise NotImplementedError

    @abstractmethod
    def get_credit_card(self, card_id: UUID) -> Optional[CreditCardInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def list_credit_cards_for_user(self, user_id: UUID) -> List[CreditCardInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def update_credit_card(
        self, card_id: UUID, update_data: dict
    ) -> CreditCardInDBBase:
        raise NotImplementedError

    @abstractmethod
    def delete_credit_card(self, card_id: UUID) -> None:
        raise NotImplementedError

    # --- Product operations ---
    @abstractmethod
    def create_product(self, product: ProductInDBBase) -> ProductInDBBase:
        raise NotImplementedError

    @abstractmethod
    def get_product(self, product_id: UUID) -> Optional[ProductInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def list_products(self) -> List[ProductInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def update_product(self, product_id: UUID, update_data: dict) -> ProductInDBBase:
        raise NotImplementedError

    @abstractmethod
    def delete_product(self, product_id: UUID) -> None:
        raise NotImplementedError

    # --- Stock operations ---
    @abstractmethod
    def get_stock(self, product_id: UUID) -> Optional[StockInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def update_stock(self, product_id: UUID, quantity: int) -> StockInDBBase:
        raise NotImplementedError

    @abstractmethod
    def list_stock_for_products(
        self, product_ids: List[UUID]
    ) -> Dict[UUID, StockInDBBase]:
        raise NotImplementedError

    # --- Order operations ---
    @abstractmethod
    def create_order(self, order: OrderInDBBase) -> OrderInDBBase:
        raise NotImplementedError

    @abstractmethod
    def get_order(self, order_id: UUID) -> Optional[OrderInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def list_orders_for_user(self, user_id: UUID) -> List[OrderInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def update_order(self, order_id: UUID, update_data: dict) -> OrderInDBBase:
        raise NotImplementedError

    @abstractmethod
    def delete_order(self, order_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_order_item(self, item: OrderItemInDBBase) -> OrderItemInDBBase:
        raise NotImplementedError

    @abstractmethod
    def list_order_items(self, order_id: UUID) -> List[OrderItemInDBBase]:
        raise NotImplementedError

    # --- Coupon operations ---
    @abstractmethod
    def create_coupon(self, coupon: CouponInDBBase) -> CouponInDBBase:
        raise NotImplementedError

    @abstractmethod
    def get_coupon(self, coupon_id: UUID) -> Optional[CouponInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def get_coupon_by_code(self, code: str) -> Optional[CouponInDBBase]:
        raise NotImplementedError

    @abstractmethod
    def update_coupon(self, coupon_id: UUID, update_data: dict) -> CouponInDBBase:
        raise NotImplementedError

    @abstractmethod
    def delete_coupon(self, coupon_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_coupons(self) -> List[CouponInDBBase]:
        raise NotImplementedError
