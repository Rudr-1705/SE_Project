"""Document model — uploaded files and their parsed chunks."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt, csv
    file_size = Column(Integer, default=0)
    file_path = Column(String(500), nullable=False)

    # Metadata
    title = Column(String(255), default="")
    doc_type = Column(String(100), default="general")
    # Types: policy, regulation, requirement, interview_transcript,
    #        meeting_notes, api_spec, legacy_doc, audit_finding
    jurisdiction = Column(String(100), default="")
    effective_date = Column(String(50), default="")
    version = Column(String(50), default="1.0")
    source = Column(String(255), default="")
    applicability = Column(JSON, default=list)

    # Processing state
    status = Column(String(30), default="uploaded")
    # uploaded, parsing, parsed, chunked, embedded, failed
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, default="")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    project = relationship("Project", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, default=None)
    section = Column(String(255), default="")
    token_count = Column(Integer, default=0)
    embedding_id = Column(String(100), default="")  # ChromaDB reference

    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="chunks")
