from fastapi import APIRouter, HTTPException, status, Query, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from uuid import UUID, uuid4 # Import uuid4 for generating UUIDs
from datetime import datetime, timezone

from .. import db
from ..models.user_models import (
    User, UserCreate, UserInDBBase, UserUpdate,
    CreditCard, CreditCardCreate, CreditCardUpdate # Import CreditCard models
)
from ..security import get_password_hash, decode_access_token, SECRET_KEY, ALGORITHM
from ..security import hash_credit_card_data, verify_credit_card_cvv # Assuming these exist in security.py
from ..models.order_models import TokenData # For current_user dependency

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") # Updated tokenUrl for /api/ prefix

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

    user = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found") # Changed to 401 for consistency
    return TokenData(username=user.username, user_id=user.user_id)

# --- User Endpoints ---

# According to OpenAPI, /users POST is for creating a user with query params.
# This is similar to /auth/register. For now, implementing as per OpenAPI.
@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user_endpoint(
    username: str = Query(...),
    email: str = Query(...),
    password: str = Query(...)
    # is_admin: bool = Query(False) # OpenAPI doesn't list is_admin for this initial creation via /users
):
    existing_user_by_username = next((u for u in db.db["users"] if u.username == username), None)
    if existing_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' already registered"
        )
    existing_user_by_email = next((u for u in db.db["users"] if u.email == email), None)
    if existing_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{email}' already registered"
        )

    hashed_password = get_password_hash(password)
    new_user = UserInDBBase(username=username, email=email, password_hash=hashed_password, is_admin=False)
    db.db["users"].append(new_user)
    return User.model_validate(new_user)

@router.get("/users/{user_id}", response_model=User, tags=["Users"])
async def get_user_by_id(
    user_id: UUID,
    # current_user: TokenData = Depends(get_current_user) # BOLA: No check initially
):
    user = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # BOLA vulnerability: Any authenticated user can access any user's details by ID.
    # No check if current_user.user_id matches user_id from path.
    return User.model_validate(user)

@router.put("/users/{user_id}", response_model=User, tags=["Users"])
async def update_user(
    user_id: UUID,
    email: Optional[str] = Query(None),
    is_admin_param: Optional[bool] = Query(None, alias="is_admin"), # Parameter pollution target
    # current_user: TokenData = Depends(get_current_user) # BOLA: No check initially
):
    user_to_update = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not user_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # BOLA: No check if current_user.user_id matches user_id from path.
    update_data = {}
    if email is not None:
        # Check if new email is already taken by another user
        existing_email_user = next((u for u in db.db["users"] if u.email == email and u.user_id != user_id), None)
        if existing_email_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email '{email}' already in use.")
        update_data["email"] = email

    # Parameter Pollution Vulnerability for is_admin:
    # A regular user can pass ?is_admin=true to escalate privileges.
    if is_admin_param is not None:
        print(f"Attempting to set is_admin to: {is_admin_param} for user {user_id} via query parameter.") # Logging for demo
        update_data["is_admin"] = is_admin_param

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")

    for key, value in update_data.items():
        setattr(user_to_update, key, value)
    user_to_update.updated_at = datetime.now(timezone.utc)

    # Simulate saving back to DB (in-memory list)
    # No actual save needed as we are modifying the object in the list directly.

    return User.model_validate(user_to_update)

# BFLA Target: Initially, no admin check for deleting users.
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(
    user_id: UUID,
    # current_user: TokenData = Depends(get_current_user) # BFLA: No check initially
):
    user_index = -1
    for i, u in enumerate(db.db["users"]):
        if u.user_id == user_id:
            user_index = i
            break

    if user_index == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # BFLA Vulnerability: Any authenticated user can delete any other user.
    # No check if current_user is admin.
    # Also, BOLA if current_user.user_id is not user_id and they can delete themselves (less of a BOLA then).
    print(f"User {user_id} being deleted. Intended BFLA: No admin check performed.") # Logging for demo
    db.db["users"].pop(user_index)

    # Also remove associated addresses and credit cards for hygiene, though not strictly part of BFLA demo
    db.db["addresses"] = [a for a in db.db["addresses"] if a.user_id != user_id]
    db.db["credit_cards"] = [cc for cc in db.db["credit_cards"] if cc.user_id != user_id]
    # Orders might be kept for historical reasons or marked inactive.

    return

@router.get("/users", response_model=List[User], tags=["Users"])
async def list_users(
    current_user: TokenData = Depends(get_current_user)
):
    """Get a list of all users - intentionally vulnerable for demonstration purposes.
    In a real application, this would be restricted to admins or have proper filtering."""
    # BOLA/BFLA Vulnerability: Any authenticated user can list all users
    print(f"User {current_user.username} (ID: {current_user.user_id}) is listing all users. Intentional vulnerability for demo.")

    # Return all users - this is the vulnerability
    return [User.model_validate(u) for u in db.db["users"]]

## Credit Card Endpoints

@router.get("/users/{user_id}/credit-cards", response_model=List[CreditCard], tags=["Credit Cards"])
async def list_user_credit_cards(
    user_id: UUID,
    # current_user: TokenData = Depends(get_current_user) # BOLA: No owner check initially
):
    """
    List all credit cards for a specific user.
    Intended BOLA: No owner check performed, allowing any authenticated user to view others' credit cards.
    """
    user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # BOLA Vulnerability: Any authenticated user can list credit cards for any user_id.
    # No check if current_user.user_id matches user_id from path.
    user_credit_cards = [
        CreditCard.model_validate(cc)
        for cc in db.db["credit_cards"]
        if cc.user_id == user_id
    ]
    print(f"User {user_id} credit cards being listed. Intended BOLA: No owner check performed.") # Logging for demo
    return user_credit_cards

