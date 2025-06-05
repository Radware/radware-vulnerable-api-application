from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class CouponBase(BaseModel):
    """Base fields shared by coupon models."""

    code: str = Field(..., min_length=1)
    discount_type: str
    discount_value: float = Field(..., gt=0)
    is_active: bool = True
    usage_limit: Optional[int] = None
    expiration_date: Optional[datetime] = None


class CouponCreate(CouponBase):
    """Model for creating a new coupon."""

    pass


class CouponInDBBase(CouponBase):
    """Representation of a coupon stored in the database."""

    coupon_id: UUID = Field(default_factory=uuid4)
    usage_count: int = 0
    is_protected: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"from_attributes": True}


class Coupon(CouponInDBBase):
    """Public facing coupon model."""

    pass
