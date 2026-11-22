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
    """Extract requirements from text using the extraction agent and persist deduplicated."""
    orchestrator = get_orchestrator()
    result = await orchestrator.extract_requirements(
        project_id, user.id, text, source_type, db=db
    )

    # Check existing requirements in DB to prevent duplicates
    existing_res = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id, Requirement.is_current == True)
    )
    existing_db_reqs = existing_res.scalars().all()
    existing_stmts = {r.statement.strip().lower() for r in existing_db_reqs}
    existing_ids = {r.requirement_id for r in existing_db_reqs}

    extracted = result.get("requirements", [])
    persisted = []
    for r in extracted:
        stmt = r.get("statement", "").strip()
        if not stmt or stmt.lower() in existing_stmts:
            continue

        req_id = r.get("requirement_id")
        if not req_id or req_id in existing_ids:
            cat_prefix = "NFR-SEC" if "sec" in r.get("category", "").lower() else ("NFR-PERF" if "perf" in r.get("category", "").lower() else "FR-LOAN")
            req_id = f"{cat_prefix}-{len(existing_ids) + 1:03d}"

        existing_stmts.add(stmt.lower())
        existing_ids.add(req_id)

        req = Requirement(
            id=str(uuid.uuid4()),
            requirement_id=req_id,
            project_id=project_id,
            statement=stmt,
            category=r.get("category", "functional"),
            subcategory=r.get("subcategory", ""),
            business_justification=r.get("business_justification", ""),
            priority=r.get("priority", "medium"),
            acceptance_criteria=r.get("acceptance_criteria", []),
            applicable_regulations=r.get("applicable_regulations", []),
            risks=r.get("risks", []),
            confidence=float(r.get("confidence", 0.85)),
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

    if persisted:
        db.add(AuditLog(event_type="requirement", action="extract",
                        user_id=user.id, project_id=project_id,
                        details={"count": len(persisted), "source_type": source_type}))
    await db.flush()

    # Re-fetch all current requirements for response
    all_res = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id, Requirement.is_current == True)
        .order_by(Requirement.requirement_id.asc())
    )
    all_reqs = all_res.scalars().all()
    result["requirements"] = [RequirementResponse.model_validate(r).model_dump() for r in all_reqs]
    result["count"] = len(all_reqs)
    result["persisted_ids"] = persisted
    return result


@router.post("/analyse")
async def analyse_requirements(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run the full analysis pipeline on project requirements."""
    orchestrator = get_orchestrator()
    result = await orchestrator.run_analysis_pipeline(project_id, user.id, db=db)
    return result


@router.get("/analysis-results")
async def get_analysis_results(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get stored analysis pipeline results."""
    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)
    raw = orchestrator._get_session(project_id)
    return raw.get("analysis_results", {})