@router.get("/users/{user_id}/credit-cards/{card_id}", response_model=CreditCard, tags=["Credit Cards"])
async def get_user_credit_card_by_id(
    user_id: UUID,
    card_id: UUID,
    # current_user: TokenData = Depends(get_current_user) # BOLA: No owner check initially
):
    """
    Get a specific credit card by ID for a given user.
    Intended BOLA: No owner check performed, allowing any authenticated user to view others' credit cards.
    """
    user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    credit_card = next(
        (cc for cc in db.db["credit_cards"] if cc.user_id == user_id and cc.card_id == card_id),
        None
    )
    if not credit_card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit card not found for this user.")

    # BOLA Vulnerability: Any authenticated user can get credit card details for any user_id and card_id.
    # No check if current_user.user_id matches user_id from path.
    return CreditCard.model_validate(credit_card)

@router.post("/users/{user_id}/credit-cards", response_model=CreditCard, status_code=status.HTTP_201_CREATED, tags=["Credit Cards"])
async def add_credit_card_to_user(
    user_id: UUID,
    cardholder_name: str = Query(..., description="Name of the cardholder"),
    card_number: str = Query(..., min_length=13, max_length=19, description="Full credit card number"),
    expiry_month: str = Query(..., pattern=r"^0[1-9]|1[0-2]$", description="Expiry month (MM)"),
    expiry_year: str = Query(..., pattern=r"^20[2-9][0-9]$", description="Expiry year (YYYY)"),
    cvv: Optional[str] = Query(None, min_length=3, max_length=4, description="Card Verification Value"),
    is_default: bool = Query(False, description="Whether this is the default credit card"),
    # current_user: TokenData = Depends(get_current_user) # BOLA: No owner check initially
):
    """
    Add a new credit card to a user's profile, with details passed as query parameters.
    Intended BOLA: No owner check performed, allowing any authenticated user to add cards to others' profiles.
    """
    user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # BOLA Vulnerability: Any authenticated user can add credit cards for any user_id.
    # No check if current_user.user_id matches user_id from path.

    # Create a CreditCardCreate object internally for consistency,
    # or you could directly use the parameters to build CreditCardInDBBase
    card_data = CreditCardCreate(
        cardholder_name=cardholder_name,
        card_number=card_number,
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        cvv=cvv,
        is_default=is_default
    )

    # Hash sensitive data (card number and CVV)
    card_number_hash = hash_credit_card_data(card_data.card_number)
    cvv_hash = hash_credit_card_data(card_data.cvv) if card_data.cvv else None
    card_last_four = card_data.card_number[-4:] # Extract last four digits

    new_card_in_db = db.CreditCardInDBBase(
        user_id=user_id,
        cardholder_name=card_data.cardholder_name,
        expiry_month=card_data.expiry_month,
        expiry_year=card_data.expiry_year,
        is_default=card_data.is_default,
        card_number_hash=card_number_hash,
        card_last_four=card_last_four,
        cvv_hash=cvv_hash # Store hashed CVV, though not recommended for production
    )
    db.db["credit_cards"].append(new_card_in_db)
    print(f"Credit card added for user {user_id}. Intended BOLA: No owner check performed.") # Logging for demo
    return CreditCard.model_validate(new_card_in_db)

@router.put("/users/{user_id}/credit-cards/{card_id}", response_model=CreditCard, tags=["Credit Cards"])
async def update_user_credit_card(
    user_id: UUID,
    card_id: UUID,
    cardholder_name: Optional[str] = Query(None, description="Name of the cardholder"),
    expiry_month: Optional[str] = Query(None, pattern=r"^0[1-9]|1[0-2]$", description="Expiry month (MM)"),
    expiry_year: Optional[str] = Query(None, pattern=r"^20[2-9][0-9]$", description="Expiry year (YYYY)"),
    is_default: Optional[bool] = Query(None, description="Whether this is the default credit card"),
    # current_user: TokenData = Depends(get_current_user) # BOLA: No owner check initially
):
    """
    Update an existing credit card's details for a user, with details passed as query parameters.
    Intended BOLA: No owner check performed, allowing any authenticated user to modify others' credit cards.
    """
    user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    credit_card_to_update = next(
        (cc for cc in db.db["credit_cards"] if cc.user_id == user_id and cc.card_id == card_id),
        None
    )
    if not credit_card_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit card not found for this user.")

    # BOLA Vulnerability: Any authenticated user can update any user's credit card.
    # No check if current_user.user_id matches user_id from path.

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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")

    for key, value in update_data.items():
        if value is not None:
            setattr(credit_card_to_update, key, value)
    credit_card_to_update.updated_at = datetime.now(timezone.utc)
    print(f"Credit card {card_id} for user {user_id} updated. Intended BOLA: No owner check performed.") # Logging for demo
    return CreditCard.model_validate(credit_card_to_update)

@router.delete("/users/{user_id}/credit-cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Credit Cards"])
async def delete_user_credit_card(
    user_id: UUID,
    card_id: UUID,
    # current_user: TokenData = Depends(get_current_user) # BOLA: No owner check initially
):
    """
    Delete a specific credit card for a given user.
    Intended BOLA: No owner check performed, allowing any authenticated user to delete others' credit cards.
    """
    user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    card_index = -1
    for i, cc in enumerate(db.db["credit_cards"]):
        if cc.user_id == user_id and cc.card_id == card_id:
            card_index = i
            break

    if card_index == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit card not found for this user.")

    # BOLA Vulnerability: Any authenticated user can delete any user's credit card.
    # No check if current_user.user_id matches user_id from path.
    db.db["credit_cards"].pop(card_index)
    print(f"Credit card {card_id} for user {user_id} deleted. Intended BOLA: No owner check performed.") # Logging for demo
    return
