"""Knowledge base items — regulatory docs, policies, standards."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from database import Base


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    # Categories: regulation, policy, security_standard, process,
    #             template, guideline, terminology, sdlc_rule

    # Source tracking
    source = Column(String(255), nullable=False)
    source_url = Column(String(500), default="")
    document_id = Column(String(36), default=None)

    # Jurisdiction & applicability
    jurisdiction = Column(String(100), default="general")
    effective_date = Column(String(50), default="")
    expiry_date = Column(String(50), default="")
    version = Column(String(50), default="1.0")
    applicability = Column(JSON, default=list)  # e.g. ["loan_processing", "kyc"]

    # Embedding reference
    embedding_id = Column(String(100), default="")
    is_active = Column(Boolean, default=True)

    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
