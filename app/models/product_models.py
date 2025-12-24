from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductInDBBase(ProductBase):
    product_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    internal_status: Optional[str] = None  # For parameter pollution
    is_protected: bool = False

    model_config = {"from_attributes": True}


class Product(ProductInDBBase):
    pass


class ProductWithStock(ProductInDBBase):
    stock_quantity: int = Field(..., ge=0)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    internal_status: Optional[str] = None  # For parameter pollution vulnerability


class StockBase(BaseModel):
    quantity: int = Field(..., ge=0)


class StockCreate(StockBase):
    product_id: UUID  # Will be linked from path or product creation


class StockInDBBase(StockBase):
    product_id: UUID  # Serves as FK and part of PK if we consider it unique per product
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"from_attributes": True}


class Stock(StockInDBBase):
    pass


class StockUpdate(BaseModel):
    quantity: int = Field(..., ge=0)
