from typing import List

from pydantic import BaseModel, Field


class B2BPricingItem(BaseModel):
    sku: str
    retail_price: float = Field(..., ge=0)
    wholesale_price: float = Field(..., ge=0)


class B2BPartnerLookup(BaseModel):
    ref_code: str
    partner_name: str
    tier: str
    discount_percent: float = Field(..., ge=0)
    discount_floor_percent: float = Field(..., ge=0)
    contact_email: str
    billing_account_id: str
    pricing_snapshot: List[B2BPricingItem] = []
    legacy_notes: str
