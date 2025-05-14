from fastapi import APIRouter, HTTPException, status, Query
from typing import List
from uuid import UUID

from .. import db  # Relative import for the db module
from ..models.user_models import User, UserCreate, UserInDBBase, UserUpdate
from ..models.order_models import Token # Token model for response
from ..security import get_password_hash, verify_password, create_access_token, decode_access_token

router = APIRouter()

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register_user(
    username: str = Query(...),
    email: str = Query(...),
    password: str = Query(...)
):
    # Check if user already exists
    existing_user_by_username = next((u for u in db.db["users"] if u.username == username), None)
    if existing_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    existing_user_by_email = next((u for u in db.db["users"] if u.email == email), None)
    if existing_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(password)
    # Create UserInDBBase instance before saving
    user_in_db = UserInDBBase(username=username, email=email, password_hash=hashed_password)
    db.db["users"].append(user_in_db)
    return User.model_validate(user_in_db) # Convert to User model for response

@router.post("/login", response_model=Token, tags=["Auth"])
async def login_for_access_token(
    username: str = Query(...),
    password: str = Query(...)
):
    user = next((u for u in db.db["users"] if u.username == username), None)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.user_id)} # Ensure user_id is str for JWT
    )
    return {"access_token": access_token, "token_type": "bearer"}
