from fastapi import APIRouter, HTTPException, status, Query
from typing import List
from uuid import UUID
from jose import jwk
from ..security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    RSA_PUBLIC_KEY,
)

from .. import db  # Relative import for the db module
from ..models.user_models import User, UserCreate, UserInDBBase, UserUpdate
from ..models.order_models import Token  # Token model for response

router = APIRouter()


@router.post(
    "/register", response_model=User, status_code=status.HTTP_201_CREATED, tags=["Auth"]
)
async def register_user(
    username: str = Query(...), email: str = Query(...), password: str = Query(...)
):
    # Check if user already exists
    existing_user_by_username = db.db_users_by_username.get(username)
    if existing_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    existing_user_by_email = db.db_users_by_email.get(email)
    if existing_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    hashed_password = get_password_hash(password)
    # Create UserInDBBase instance before saving
    user_in_db = UserInDBBase(
        username=username, email=email, password_hash=hashed_password
    )
    db.db["users"].append(user_in_db)
    db.db_users_by_id[user_in_db.user_id] = user_in_db
    db.db_users_by_username[user_in_db.username] = user_in_db
    db.db_users_by_email[user_in_db.email] = user_in_db
    return User.model_validate(user_in_db)  # Convert to User model for response


@router.post("/login", response_model=Token, tags=["Auth"])
async def login_for_access_token(
    username: str = Query(...), password: str = Query(...)
):
    user = db.db_users_by_username.get(username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": str(user.user_id),
            "is_admin": user.is_admin,
        }
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/.well-known/jwks.json", tags=["Auth"])
async def get_jwks():
    """Return the JSON Web Key Set (JWKS) for the RSA public key."""
    try:
        key_obj = jwk.construct(RSA_PUBLIC_KEY, algorithm="RS256")
        key_dict = key_obj.to_dict()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="Failed to construct JWK") from exc

    jwks = {
        "keys": [
            {
                "kty": key_dict.get("kty"),
                "use": "sig",
                "kid": "radware-demo-key-1",
                "alg": key_dict.get("alg"),
                "n": key_dict.get("n"),
                "e": key_dict.get("e"),
            }
        ]
    }
    return jwks
