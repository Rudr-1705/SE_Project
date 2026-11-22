"""Approval workflow models — routes critical decisions to humans."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    request_type = Column(String(50), nullable=False)
    # Types: requirement_baseline, regulatory_interpretation,
    #        high_risk_security, stakeholder_conflict,
    #        architecture_critical, sdlc_selection,
    #        requirement_change, production_readiness

    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    context = Column(JSON, default=dict)  # Supporting data for reviewer

    # What is being approved
    target_type = Column(String(50), default="")  # requirement, sdlc, artefact
    target_id = Column(String(36), default="")
    target_data = Column(JSON, default=dict)

    # Required approvers (role-based)
    required_roles = Column(JSON, default=list)
    # e.g. ["project_manager", "compliance_officer"]

    status = Column(String(30), default="pending")
    # pending, approved, rejected, modified, cancelled
    priority = Column(String(20), default="medium")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, default=None)

    # Relationships
    project = relationship("Project", back_populates="approval_requests")
    actions = relationship("ApprovalAction", back_populates="approval_request",
                           cascade="all, delete-orphan", lazy="selectin")


class ApprovalAction(Base):
    """Individual approval/rejection by a reviewer."""
    __tablename__ = "approval_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    approval_request_id = Column(String(36), ForeignKey("approval_requests.id"), nullable=False)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    action = Column(String(20), nullable=False)  # approve, reject, modify, request_regeneration
    comments = Column(Text, default="")
    modifications = Column(JSON, default=dict)  # If action is 'modify'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    approval_request = relationship("ApprovalRequest", back_populates="actions")
    reviewer = relationship("User", back_populates="approval_actions")
