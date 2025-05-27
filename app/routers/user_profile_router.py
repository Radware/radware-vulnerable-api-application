from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Query,
    Depends,
    Body,
)  # Ensure Body is imported
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from .. import db
from ..models.user_models import (
    Address,
    AddressCreate,
    AddressInDBBase,
    AddressUpdate,
    CreditCard,
    CreditCardCreate,
    CreditCardInDBBase,
    CreditCardUpdate,
)
from ..models.order_models import (
    TokenData,
)  # Using TokenData for current_user type hint
from ..routers.user_router import (
    get_current_user,
)  # Reuse the dependency for authentication
from ..security import get_password_hash  # For hashing card details

router = APIRouter(
    prefix="/users/{user_id}",  # Common prefix for these routes
    tags=["User Profile"],  # Grouping in OpenAPI docs
)

# --- Address Endpoints (BOLA Targets - for demonstration) ---


@router.get("/addresses", response_model=List[Address])
async def list_user_addresses(
    user_id: UUID, current_user: TokenData = Depends(get_current_user)
):
    """
    Get a list of all addresses for a specific user.
    BOLA Vulnerability: Authenticated, but no check if current_user.user_id matches path user_id.
    Any authenticated user can list addresses for any user_id specified in the path.
    """
    print(
        f"Listing addresses for user {user_id}. Authenticated user: {current_user.user_id}. BOLA: No ownership check."
    )

    # Check if the user_id from path even exists
    path_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not path_user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    user_addresses = [
        Address.model_validate(a) for a in db.db["addresses"] if a.user_id == user_id
    ]
    return user_addresses


@router.post("/addresses", response_model=Address, status_code=status.HTTP_201_CREATED)
async def create_user_address(
    user_id: UUID,  # User ID from path
    street: str = Query(...),
    city: str = Query(...),
    country: str = Query(...),
    zip_code: str = Query(...),
    is_default: bool = Query(False),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new address for a specific user.
    BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    An authenticated user can create an address for another user.
    """
    print(
        f"Creating address for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check."
    )

    path_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not path_user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found. Cannot create address.",
        )

    duplicate = next(
        (
            a
            for a in db.db["addresses"]
            if a.user_id == user_id
            and a.street == street
            and a.city == city
            and a.country == country
            and a.zip_code == zip_code
        ),
        None,
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Address already exists for this user.",
        )

    address_data = AddressCreate(
        street=street,
        city=city,
        country=country,
        zip_code=zip_code,
        is_default=is_default,
    )
    new_address = AddressInDBBase(
        **address_data.model_dump(),
        user_id=user_id,
        is_protected=False,
    )
    db.db["addresses"].append(new_address)
    return Address.model_validate(new_address)


@router.put("/addresses/{address_id}", response_model=Address)
async def update_user_address(
    user_id: UUID,  # User ID from path
    address_id: UUID,
    street: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    is_default: Optional[bool] = Query(None),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Update an existing address for a specific user.
    BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    An authenticated user can update an address for another user.
    """
    print(
        f"Updating address {address_id} for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check."
    )

    address_to_update = next(
        (
            a
            for a in db.db["addresses"]
            if a.address_id == address_id and a.user_id == user_id
        ),
        None,
    )
    if not address_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found for this user or address ID is incorrect.",
        )

    if hasattr(address_to_update, "is_protected") and address_to_update.is_protected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Address ID '{address_id}' is protected and cannot be modified. "
                "Try with a non-protected address."
            ),
        )

    update_data = AddressUpdate(
        street=street,
        city=city,
        country=country,
        zip_code=zip_code,
        is_default=is_default,
    ).model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided"
        )

    for key, value in update_data.items():
        setattr(address_to_update, key, value)
    return Address.model_validate(address_to_update)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_address(
    user_id: UUID,  # User ID from path
    address_id: UUID,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete an address for a specific user.
    BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    An authenticated user can delete an address for another user.
    """
    print(
        f"Deleting address {address_id} for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check."
    )

    address_index = -1
    address_to_delete = None
    for i, a in enumerate(db.db["addresses"]):
        if a.address_id == address_id and a.user_id == user_id:
            address_index = i
            address_to_delete = a
            break

    if address_index == -1 or address_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found for this user or address ID is incorrect.",
        )

    if hasattr(address_to_delete, "is_protected") and address_to_delete.is_protected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Address ID '{address_id}' is protected and cannot be deleted. "
                "Try with a non-protected address."
            ),
        )

    db.db["addresses"].pop(address_index)
    return


# --- Credit Card Endpoints (BOLA Targets - for demonstration) ---


@router.get("/credit-cards", response_model=List[CreditCard])
async def list_user_credit_cards(
    user_id: UUID, current_user: TokenData = Depends(get_current_user)
):
    """
    Get a list of all credit cards for a specific user.
    BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    Any authenticated user can list credit cards for any user_id specified in the path.
    """
    print(
        f"Listing credit cards for user {user_id}. Authenticated user: {current_user.user_id}. BOLA: No ownership check."
    )

    path_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not path_user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    user_cards = [
        CreditCard.model_validate(cc)
        for cc in db.db["credit_cards"]
        if cc.user_id == user_id
    ]
    return user_cards


@router.post(
    "/credit-cards", response_model=CreditCard, status_code=status.HTTP_201_CREATED
)
async def create_user_credit_card(
    user_id: UUID,  # User ID from path
    cardholder_name: str = Query(...),
    card_number: str = Query(...),  # Actual card number
    expiry_month: str = Query(..., pattern=r"^0[1-9]|1[0-2]$"),
    expiry_year: str = Query(..., pattern=r"^20[2-9][0-9]$"),
    cvv: Optional[str] = Query(None),
    is_default: bool = Query(False),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new credit card for a specific user using query parameters.
    BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    An authenticated user can create a credit card for another user.
    """
    print(
        f"Creating credit card for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check."
    )

    path_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not path_user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found. Cannot create credit card.",
        )

    # Create a CreditCardCreate instance from query parameters for consistent validation and data processing
    try:
        card_data_from_query = CreditCardCreate(
            cardholder_name=cardholder_name,
            card_number=card_number,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
            is_default=is_default,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error for query parameters: {e}",
        )

    # Extract last four digits before hashing
    card_last_four_digits = card_data_from_query.card_number[-4:]

    # Hash sensitive information
    card_number_hash = get_password_hash(card_data_from_query.card_number)
    cvv_hash = (
        get_password_hash(card_data_from_query.cvv)
        if card_data_from_query.cvv
        else None
    )

    new_card = CreditCardInDBBase(
        # Pass fields from the validated card_data_from_query (excluding sensitive ones)
        cardholder_name=card_data_from_query.cardholder_name,
        expiry_month=card_data_from_query.expiry_month,
        expiry_year=card_data_from_query.expiry_year,
        is_default=card_data_from_query.is_default,
        user_id=user_id,  # Assign to user_id from path
        card_number_hash=card_number_hash,
        cvv_hash=cvv_hash,
        card_last_four=card_last_four_digits,
        is_protected=False,
    )
    db.db["credit_cards"].append(new_card)
    return CreditCard.model_validate(new_card)


@router.put("/credit-cards/{card_id}", response_model=CreditCard)
async def update_user_credit_card(
    user_id: UUID,  # User ID from path
    card_id: UUID,
    cardholder_name: Optional[str] = Query(None),
    expiry_month: Optional[str] = Query(None, pattern=r"^0[1-9]|1[0-2]$"),
    expiry_year: Optional[str] = Query(None, pattern=r"^20[2-9][0-9]$"),
    is_default: Optional[bool] = Query(None),
    # Note: Card number and CVV are typically not updated via PUT.
    # If you need to allow changing them, it's usually via a new card or a separate process.
    current_user: TokenData = Depends(get_current_user),
):
    """
    Update an existing credit card for a specific user using query parameters.
    BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    An authenticated user can update a credit card for another user.
    """
    print(
        f"Updating credit card {card_id} for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check."
    )

    card_to_update = next(
        (
            cc
            for cc in db.db["credit_cards"]
            if cc.card_id == card_id and cc.user_id == user_id
        ),
        None,
    )
    if not card_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit card not found for this user or card ID is incorrect.",
        )

    # Manually collect update data from query parameters
    update_data = {}
    if cardholder_name is not None:
        update_data["cardholder_name"] = cardholder_name
    if expiry_month is not None:
        update_data["expiry_month"] = expiry_month
    if expiry_year is not None:
        update_data["expiry_year"] = expiry_year
    if is_default is not None:
        update_data["is_default"] = is_default

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided"
        )

    if hasattr(card_to_update, "is_protected") and card_to_update.is_protected:
        if (
            str(card_to_update.card_id) == "cc000003-0002-0000-0000-000000000002"
            and str(user_id) == "00000003-0000-0000-0000-000000000003"
        ):
            allowed_updates = {}
            if "expiry_year" in update_data and update_data["expiry_year"] == "2031":
                allowed_updates["expiry_year"] = "2031"
            if "is_default" in update_data and update_data["is_default"] is True:
                allowed_updates["is_default"] = True
            if len(allowed_updates) == len(update_data) and len(update_data) > 0:
                for key, value in allowed_updates.items():
                    setattr(card_to_update, key, value)
                card_to_update.updated_at = datetime.now(timezone.utc)
                return CreditCard.model_validate(card_to_update)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "For this protected card (Bob's demo card), only specific updates "
                    "(expiry_year to 2031, is_default to true) are permitted for the demo flow."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Credit Card ID '{card_id}' is protected and cannot be modified. "
                "Try with a non-protected card."
            ),
        )

    # Apply updates to the found card
    for key, value in update_data.items():
        setattr(card_to_update, key, value)
    card_to_update.updated_at = datetime.now(timezone.utc)  # Update timestamp
    return CreditCard.model_validate(card_to_update)


@router.delete("/credit-cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_credit_card(
    user_id: UUID,  # User ID from path
    card_id: UUID,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete a credit card for a specific user.
    BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    An authenticated user can delete a credit card for another user.
    """
    print(
        f"Deleting credit card {card_id} for user {user_id} by authenticated user {current_user.user_id}. BOLA: No ownership check."
    )

    card_index = -1
    card_to_delete = None
    for i, cc in enumerate(db.db["credit_cards"]):
        if cc.card_id == card_id and cc.user_id == user_id:
            card_index = i
            card_to_delete = cc
            break

    if card_index == -1 or card_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit card not found for this user or card ID is incorrect.",
        )

    if hasattr(card_to_delete, "is_protected") and card_to_delete.is_protected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Credit Card ID '{card_id}' is protected and cannot be deleted. "
                "Try with a non-protected card."
            ),
        )

    db.db["credit_cards"].pop(card_index)
    return
