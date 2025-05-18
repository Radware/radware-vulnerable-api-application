from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_admin: bool = False

class UserCreate(UserBase):
    password: str # This will be used for creation, then hashed

class UserInDBBase(UserBase):
    user_id: UUID = Field(default_factory=uuid4)
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"from_attributes": True}

class User(UserInDBBase):
    pass

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = None # For parameter pollution vulnerability
    # Password updates would typically be a separate, more secure process

class AddressBase(BaseModel):
    street: str
    city: str
    country: str
    zip_code: str
    is_default: bool = False

class AddressCreate(AddressBase):
    pass # user_id will be added from path

class AddressInDBBase(AddressBase):
    address_id: UUID = Field(default_factory=uuid4)
    user_id: UUID

    model_config = {"from_attributes": True}

class Address(AddressInDBBase):
    pass

class AddressUpdate(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    is_default: Optional[bool] = None

class CreditCardBase(BaseModel):
    cardholder_name: str
    expiry_month: str = Field(..., pattern=r"^0[1-9]|1[0-2]$") # MM
    expiry_year: str = Field(..., pattern=r"^20[2-9][0-9]$") # YYYY (e.g., 2024-2099)
    is_default: bool = False
    card_last_four: Optional[str] = Field(None, description="Last four digits of the card number for display purposes")

class CreditCardCreate(CreditCardBase):
    # card_number and cvv will be passed in, hashed, and not stored directly in this model
    # user_id will be added from path
    pass

class CreditCardInDBBase(CreditCardBase):
    card_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    card_number_hash: str
    card_last_four: str
    cvv_hash: Optional[str] = None # CVV not typically stored, but hash for realism

    model_config = {"from_attributes": True}

class CreditCard(CreditCardInDBBase):
    pass

class CreditCardUpdate(BaseModel):
    cardholder_name: Optional[str] = None
    expiry_month: Optional[str] = Field(None, pattern=r"^0[1-9]|1[0-2]$")
    expiry_year: Optional[str] = Field(None, pattern=r"^20[2-9][0-9]$")
    is_default: Optional[bool] = None
