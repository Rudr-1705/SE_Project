"""Authentication — JWT tokens, password hashing, user verification, and token revocation."""
import uuid
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config import settings
from database import get_db
from models.user import User
from models.revoked_token import RevokedToken

security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "role": role,
        "jti": jti,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def is_token_revoked(jti: str, db: AsyncSession) -> bool:
    """Check if token JTI has been revoked."""
    if not jti:
        return False
    res = await db.execute(select(RevokedToken).where(RevokedToken.token_jti == jti))
    return res.scalar_one_or_none() is not None


async def revoke_token(token: str, user_id: str, db: AsyncSession) -> bool:
    """Revoke a JWT token by storing its JTI in the database."""
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        if not jti:
            jti = str(uuid.uuid5(uuid.NAMESPACE_DNS, token))
        
        exp_ts = payload.get("exp")
        exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else None

        existing = await db.execute(select(RevokedToken).where(RevokedToken.token_jti == jti))
        if not existing.scalar_one_or_none():
            revoked = RevokedToken(
                token_jti=jti,
                user_id=user_id,
                expires_at=exp_dt,
            )
            db.add(revoked)
            await db.flush()
        return True
    except Exception:
        return False


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    token_param: Optional[str] = Query(None, alias="token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency — extracts, validates and enforces revocation checks for JWT."""
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif token_param:
        raw_token = token_param

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(raw_token)
    user_id = payload.get("sub")
    jti = payload.get("jti")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Enforce token revocation check against database
    if jti and await is_token_revoked(jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user
