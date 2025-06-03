from fastapi import APIRouter, HTTPException, status, Query, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from uuid import UUID, uuid4  # Import uuid4 for generating UUIDs
from datetime import datetime, timezone

from .. import db
from ..models.user_models import (
    User,
    UserCreate,
    UserInDBBase,
    UserUpdate,
    CreditCard,
    CreditCardCreate,
    CreditCardInDBBase, # Added this import
    CreditCardUpdate,  # Import CreditCard models
)
from ..security import get_password_hash, decode_access_token
from ..security import (
    hash_credit_card_data,
    verify_credit_card_cvv,
)  # Assuming these exist in security.py
from ..models.order_models import TokenData  # For current_user dependency

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)  # Updated tokenUrl for /api/ prefix


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: Optional[str] = payload.get("sub")
    user_id_val: Optional[UUID] = payload.get("user_id")
    is_admin_claim: Optional[bool] = payload.get("is_admin")

    if username is None or user_id_val is None:
        raise credentials_exception

    # If user_id_val is a string, convert to UUID; if already UUID, use as is
    if isinstance(user_id_val, str):
        try:
            user_id = UUID(user_id_val)
        except ValueError:
            raise credentials_exception
    elif isinstance(user_id_val, UUID):
        user_id = user_id_val
    else:
        raise credentials_exception

    user = db.db_users_by_id.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )  # Changed to 401 for consistency
    return TokenData(
        username=user.username,
        user_id=user.user_id,
        is_admin=is_admin_claim if is_admin_claim is not None else False,
    )


# --- User Endpoints ---


# According to OpenAPI, /users POST is for creating a user with query params.
# This is similar to /auth/register. For now, implementing as per OpenAPI.
@router.post(
    "/users", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users"]
)
async def create_user_endpoint(
    username: str = Query(...),
    email: str = Query(...),
    password: str = Query(...),
    # is_admin: bool = Query(False) # OpenAPI doesn't list is_admin for this initial creation via /users
):
    existing_user_by_username = db.db_users_by_username.get(username)
    if existing_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' already registered",
        )
    existing_user_by_email = db.db_users_by_email.get(email)
    if existing_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{email}' already registered",
        )

    hashed_password = get_password_hash(password)
    new_user = UserInDBBase(
        username=username, email=email, password_hash=hashed_password, is_admin=False
    )
    db.db["users"].append(new_user) # Keep for now if other parts of code rely on it
    db.db_users_by_id[new_user.user_id] = new_user
    db.db_users_by_username[new_user.username] = new_user
    db.db_users_by_email[new_user.email] = new_user
    return User.model_validate(new_user)


@router.get("/users/{user_id}", response_model=User, tags=["Users"])
async def get_user_by_id(
    user_id: UUID,
    # current_user: TokenData = Depends(get_current_user) # BOLA: No check initially
):
    user = db.db_users_by_id.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    # BOLA vulnerability: Any authenticated user can access any user's details by ID.
    # No check if current_user.user_id matches user_id from path.
    return User.model_validate(user)


@router.put("/users/{user_id}", response_model=User, tags=["Users"])
async def update_user(
    user_id: UUID,
    username: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    is_admin_param: Optional[bool] = Query(
        None, alias="is_admin"
    ),  # Parameter pollution target
    # current_user: TokenData = Depends(get_current_user) # BOLA: No check initially
):
    user_to_update = db.db_users_by_id.get(user_id)
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if hasattr(user_to_update, "is_protected") and user_to_update.is_protected:
        username_change = username is not None and username != user_to_update.username
        if username_change:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"User '{user_to_update.username}' is protected. Username cannot be changed. Other fields can be modified."
                ),
            )

    update_data = {}
    if username is not None:
        existing_username_user = db.db_users_by_username.get(username)
        if existing_username_user and existing_username_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{username}' already in use.",
            )
        update_data["username"] = username
    if email is not None:
        existing_email_user = db.db_users_by_email.get(email)
        if existing_email_user and existing_email_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{email}' already in use.",
            )
        update_data["email"] = email

    if is_admin_param is not None:
        print(
            f"Attempting to set is_admin to: {is_admin_param} for user {user_id} via query parameter."
        )
        update_data["is_admin"] = is_admin_param

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided"
        )

    old_username = user_to_update.username
    old_email = user_to_update.email
    for key, value in update_data.items():
        setattr(user_to_update, key, value)
    user_to_update.updated_at = datetime.now(timezone.utc)

    if "username" in update_data and update_data["username"] != old_username :
        db.db_users_by_username.pop(old_username, None)
        db.db_users_by_username[user_to_update.username] = user_to_update
    if "email" in update_data and update_data["email"] != old_email:
        db.db_users_by_email.pop(old_email, None)
        db.db_users_by_email[user_to_update.email] = user_to_update
    
    # db.db_users_by_id already holds the updated user_to_update object reference

    return User.model_validate(user_to_update)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    tags=["Users"],
    response_model=dict,
)
async def delete_user(
    user_id: UUID,
):
    user_to_delete = db.db_users_by_id.get(user_id)
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if hasattr(user_to_delete, "is_protected") and user_to_delete.is_protected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"User '{user_to_delete.username}' is protected for demo purposes and cannot be deleted. "
                "Please try with a non-protected user or one you created."
            ),
        )

    print(
        f"User {user_id} being deleted. Intended BFLA: No admin check performed."
    )
    
    # Remove from old list-based storage if it's still populated
    if user_to_delete in db.db["users"]:
        db.db["users"].remove(user_to_delete)
        
    # Remove from new dictionary-based indexes
    db.db_users_by_id.pop(user_id, None)
    db.db_users_by_username.pop(user_to_delete.username, None)
    db.db_users_by_email.pop(user_to_delete.email, None)

    # Remove associated addresses
    user_addresses_to_remove = db.db_addresses_by_user_id.pop(user_id, [])
    for addr in user_addresses_to_remove:
        db.db_addresses_by_id.pop(addr.address_id, None)
        if addr in db.db["addresses"]: # Remove from old list if present
            db.db["addresses"].remove(addr)


    # Remove associated credit cards
    user_cards_to_remove = db.db_credit_cards_by_user_id.pop(user_id, [])
    for card in user_cards_to_remove:
        db.db_credit_cards_by_id.pop(card.card_id, None)
        if card in db.db["credit_cards"]: # Remove from old list if present
            db.db["credit_cards"].remove(card)

    return {"message": "User deleted successfully"}


