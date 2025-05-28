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

    path_user: Optional[UserInDBBase] = next(
        (u for u in db.db["users"] if u.user_id == user_id), None
    )
    if not path_user:
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

    if is_default:
        for addr_item in db.db["addresses"]:
            if addr_item.user_id == user_id:
                addr_item.is_default = False

    new_address_db = AddressInDBBase(
        **address_data.model_dump(),
        user_id=user_id,
        is_protected=False,
    )
    db.db["addresses"].append(new_address_db)
    return Address.model_validate(new_address_db)


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

    owner_user: Optional[UserInDBBase] = next(
        (u for u in db.db["users"] if u.user_id == user_id), None
    )
    if not owner_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found."
        )

    # If is_default is being set to True, all other addresses for this user will
    # be un-defaulted. Previous restrictions around un-defaulting item.is_protected
    # defaults have been removed.

    update_data_dict = {}
    if street is not None:
        update_data_dict["street"] = street
    if city is not None:
        update_data_dict["city"] = city
    if country is not None:
        update_data_dict["country"] = country
    if zip_code is not None:
        update_data_dict["zip_code"] = zip_code
    if is_default is not None:
        update_data_dict["is_default"] = is_default
    if not update_data_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided"
        )

    for key, value in update_data_dict.items():
        setattr(address_to_update, key, value)

    if is_default is True:
        for addr_item in db.db["addresses"]:
            if addr_item.user_id == user_id and addr_item.address_id != address_id:
                addr_item.is_default = False

    address_to_update.updated_at = datetime.now(timezone.utc)
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

    owner_user = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if owner_user and owner_user.is_protected:
        remaining = [a for a in db.db["addresses"] if a.user_id == user_id]
        if len(remaining) <= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Protected user '{owner_user.username}' must have at least one address. "
                    "Cannot delete the last one."
                ),
            )

    was_default = address_to_delete.is_default
    db.db["addresses"].pop(address_index)

    if was_default:
        remaining_user_addresses = [
            a for a in db.db["addresses"] if a.user_id == user_id
        ]
        if remaining_user_addresses and not any(
            a.is_default for a in remaining_user_addresses
        ):
            non_item_protected_remaining = [
                a
                for a in remaining_user_addresses
                if not (hasattr(a, "is_protected") and a.is_protected)
            ]
            if non_item_protected_remaining:
                non_item_protected_remaining[0].is_default = True
                print(
                    f"Address {non_item_protected_remaining[0].address_id} made default for user {user_id} after deleting previous default."
                )
            else:
                remaining_user_addresses[0].is_default = True
                print(
                    f"Address {remaining_user_addresses[0].address_id} (item.is_protected) made default for user {user_id} after deleting previous default."
                )
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

    path_user: Optional[UserInDBBase] = next(
        (u for u in db.db["users"] if u.user_id == user_id), None
    )
    if not path_user:
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

    if is_default:
        for card_item in db.db["credit_cards"]:
            if card_item.user_id == user_id:
                card_item.is_default = False

    card_last_four_digits = card_data_from_query.card_number[-4:]
    card_number_hash = get_password_hash(card_data_from_query.card_number)
    cvv_hash = (
        get_password_hash(card_data_from_query.cvv)
        if card_data_from_query.cvv
        else None
    )

    new_card_db = CreditCardInDBBase(
        cardholder_name=card_data_from_query.cardholder_name,
        expiry_month=card_data_from_query.expiry_month,
        expiry_year=card_data_from_query.expiry_year,
        is_default=card_data_from_query.is_default,
        user_id=user_id,
        card_number_hash=card_number_hash,
        cvv_hash=cvv_hash,
        card_last_four=card_last_four_digits,
        is_protected=False,
    )
    db.db["credit_cards"].append(new_card_db)
    return CreditCard.model_validate(new_card_db)


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

    owner_user: Optional[UserInDBBase] = next(
        (u for u in db.db["users"] if u.user_id == user_id), None
    )
    if not owner_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found."
        )

    update_data_dict = {}
    if cardholder_name is not None:
        update_data_dict["cardholder_name"] = cardholder_name
    if expiry_month is not None:
        update_data_dict["expiry_month"] = expiry_month
    if expiry_year is not None:
        update_data_dict["expiry_year"] = expiry_year
    if is_default is not None:
        update_data_dict["is_default"] = is_default

    if not update_data_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided"
        )

    if hasattr(card_to_update, "is_protected") and card_to_update.is_protected:
        if (
            str(card_to_update.card_id) == "cc000003-0002-0000-0000-000000000002"
            and str(user_id) == "00000003-0000-0000-0000-000000000003"
        ):
            allowed_updates_for_bob_card = {}
            if (
                "expiry_year" in update_data_dict
                and update_data_dict["expiry_year"] == "2031"
            ):
                allowed_updates_for_bob_card["expiry_year"] = "2031"
            if (
                "is_default" in update_data_dict
                and update_data_dict["is_default"] is True
            ):
                allowed_updates_for_bob_card["is_default"] = True

            is_subset = all(
                key in allowed_updates_for_bob_card for key in update_data_dict
            )

            if not is_subset or not update_data_dict:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "For this protected card (Bob's demo card), only specific updates "
                        "(expiry_year to 2031, is_default to true) are permitted for the demo flow."
                    ),
                )
            update_data_dict = allowed_updates_for_bob_card
        else:
            pass  # Other protected cards can now be modified

    # If is_default is True, we simply make this card default and un-default all
    # other cards for the user. Previous restrictions on un-defaulting
    # item.is_protected defaults have been removed.

    for key, value in update_data_dict.items():
        setattr(card_to_update, key, value)

    if update_data_dict.get("is_default") is True:
        for card_item in db.db["credit_cards"]:
            if card_item.user_id == user_id and card_item.card_id != card_id:
                card_item.is_default = False

    card_to_update.updated_at = datetime.now(timezone.utc)
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

    owner_user = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if owner_user and owner_user.is_protected:
        remaining = [cc for cc in db.db["credit_cards"] if cc.user_id == user_id]
        if len(remaining) <= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Protected user '{owner_user.username}' must have at least one credit card. "
                    "Cannot delete the last one."
                ),
            )

    was_default = card_to_delete.is_default
    db.db["credit_cards"].pop(card_index)

    if was_default:
        remaining_user_cards = [
            cc for cc in db.db["credit_cards"] if cc.user_id == user_id
        ]
        if remaining_user_cards and not any(c.is_default for c in remaining_user_cards):
            non_item_protected_remaining_cards = [
                c
                for c in remaining_user_cards
                if not (hasattr(c, "is_protected") and c.is_protected)
            ]
            if non_item_protected_remaining_cards:
                non_item_protected_remaining_cards[0].is_default = True
                print(
                    f"Card {non_item_protected_remaining_cards[0].card_id} made default for user {user_id} after deleting previous default."
                )
            else:
                remaining_user_cards[0].is_default = True
                print(
                    f"Card {remaining_user_cards[0].card_id} (item.is_protected) made default for user {user_id} after deleting previous default."
                )
    return
