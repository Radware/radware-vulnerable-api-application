from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict

# --- User Models ---


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    is_admin: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = None  # For admin privilege escalation demo


class UserInDBBase(UserBase):
    user_id: UUID = Field(default_factory=uuid4)
    password_hash: str
    is_protected: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Pydantic V2 config to allow ORM mode
    model_config = ConfigDict(from_attributes=True)


class User(UserBase):
    user_id: UUID
    is_protected: bool = False
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Address Models ---


class AddressBase(BaseModel):
    street: str
    city: str
    country: str
    zip_code: str
    is_default: bool = False


class AddressCreate(AddressBase):
    pass  # Inherits fields from AddressBase


class AddressUpdate(AddressBase):
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    is_default: Optional[bool] = None


class AddressInDBBase(AddressBase):
    address_id: UUID = Field(default_factory=uuid4)
    user_id: UUID  # Link to the user
    is_protected: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class Address(AddressBase):
    address_id: UUID
    user_id: UUID
    is_protected: bool = False
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Credit Card Models ---


# Base model for creating/updating - does NOT include sensitive info or DB-specific fields
class CreditCardBase(BaseModel):
    cardholder_name: str
    expiry_month: str = Field(..., pattern=r"^0[1-9]|1[0-2]$")
    expiry_year: str = Field(..., pattern=r"^20[2-9][0-9]$")
    is_default: bool = False


# Model for creating a new credit card - includes actual sensitive details for processing
class CreditCardCreate(CreditCardBase):
    card_number: str  # Actual card number - will be hashed and not stored directly
    cvv: Optional[str] = None  # CVV - will be hashed and not stored directly


# Model for updating existing credit card - sensitive details are NOT updated this way
class CreditCardUpdate(CreditCardBase):
    cardholder_name: Optional[str] = None
    expiry_month: Optional[str] = Field(None, pattern=r"^0[1-9]|1[0-2]$")
    expiry_year: Optional[str] = Field(None, pattern=r"^20[2-9][0-9]$")
    is_default: Optional[bool] = None


# Database model for credit cards - stores hashes and last four, plus DB info
class CreditCardInDBBase(BaseModel):
    card_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    card_number_hash: str  # Stored hash of the card number
    cvv_hash: Optional[str] = None  # Stored hash of the CVV
    card_last_four: str  # Last four digits of the card (for display)
    cardholder_name: str
    expiry_month: str
    expiry_year: str
    is_default: bool
    is_protected: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


# Public facing model for credit cards - excludes hashes, includes last four
class CreditCard(CreditCardBase):
    card_id: UUID
    user_id: UUID
    card_last_four: str  # Included for display
    is_protected: bool = False
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
