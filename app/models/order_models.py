from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from .user_models import User, Address, CreditCard  # Assuming these are defined
from .product_models import Product  # Assuming this is defined


class OrderItemBase(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemInDBBase(OrderItemBase):
    order_item_id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    price_at_purchase: float  # Will be set when order is created

    model_config = {"from_attributes": True}


class OrderItem(OrderItemInDBBase):
    pass


class OrderBase(BaseModel):
    """Base fields shared by order models."""

    user_id: UUID  # Will be set from path or JWT
    address_id: UUID  # From query param - BOLA target
    credit_card_id: UUID  # From query param - BOLA target
    status: str = "pending"
    applied_coupon_id: Optional[UUID] = None
    applied_coupon_code: Optional[str] = None
    discount_amount: float = Field(default=0.0, ge=0)


class OrderCreate(BaseModel):
    # user_id will come from path/JWT
    address_id: UUID  # From query param - BOLA target
    credit_card_id: UUID  # From query param - BOLA target
    # products will be passed as product_id_1, quantity_1 etc. in query
    # This model is more for conceptual grouping; actual creation logic will parse dynamic query params


class OrderInDBBase(OrderBase):
    """Representation of an order stored in the database."""

    order_id: UUID = Field(default_factory=uuid4)
    total_amount: float = Field(
        default=0.0,
        description="Final price of the order after applying any discount",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"from_attributes": True}


class Order(OrderInDBBase):
    """Public facing order model."""

    items: List[OrderItem] = []
    credit_card_last_four: Optional[str] = None


class LegacyOrderStatus(BaseModel):
    order_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    address: Optional[Address] = None
    credit_card_id: Optional[UUID] = None
    credit_card_last_four: Optional[str] = None
    billing_email: Optional[str] = None
    legacy_notes: Optional[str] = None


# For responses
class OrderDetails(Order):
    # Potentially include resolved Address and CreditCard info if needed, but be mindful of data exposure
    pass


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[UUID] = None
    is_admin: Optional[bool] = False
