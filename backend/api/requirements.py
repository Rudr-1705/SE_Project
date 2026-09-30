"""Requirements API routes — extraction, analysis pipeline, CRUD."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from models.requirement import Requirement, RequirementVersion
from models.audit import AuditLog
from schemas.models import RequirementCreate, RequirementUpdate, RequirementResponse
from security.auth import get_current_user
from security.rbac import check_permission
from agents.orchestrator import get_orchestrator
import uuid
import json
from datetime import datetime, timezone

router = APIRouter(prefix="/api/projects/{project_id}/requirements", tags=["requirements"])


@router.get("", response_model=list[RequirementResponse])
async def list_requirements(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Requirement)
        .where(Requirement.project_id == project_id, Requirement.is_current == True)
        .order_by(Requirement.created_at.desc())
    )
    reqs = result.scalars().all()
    return [RequirementResponse.model_validate(r) for r in reqs]


@router.post("", response_model=RequirementResponse)
async def create_requirement(
    project_id: str,
    data: RequirementCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not check_permission(user, "requirements", "create"):
        raise HTTPException(status_code=403, detail="Cannot create requirements")

    # Generate requirement ID
    result = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id)
    )
    count = len(result.scalars().all())
    cat_prefix = "FR" if data.category.value == "functional" else "NFR"
    req_id = f"{cat_prefix}-LOAN-{count + 1:03d}"

    req = Requirement(
        id=str(uuid.uuid4()),
        requirement_id=req_id,
        project_id=project_id,
        statement=data.statement,
        category=data.category.value,
        source=data.source or user.full_name,
        source_type=data.source_type,
        business_justification=data.business_justification,
        priority=data.priority.value,
        status="raw",
    )
    db.add(req)

    # Create initial version
    db.add(RequirementVersion(
        requirement_id=req.id, version=1,
        statement=req.statement, category=req.category, status="raw",
        full_snapshot={"statement": req.statement, "category": req.category},
        change_reason="Initial creation", changed_by=user.id,
    ))

    db.add(AuditLog(event_type="requirement", action="create",
                    user_id=user.id, project_id=project_id,
                    target_type="requirement", target_id=req.id))
    await db.flush()
    return RequirementResponse.model_validate(req)


@router.put("/{req_id}", response_model=RequirementResponse)
async def update_requirement(
    project_id: str, req_id: str,
    data: RequirementUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not check_permission(user, "requirements", "update"):
        raise HTTPException(status_code=403, detail="Cannot update requirements")

    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Save version snapshot before update
    req.version += 1
    db.add(RequirementVersion(
        requirement_id=req.id, version=req.version,
        statement=data.statement or req.statement,
        category=data.category.value if data.category else req.category,
        status=data.status.value if data.status else req.status,
        full_snapshot=json.loads(json.dumps({
            "statement": data.statement or req.statement,
            "category": data.category.value if data.category else req.category,
        })),
        change_reason=data.change_reason or "Updated",
        changed_by=user.id,
    ))

    # Apply updates
    if data.statement:
        req.statement = data.statement
    if data.category:
        req.category = data.category.value
    if data.priority:
        req.priority = data.priority.value
    if data.business_justification:
        req.business_justification = data.business_justification
    if data.status:
        req.status = data.status.value
    req.updated_at = datetime.now(timezone.utc)

    db.add(AuditLog(event_type="requirement", action="update",
                    user_id=user.id, project_id=project_id,
                    target_type="requirement", target_id=req.id,
                    details={"version": req.version, "reason": data.change_reason}))
    await db.flush()
    return RequirementResponse.model_validate(req)


@router.post("/extract")
async def extract_requirements(
    project_id: str,
    text: str = "",
    source_type: str = "conversation",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Extract requirements from text using the extraction agent."""
    orchestrator = get_orchestrator()
    result = await orchestrator.extract_requirements(
        project_id, user.id, text, source_type
    )

    # Persist extracted requirements to DB
    extracted = result.get("requirements", [])
    persisted = []
    for r in extracted:
        req = Requirement(
            id=str(uuid.uuid4()),
            requirement_id=r.get("requirement_id", f"FR-LOAN-{len(persisted)+1:03d}"),
            project_id=project_id,
            statement=r.get("statement", ""),
            category=r.get("category", "functional"),
            subcategory=r.get("subcategory", ""),
            business_justification=r.get("business_justification", ""),
            priority=r.get("priority", "medium"),
            acceptance_criteria=r.get("acceptance_criteria", []),
            applicable_regulations=r.get("applicable_regulations", []),
            risks=r.get("risks", []),
            confidence=r.get("confidence", 0.0),
            status="extracted",
            source=user.full_name,
            source_type=source_type,
        )
        db.add(req)
        db.add(RequirementVersion(
            requirement_id=req.id, version=1,
            statement=req.statement, category=req.category, status="extracted",
            change_reason="Extracted by AI agent", changed_by=user.id,
        ))
        persisted.append(req.requirement_id)

    db.add(AuditLog(event_type="requirement", action="extract",
                    user_id=user.id, project_id=project_id,
                    details={"count": len(persisted), "source_type": source_type}))
    await db.flush()

    result["persisted_ids"] = persisted
    return result


@router.post("/analyse")
async def analyse_requirements(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """Run the full analysis pipeline on project requirements."""
    orchestrator = get_orchestrator()
    result = await orchestrator.run_analysis_pipeline(project_id, user.id)
    return result
