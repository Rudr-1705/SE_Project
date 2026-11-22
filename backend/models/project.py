"""Project model — represents a financial requirements project."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    use_case = Column(String(100), nullable=False, default="loan_processing")
    # Use cases: loan_processing, digital_onboarding, payment_processing,
    #            fraud_detection, regulatory_reporting, etc.
    status = Column(String(50), default="active")
    # Statuses: active, in_review, approved, archived
    current_stage = Column(String(50), default="interview")
    # Stages: interview, extraction, analysis, sdlc, srs, approval, completed
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    jurisdiction = Column(String(100), default="")
    industry_segment = Column(String(100), default="banking")
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="projects")
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="project", cascade="all, delete-orphan")
