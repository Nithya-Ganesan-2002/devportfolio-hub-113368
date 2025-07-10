import hashlib
import secrets
import hmac
from datetime import datetime, timedelta
from typing import Optional

import jwt

from fastapi import HTTPException, status

# SECRET for JWT (should use env variable in a real app)
JWT_SECRET = "supersecretkey"  # TODO: Use environment variable
JWT_ALGORITHM = "HS256"

# PUBLIC_INTERFACE
def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash a password with a randomly-generated or provided salt."""
    if not salt:
        salt = secrets.token_hex(8)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${pwd_hash.hex()}"

# PUBLIC_INTERFACE
def verify_password(password: str, hashed: str) -> bool:
    """Verify that a password matches a hashed value."""
    try:
        salt, pwd_hash = hashed.split("$")
        expected = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
        return hmac.compare_digest(pwd_hash, expected)
    except Exception:
        return False

# PUBLIC_INTERFACE
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60*12))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

# PUBLIC_INTERFACE
def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT access token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

