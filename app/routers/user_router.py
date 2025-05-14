from fastapi import APIRouter, HTTPException, status, Query, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from .. import db
from ..models.user_models import User, UserCreate, UserInDBBase, UserUpdate
from ..security import get_password_hash, decode_access_token, SECRET_KEY, ALGORITHM
from ..models.order_models import TokenData # For current_user dependency

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") # Corrected tokenUrl

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
        raise credentials_exception
    return TokenData(username=user.username, user_id=user.user_id)

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
