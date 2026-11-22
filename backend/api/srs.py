"""SRS Document API — IEEE 29148 generation, preview, and authenticated PDF/DOCX downloads."""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from models.project import Project
from models.approval import ApprovalRequest
from models.audit import AuditLog
from security.auth import get_current_user
from security.project_guard import verify_project_ownership
from agents.orchestrator import get_orchestrator
from config import settings

router = APIRouter(prefix="/api/projects/{project_id}/srs", tags=["srs"])


@router.post("/generate")
async def generate_srs_document(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate the complete IEEE 29148 Software Requirements Specification with ownership check."""
    project = await verify_project_ownership(project_id, user, db)

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)

    # Workflow validation: requirements must exist
    if session.get("requirement_count", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate SRS: No requirements found for this project. Please complete extraction first."
        )

    # Check actual approval status
    app_res = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.project_id == project_id)
    )
    approvals = app_res.scalars().all()
    is_approved = any(a.status == "approved" for a in approvals)
    approval_status = "approved" if is_approved else "pending"

    result = await orchestrator.generate_srs(
        project_id=project_id,
        user_id=user.id,
        project_name=project.name,
        project_desc=project.description,
        jurisdiction=project.jurisdiction,
        approval_status=approval_status,
        db=db,
    )

    db.add(AuditLog(
        event_type="document", action="generate_srs",
        user_id=user.id, project_id=project_id,
        details={"version": "1.0", "title": result.get("title"), "is_approved": is_approved}
    ))
    await db.flush()

    return result


@router.get("/preview")
async def preview_srs_document(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get structured representation of generated SRS with ownership check."""
    project = await verify_project_ownership(project_id, user, db)

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)
    srs_res = session.get("srs_result")

    # Check actual approval status
    app_res = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.project_id == project_id)
    )
    approvals = app_res.scalars().all()
    is_approved = any(a.status == "approved" for a in approvals)
    approval_status = "approved" if is_approved else "pending"

    if not srs_res:
        srs_res = await orchestrator.generate_srs(
            project_id=project_id,
            user_id=user.id,
            project_name=project.name,
            project_desc=project.description,
            jurisdiction=project.jurisdiction,
            approval_status=approval_status,
            db=db,
        )
    elif srs_res and "srs_data" in srs_res and is_approved:
        srs_res["srs_data"]["metadata"]["status"] = "APPROVED BASELINE"
        srs_res["srs_data"]["metadata"]["version"] = "1.0 Baseline"

    return srs_res


@router.get("/download/pdf")
async def download_srs_pdf(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the generated IEEE 29148 SRS as a formatted PDF with JWT ownership check."""
    project = await verify_project_ownership(project_id, user, db)

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)
    srs_res = session.get("srs_result")

    if not srs_res or not srs_res.get("pdf_path") or not os.path.exists(srs_res["pdf_path"]):
        app_res = await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.project_id == project_id)
        )
        approvals = app_res.scalars().all()
        is_approved = any(a.status == "approved" for a in approvals)
        approval_status = "approved" if is_approved else "pending"

        srs_res = await orchestrator.generate_srs(
            project_id=project_id,
            user_id=user.id,
            project_name=project.name,
            project_desc=project.description,
            jurisdiction=project.jurisdiction,
            approval_status=approval_status,
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
    """Download the generated IEEE 29148 SRS as an editable DOCX document with JWT ownership check."""
    project = await verify_project_ownership(project_id, user, db)

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)
    srs_res = session.get("srs_result")

    if not srs_res or not srs_res.get("docx_path") or not os.path.exists(srs_res["docx_path"]):
        app_res = await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.project_id == project_id)
        )
        approvals = app_res.scalars().all()
        is_approved = any(a.status == "approved" for a in approvals)
        approval_status = "approved" if is_approved else "pending"

        srs_res = await orchestrator.generate_srs(
            project_id=project_id,
            user_id=user.id,
            project_name=project.name,
            project_desc=project.description,
            jurisdiction=project.jurisdiction,
            approval_status=approval_status,
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