@router.get("/users", response_model=List[User], tags=["Users"])
async def list_users(current_user: TokenData = Depends(get_current_user)):
    """Get a list of all users - intentionally vulnerable for demonstration purposes.
    In a real application, this would be restricted to admins or have proper filtering.
    """
    print(
        f"User {current_user.username} (ID: {current_user.user_id}) is listing all users. Intentional vulnerability for demo."
    )
    return [User.model_validate(u) for u in db.db_users_by_id.values()]


## Credit Card Endpoints ##
# Note: These endpoints are defined here but the OpenAPI spec and user_profile_router.py
# place them under "/users/{user_id}/credit-cards".
# Assuming the user_profile_router.py is the one being actively used and refactored.
# If these are also active and need fixing, the same logic from user_profile_router.py should be applied here.

@router.get(
    "/users/{user_id}/credit-cards",
    response_model=List[CreditCard],
    tags=["Credit Cards"], # Changed tag to match user_profile_router
)
async def list_user_credit_cards(user_id: UUID): # Removed Depends(get_current_user) to match observed BOLA
    """List all credit cards for a specific user.
    BOLA Vulnerability: No ownership check.
    """
    user_exists = db.db_users_by_id.get(user_id)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user_card_objects = db.db_credit_cards_by_user_id.get(user_id, [])
    user_credit_cards = [CreditCard.model_validate(cc) for cc in user_card_objects]
    print(
        f"User {user_id} credit cards being listed. Intended BOLA: No owner check performed."
    )
    return user_credit_cards


@router.get(
    "/users/{user_id}/credit-cards/{card_id}",
    response_model=CreditCard,
    tags=["Credit Cards"], # Changed tag
)
async def get_user_credit_card_by_id(user_id: UUID, card_id: UUID): # Removed Depends(get_current_user)
    """Get a specific credit card by ID for a given user."""
    user_exists = db.db_users_by_id.get(user_id)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    credit_card = db.db_credit_cards_by_id.get(card_id)
    if not credit_card or credit_card.user_id != user_id: # Check ownership against path user_id
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit card not found for this user.",
        )
    return CreditCard.model_validate(credit_card)


@router.post(
    "/users/{user_id}/credit-cards",
    response_model=CreditCard,
    status_code=status.HTTP_201_CREATED,
    tags=["Credit Cards"], # Changed tag
)
async def add_credit_card_to_user( # Removed Depends(get_current_user)
    user_id: UUID,
    cardholder_name: str = Query(..., description="Name of the cardholder"),
    card_number: str = Query(
        ..., min_length=13, max_length=19, description="Full credit card number"
    ),
    expiry_month: str = Query(
        ..., pattern=r"^0[1-9]|1[0-2]$", description="Expiry month (MM)"
    ),
    expiry_year: str = Query(
        ..., pattern=r"^20[2-9][0-9]$", description="Expiry year (YYYY)"
    ),
    cvv: Optional[str] = Query(
        None, min_length=3, max_length=4, description="Card Verification Value"
    ),
    is_default: bool = Query(
        False, description="Whether this is the default credit card"
    ),
):
    """Add a new credit card to a user's profile via query parameters."""
    user_exists = db.db_users_by_id.get(user_id)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    card_data = CreditCardCreate(
        cardholder_name=cardholder_name,
        card_number=card_number,
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        cvv=cvv,
        is_default=is_default,
    )

    card_number_hash = hash_credit_card_data(card_data.card_number) # Uses security.hash_credit_card_data
    cvv_hash = hash_credit_card_data(card_data.cvv) if card_data.cvv else None
    card_last_four = card_data.card_number[-4:]

    new_card_in_db = CreditCardInDBBase( # Explicitly use CreditCardInDBBase from user_models
        user_id=user_id,
        cardholder_name=card_data.cardholder_name,
        expiry_month=card_data.expiry_month,
        expiry_year=card_data.expiry_year,
        is_default=card_data.is_default,
        card_number_hash=card_number_hash,
        card_last_four=card_last_four,
        cvv_hash=cvv_hash,
        is_protected=False, # New cards are not protected by default
    )
    
    db.db_credit_cards_by_id[new_card_in_db.card_id] = new_card_in_db
    db.db_credit_cards_by_user_id.setdefault(user_id, []).append(new_card_in_db)
    if new_card_in_db not in db.db["credit_cards"]: # Add to old list if not already there (idempotency)
         db.db["credit_cards"].append(new_card_in_db)


    user_cards = db.db_credit_cards_by_user_id.get(user_id, [])
    if len(user_cards) == 1: # If this is the first card
        new_card_in_db.is_default = True
    elif is_default: # If this card is marked as default
        for card_item in user_cards:
            if card_item.card_id != new_card_in_db.card_id:
                card_item.is_default = False
        new_card_in_db.is_default = True # Ensure the new card is set
        
    print(
        f"Credit card added for user {user_id}. Intended BOLA: No owner check performed."
    )
    return CreditCard.model_validate(new_card_in_db)


