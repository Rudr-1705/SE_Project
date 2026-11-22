"""Revoked tokens model — tracks invalidated JWT tokens across restarts."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from database import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    token_jti = Column(String(64), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    revoked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
