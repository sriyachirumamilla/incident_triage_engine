# Hashes passwords and creates digital JWT entry badges for auth.
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Hashing User passwords using Bcrypt - Hashing is one way
pwd_context = CryptContext(schemas=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verifies a plain password against the stored Bcrypt hash.
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    # converts the plain password to a hash 
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expire_delta: timedelta = None) -> str:
    if expire_delta:
        expire = datetime.now(timezone.utc) + expire_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt