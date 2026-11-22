"""SRS Document API — IEEE 29148 generation, preview, and PDF/DOCX downloads."""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from models.project import Project
from models.audit import AuditLog
from security.auth import get_current_user
from agents.orchestrator import get_orchestrator
from config import settings

router = APIRouter(prefix="/api/projects/{project_id}/srs", tags=["srs"])


@router.post("/generate")
async def generate_srs_document(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate the complete IEEE 29148 Software Requirements Specification."""
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role != "admin" and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")

    orchestrator = get_orchestrator()
    result = await orchestrator.generate_srs(
        project_id=project_id,
        user_id=user.id,
        project_name=project.name,
        project_desc=project.description,
        db=db,
    )

    db.add(AuditLog(
        event_type="document", action="generate_srs",
        user_id=user.id, project_id=project_id,
        details={"version": "1.0", "title": result.get("title")}
    ))
    await db.flush()

    return result


@router.get("/preview")
async def preview_srs_document(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the structured JSON representation of the generated SRS."""
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)
    srs_res = session.get("srs_result")

    if not srs_res:
        # If not generated yet, generate now on demand
        srs_res = await orchestrator.generate_srs(
            project_id=project_id,
            user_id=user.id,
            project_name=project.name,
            project_desc=project.description,
            db=db,
        )

    return srs_res


@router.get("/download/pdf")
async def download_srs_pdf(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the generated IEEE 29148 SRS as a formatted PDF."""
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)
    srs_res = session.get("srs_result")

    if not srs_res or not srs_res.get("pdf_path") or not os.path.exists(srs_res["pdf_path"]):
        # Generate on demand
        srs_res = await orchestrator.generate_srs(
            project_id=project_id,
            user_id=user.id,
            project_name=project.name,
            project_desc=project.description,
            db=db,
        )

    pdf_path = srs_res.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="PDF generation failed or file not found")

    filename = srs_res.get("pdf_filename", f"SRS_{project.name}.pdf")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.get("/download/docx")
async def download_srs_docx(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the generated IEEE 29148 SRS as an editable DOCX document."""
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)
    srs_res = session.get("srs_result")

    if not srs_res or not srs_res.get("docx_path") or not os.path.exists(srs_res["docx_path"]):
        srs_res = await orchestrator.generate_srs(
            project_id=project_id,
            user_id=user.id,
            project_name=project.name,
            project_desc=project.description,
            db=db,
        )

    docx_path = srs_res.get("docx_path")
    if not docx_path or not os.path.exists(docx_path):
        raise HTTPException(status_code=500, detail="DOCX generation failed or file not found")

    filename = srs_res.get("docx_filename", f"SRS_{project.name}.docx")
    return FileResponse(
        path=docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )
