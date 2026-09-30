"""Audit log — immutable record of all system events."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    project_id = Column(String(36), default=None)

    # Event classification
    event_type = Column(String(50), nullable=False)
    # Types: auth, project, requirement, document, approval,
    #        agent, compliance, sdlc, artefact, system
    action = Column(String(100), nullable=False)
    # Actions: create, read, update, delete, approve, reject,
    #          upload, download, analyse, generate, login, logout

    # What was affected
    target_type = Column(String(50), default="")
    target_id = Column(String(36), default="")
    description = Column(Text, default="")

    # Context
    details = Column(JSON, default=dict)
    ip_address = Column(String(45), default="")
    user_agent = Column(String(255), default="")

    # Agent tracking
    agent_name = Column(String(50), default="")
    llm_model = Column(String(100), default="")
    llm_prompt_hash = Column(String(64), default="")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_logs")
