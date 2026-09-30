"""User model with RBAC roles."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="stakeholder")
    # Roles: admin, project_manager, business_analyst, architect,
    #        security_officer, compliance_officer, stakeholder, auditor
    organization = Column(String(255), default="")
    department = Column(String(255), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    projects = relationship("Project", back_populates="owner")
    approval_actions = relationship("ApprovalAction", back_populates="reviewer")
    audit_logs = relationship("AuditLog", back_populates="user")
