from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
from uuid import UUID

from jose import JWTError, jwt, jwk
from pathlib import Path
from passlib.context import CryptContext
import bcrypt # <-- ADD THIS IMPORT FOR BCrypt

# Configuration (consider moving to a config file or environment variables)
BASE_DIR = Path(__file__).resolve().parent
PRIVATE_KEY_PATH = BASE_DIR / "keys" / "private_key.pem"
PUBLIC_KEY_PATH = BASE_DIR / "keys" / "public_key.pem"

RSA_PRIVATE_KEY = PRIVATE_KEY_PATH.read_text()
RSA_PUBLIC_KEY = PUBLIC_KEY_PATH.read_text()

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain-text password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
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
    encoded_jwt = jwt.encode(to_encode, RSA_PRIVATE_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decodes a JWT access token."""
    try:
        payload = jwt.decode(token, RSA_PUBLIC_KEY, algorithms=[ALGORITHM])
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

# --- NEW: Credit Card Hashing Functions ---

def hash_credit_card_data(data: str) -> str:
    """
    Hashes sensitive credit card data (e.g., card number, CVV) using bcrypt.
    NOTE: For real applications, storing CVV or full card numbers even hashed
    is highly sensitive and requires strict PCI DSS compliance. Tokenization
    via a payment gateway is usually preferred.
    """
    if not data:
        # Return an empty string or raise an error if hashing empty data is not desired
        return ""
    # bcrypt.hashpw expects bytes, so encode the string
    hashed_data = bcrypt.hashpw(data.encode('utf-8'), bcrypt.gensalt())
    # Decode back to string for storage if your DB expects string
    return hashed_data.decode('utf-8')

def verify_credit_card_cvv(plain_cvv: str, hashed_cvv: str) -> bool:
    """
    Verifies a plain-text CVV against its stored hash using bcrypt.
    NOTE: For CVV, typically it's not stored at all after initial use for transaction.
    This function is for demonstration if you choose to store a hash for some reason.
    """
    if not plain_cvv or not hashed_cvv:
        return False
    try:
        # bcrypt.checkpw expects bytes for both arguments
        return bcrypt.checkpw(plain_cvv.encode('utf-8'), hashed_cvv.encode('utf-8'))
    except ValueError:
        # This can happen if the hashed_cvv is not a valid bcrypt hash string
        return False
