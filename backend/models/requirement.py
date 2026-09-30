"""Canonical requirement model with full versioning — never destroys history."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from database import Base


class Requirement(Base):
    """The canonical requirement object as specified in the requirements."""
    __tablename__ = "requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(50), nullable=False, index=True)
    # Human-readable ID like FR-LOAN-001, NFR-SEC-003
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)

    # Core fields
    statement = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, default="functional")
    # functional, non_functional, security, privacy, regulatory,
    # performance, availability, usability, data, integration,
    # audit_reporting, operational
    subcategory = Column(String(100), default="")
    source = Column(String(255), default="")  # stakeholder name / document ref
    source_type = Column(String(50), default="")  # stakeholder, document, system
    business_justification = Column(Text, default="")
    priority = Column(String(20), default="medium")  # critical, high, medium, low

    # Dependencies & assumptions
    dependencies = Column(JSON, default=list)  # list of requirement IDs
    assumptions = Column(JSON, default=list)

    # Acceptance criteria
    acceptance_criteria = Column(JSON, default=list)

    # Compliance & regulation
    applicable_regulations = Column(JSON, default=list)
    applicable_controls = Column(JSON, default=list)

    # Risk & evidence
    risks = Column(JSON, default=list)
    evidence = Column(JSON, default=list)  # citations from RAG
    confidence = Column(Float, default=0.0)  # 0.0-1.0

    # Quality flags
    is_ambiguous = Column(Boolean, default=False)
    is_incomplete = Column(Boolean, default=False)
    is_conflicting = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)
    quality_issues = Column(JSON, default=list)

    # Status & workflow
    status = Column(String(30), nullable=False, default="raw")
    # raw, extracted, needs_clarification, structured, analysed,
    # validated, pending_approval, approved, rejected,
    # conflicted, superseded, changed

    # Versioning — never overwrite
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    previous_version_id = Column(String(36), default=None)

    # Traceability
    source_conversation_id = Column(String(36), default=None)
    source_document_id = Column(String(36), default=None)
    linked_artefacts = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime, default=None)
    approved_by = Column(String(36), default=None)

    # Relationships
    project = relationship("Project", back_populates="requirements")
    versions = relationship("RequirementVersion", back_populates="requirement",
                            cascade="all, delete-orphan")


class RequirementVersion(Base):
    """Immutable snapshot of a requirement at a point in time."""
    __tablename__ = "requirement_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False)
    version = Column(Integer, nullable=False)
    statement = Column(Text, nullable=False)
    category = Column(String(100), default="")
    status = Column(String(30), default="")
    full_snapshot = Column(JSON, default=dict)  # Complete serialized state
    change_reason = Column(Text, default="")
    changed_by = Column(String(36), default=None)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    requirement = relationship("Requirement", back_populates="versions")
