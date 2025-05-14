from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuration (consider moving to a config file or environment variables)
SECRET_KEY = "a_very_secret_key_for_jwt_radware_demo"  # KEEP THIS SECRET IN A REAL APP
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Convert UUID to string if present, as JWT standard doesn't directly support UUID type
    for key, value in to_encode.items():
        if isinstance(value, UUID):
            to_encode[key] = str(value)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Convert user_id back to UUID if it exists
        if "user_id" in payload and payload["user_id"] is not None:
            try:
                payload["user_id"] = UUID(payload["user_id"])
            except ValueError:
                # Handle cases where user_id is not a valid UUID string, though it should be
                return None 
        return payload
    except JWTError:
        return None
