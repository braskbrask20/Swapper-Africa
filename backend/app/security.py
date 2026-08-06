import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from .config import get_settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user_id: int, role: str, token_version: int) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(user_id), "role": role, "ver": token_version, "exp": expires_at}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def generate_token() -> str:
    """Raw single-use token for password reset / email verification links."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Only the hash is stored, same principle as password hashing: a DB leak can't be replayed."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def decode_access_token(credentials: Optional[HTTPAuthorizationCredentials] = None) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return jwt.decode(credentials.credentials, get_settings().jwt_secret, algorithms=[get_settings().jwt_algorithm])
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from error
