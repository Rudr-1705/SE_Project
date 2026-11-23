"""Document upload and management API with ownership verification."""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from models.document import Document, DocumentChunk
from models.audit import AuditLog
from schemas.models import DocumentResponse
from security.auth import get_current_user
from security.sanitization import validate_file_type, validate_file_size
from security.project_guard import verify_project_ownership
from config import settings
from rag.ingestion import parse_document
from rag.chunking import chunk_document
from rag.pipeline import add_documents

router = APIRouter(prefix="/api/projects/{project_id}/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    doc_type: str = Form("general"),
    title: str = Form(""),
    jurisdiction: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)

    if not validate_file_type(file.filename):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Read file
    content = await file.read()
    if not validate_file_size(len(content)):
        raise HTTPException(status_code=400, detail="File too large")

    # Save file
    file_id = str(uuid.uuid4())
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{file_id}.{ext}"
    file_path = os.path.join(str(settings.UPLOAD_DIR), filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create DB record
    doc = Document(
        id=file_id,
        project_id=project_id,
        filename=filename,
        original_filename=file.filename,
        file_type=ext,
        file_size=len(content),
        file_path=file_path,
        title=title or file.filename,
        doc_type=doc_type,
        jurisdiction=jurisdiction,
        status="uploaded",
    )
    db.add(doc)
    await db.flush()

    # Parse and chunk in background
    try:
        pages = parse_document(file_path)
        doc.status = "parsed"

        chunks = chunk_document(pages)
        doc.chunk_count = len(chunks)

        # Store chunks in DB and vector store
        chunk_texts = []
        chunk_metadatas = []
        chunk_ids = []
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            db_chunk = DocumentChunk(
                id=chunk_id,
                document_id=doc.id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                page_number=chunk.get("page_number"),
                section=chunk.get("section", ""),
                token_count=chunk.get("token_count", 0),
                embedding_id=chunk_id,
            )
            db.add(db_chunk)

            chunk_texts.append(chunk["content"])
            chunk_metadatas.append({
                "document_id": doc.id,
                "project_id": project_id,
                "doc_type": doc_type,
                "page": str(chunk.get("page_number", 0)),
                "source": file.filename,
            })
            chunk_ids.append(chunk_id)

        # Add to vector store
        if chunk_texts:
            add_documents(chunk_texts, chunk_metadatas, chunk_ids)

        doc.status = "embedded"
    except Exception as e:
        doc.status = "failed"
        doc.error_message = str(e)

    db.add(AuditLog(event_type="document", action="upload",
                    user_id=user.id, project_id=project_id,
                    target_type="document", target_id=doc.id,
                    details={"filename": file.filename, "chunks": doc.chunk_count}))
    await db.flush()
    return DocumentResponse.model_validate(doc)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)

    result = await db.execute(
        select(Document).where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return [DocumentResponse.model_validate(d) for d in docs]
