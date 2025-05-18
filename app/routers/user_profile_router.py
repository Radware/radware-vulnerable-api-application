from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from .. import db
from ..models.user_models import (Address, AddressCreate, AddressInDBBase, AddressUpdate,
                                CreditCard, CreditCardCreate, CreditCardInDBBase, CreditCardUpdate)
from ..models.order_models import TokenData # Using TokenData for current_user type hint
from ..routers.user_router import get_current_user # Reuse the dependency for authentication
from ..security import get_password_hash # For hashing card details

router = APIRouter(
    prefix="/users/{user_id}", # Common prefix for these routes
    tags=["User Profile"] # Grouping in OpenAPI docs
)

# --- Address Endpoints (BOLA Targets) --- 

@router.get("/addresses", response_model=List[Address])
async def list_user_addresses(
    user_id: UUID, 
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: Authenticated, but no check if current_user.user_id matches path user_id.
    # Any authenticated user can list addresses for any user_id specified in the path.
    print(f"Listing addresses for user {user_id}. Authenticated user: {current_user.user_id}. BOLA: No ownership check.")
    
    # Check if the user_id from path even exists
    path_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not path_user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found.")

    user_addresses = [Address.model_validate(a) for a in db.db["addresses"] if a.user_id == user_id]
    return user_addresses

@router.post("/addresses", response_model=Address, status_code=status.HTTP_201_CREATED)
async def create_user_address(
    user_id: UUID, # User ID from path
    street: str = Query(...),
    city: str = Query(...),
    country: str = Query(...),
    zip_code: str = Query(...),
    is_default: bool = Query(False),
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    # An authenticated user can create an address for another user.
    print(f"Creating address for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check.")

    path_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not path_user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found. Cannot create address.")

    address_data = AddressCreate(street=street, city=city, country=country, zip_code=zip_code, is_default=is_default)
    new_address = AddressInDBBase(**address_data.model_dump(), user_id=user_id) # Assign to user_id from path
    db.db["addresses"].append(new_address)
    return Address.model_validate(new_address)

@router.put("/addresses/{address_id}", response_model=Address)
async def update_user_address(
    user_id: UUID, # User ID from path
    address_id: UUID,
    street: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    is_default: Optional[bool] = Query(None),
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    # An authenticated user can update an address for another user.
    print(f"Updating address {address_id} for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check.")

    address_to_update = next((a for a in db.db["addresses"] if a.address_id == address_id and a.user_id == user_id), None)
    if not address_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found for this user or address ID is incorrect.")

    update_data = AddressUpdate(street=street, city=city, country=country, zip_code=zip_code, is_default=is_default).model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")

    for key, value in update_data.items():
        setattr(address_to_update, key, value)
    # address_to_update.updated_at = datetime.utcnow() # Assuming Address model has updated_at if needed
    return Address.model_validate(address_to_update)

@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_address(
    user_id: UUID, # User ID from path
    address_id: UUID,
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    print(f"Deleting address {address_id} for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check.")

    address_index = -1
    for i, a in enumerate(db.db["addresses"]):
        if a.address_id == address_id and a.user_id == user_id:
            address_index = i
            break
    
    if address_index == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found for this user or address ID is incorrect.")

    db.db["addresses"].pop(address_index)
    return

# --- Credit Card Endpoints (BOLA Targets) --- 

@router.get("/credit-cards", response_model=List[CreditCard])
async def list_user_credit_cards(
    user_id: UUID, 
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    print(f"Listing credit cards for user {user_id}. Authenticated user: {current_user.user_id}. BOLA: No ownership check.")
    
    path_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not path_user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found.")

    user_cards = [CreditCard.model_validate(cc) for cc in db.db["credit_cards"] if cc.user_id == user_id]
    return user_cards

@router.post("/credit-cards", response_model=CreditCard, status_code=status.HTTP_201_CREATED)
async def create_user_credit_card(
    user_id: UUID, # User ID from path
    cardholder_name: str = Query(...),
    # Actual card_number and cvv should be passed for hashing, not defined in OpenAPI query for brevity but handled here
    card_number: str = Query(..., description="Actual card number - will be hashed"),
    expiry_month: str = Query(..., pattern=r"^0[1-9]|1[0-2]$"),
    expiry_year: str = Query(..., pattern=r"^20[2-9][0-9]$"),
    cvv: Optional[str] = Query(None, description="CVV - will be hashed"), 
    is_default: bool = Query(False),
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    print(f"Creating credit card for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check.")

    path_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not path_user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found. Cannot create credit card.")

    # Extract last four digits before hashing
    card_last_four_digits = card_number[-4:]
    
    # Hash sensitive information
    card_number_hash = get_password_hash(card_number) # Using password hasher for simplicity
    cvv_hash = get_password_hash(cvv) if cvv else None

    card_data = CreditCardCreate(cardholder_name=cardholder_name, expiry_month=expiry_month, expiry_year=expiry_year, is_default=is_default, card_last_four=card_last_four_digits)
    new_card = CreditCardInDBBase(
        **card_data.model_dump(), 
        user_id=user_id, # Assign to user_id from path
        card_number_hash=card_number_hash, 
        cvv_hash=cvv_hash,
        card_last_four=card_last_four_digits
    )
    db.db["credit_cards"].append(new_card)
    return CreditCard.model_validate(new_card)

@router.put("/credit-cards/{card_id}", response_model=CreditCard)
async def update_user_credit_card(
    user_id: UUID, # User ID from path
    card_id: UUID,
    cardholder_name: Optional[str] = Query(None),
    expiry_month: Optional[str] = Query(None, pattern=r"^0[1-9]|1[0-2]$"),
    expiry_year: Optional[str] = Query(None, pattern=r"^20[2-9][0-9]$"),
    is_default: Optional[bool] = Query(None),
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    print(f"Updating credit card {card_id} for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check.")

    card_to_update = next((cc for cc in db.db["credit_cards"] if cc.card_id == card_id and cc.user_id == user_id), None)
    if not card_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit card not found for this user or card ID is incorrect.")

    update_data = CreditCardUpdate(cardholder_name=cardholder_name, expiry_month=expiry_month, expiry_year=expiry_year, is_default=is_default).model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")

    for key, value in update_data.items():
        setattr(card_to_update, key, value)
    # card_to_update.updated_at = datetime.utcnow() # Assuming model has updated_at if needed
    return CreditCard.model_validate(card_to_update)

@router.delete("/credit-cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_credit_card(
    user_id: UUID, # User ID from path
    card_id: UUID,
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    print(f"Deleting credit card {card_id} for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check.")

    card_index = -1
    for i, cc in enumerate(db.db["credit_cards"]):
        if cc.card_id == card_id and cc.user_id == user_id:
            card_index = i
            break
    
    if card_index == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit card not found for this user or card ID is incorrect.")

    db.db["credit_cards"].pop(card_index)
    return