@router.put(
    "/users/{user_id}/credit-cards/{card_id}",
    response_model=CreditCard,
    tags=["Credit Cards"], # Changed tag
)
async def update_user_credit_card( # Removed Depends(get_current_user)
    user_id: UUID,
    card_id: UUID,
    cardholder_name: Optional[str] = Query(None, description="Name of the cardholder"),
    expiry_month: Optional[str] = Query(
        None, pattern=r"^0[1-9]|1[0-2]$", description="Expiry month (MM)"
    ),
    expiry_year: Optional[str] = Query(
        None, pattern=r"^20[2-9][0-9]$", description="Expiry year (YYYY)"
    ),
    is_default: Optional[bool] = Query(
        None, description="Whether this is the default credit card"
    ),
):
    """Update an existing credit card's details for a user."""
    user_exists = db.db_users_by_id.get(user_id)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    credit_card_to_update = db.db_credit_cards_by_id.get(card_id)
    if not credit_card_to_update or credit_card_to_update.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit card not found for this user.",
        )

    owner_user: Optional[UserInDBBase] = db.db_users_by_id.get(user_id) # Already got user_exists
    # No need for this check if user_exists is confirmed:
    # if not owner_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found."
    #     )

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

    for key, value in update_data_dict.items():
        setattr(credit_card_to_update, key, value)

    if update_data_dict.get("is_default") is True:
        for card_item in db.db_credit_cards_by_user_id.get(user_id, []):
            if card_item.card_id != card_id:
                card_item.is_default = False
        credit_card_to_update.is_default = True # Ensure target card is set

    credit_card_to_update.updated_at = datetime.now(timezone.utc)
    print(
        f"Credit card {card_id} for user {user_id} updated. Intended BOLA: No owner check performed."
    )
    return CreditCard.model_validate(credit_card_to_update)


@router.delete(
    "/users/{user_id}/credit-cards/{card_id}",
    status_code=status.HTTP_200_OK,
    tags=["Credit Cards"], # Changed tag
    response_model=dict,
)
async def delete_user_credit_card(user_id: UUID, card_id: UUID): # Removed Depends(get_current_user)
    """Delete a specific credit card for a given user."""
    user_exists = db.db_users_by_id.get(user_id)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    card_to_delete = db.db_credit_cards_by_id.get(card_id)
    if not card_to_delete or card_to_delete.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit card not found for this user.",
        )

    owner_user = db.db_users_by_id.get(user_id) # user_exists is already owner_user
    if owner_user and owner_user.is_protected:
        remaining = db.db_credit_cards_by_user_id.get(user_id, [])
        if len(remaining) <= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Protected user '{owner_user.username}' must have at least one credit card. "
                    "Cannot delete the last one."
                ),
            )

    was_default = card_to_delete.is_default

    if card_to_delete in db.db["credit_cards"]:
        db.db["credit_cards"].remove(card_to_delete)
    db.db_credit_cards_by_id.pop(card_id, None)
    user_card_list = db.db_credit_cards_by_user_id.get(user_id, [])
    if card_to_delete in user_card_list:
        user_card_list.remove(card_to_delete)
        if not user_card_list:
            db.db_credit_cards_by_user_id.pop(user_id, None)


    if was_default:
        remaining_user_cards = db.db_credit_cards_by_user_id.get(user_id, [])
        if remaining_user_cards and not any(c.is_default for c in remaining_user_cards):
            remaining_user_cards[0].is_default = True
            print(
                f"Card {remaining_user_cards[0].card_id} made default for user {user_id} after deleting previous default."
            )

    print(
        f"Credit card {card_id} for user {user_id} deleted. Intended BOLA: No owner check performed."
    )
    return {"message": "Credit card deleted successfully"}