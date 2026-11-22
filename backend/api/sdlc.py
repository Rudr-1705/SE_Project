"""SDLC analysis, interview, and session API with project ownership enforcement."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from models.project import Project
from models.audit import AuditLog
from security.auth import get_current_user
from security.project_guard import verify_project_ownership
from agents.orchestrator import get_orchestrator

router = APIRouter(prefix="/api/projects/{project_id}", tags=["sdlc", "interview"])


@router.post("/interview/start")
async def start_interview(
    project_id: str,
    stakeholder_role: str = "business_analyst",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start adaptive stakeholder interview with ownership check."""
    await verify_project_ownership(project_id, user, db)

    orchestrator = get_orchestrator()
    return await orchestrator.start_interview(project_id, user.id, stakeholder_role, db=db)


@router.post("/interview/answer")
async def answer_interview(
    project_id: str,
    answer: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit answer and get next interview question with ownership check."""
    await verify_project_ownership(project_id, user, db)

    orchestrator = get_orchestrator()
    return await orchestrator.answer_interview(project_id, user.id, answer, db=db)


@router.get("/interview/history")
async def get_interview_history(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full conversation history and covered topics with ownership check."""
    await verify_project_ownership(project_id, user, db)

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)
    raw_session = orchestrator._get_session(project_id)
    return {
        "messages": raw_session.get("conversation_history", []),
        "topics_covered": raw_session.get("topics_covered", []),
        "stage": session.get("stage", "interview"),
    }


@router.post("/sdlc/analyse")
async def analyse_sdlc(
    project_id: str,
    factors: dict | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run SDLC selection analysis with ownership check and prerequisite validation."""
    project = await verify_project_ownership(project_id, user, db)

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)

    # Workflow validation: requirements must exist
    if session.get("requirement_count", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot run SDLC selection: No requirements found for this project."
        )

    # Include project domain/jurisdiction factors
    factors = factors or {}
    factors.setdefault("jurisdiction", project.jurisdiction)
    factors.setdefault("use_case", project.use_case)

    return await orchestrator.run_sdlc_analysis(project_id, user.id, factors, db=db)


@router.get("/sdlc/recommendation")
async def get_sdlc_recommendation(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current SDLC recommendation with ownership check."""
    await verify_project_ownership(project_id, user, db)

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    session = orchestrator.get_session_state(project_id)
    sdlc_res = session.get("analysis_results", {}).get("sdlc")
    if not sdlc_res:
        raise HTTPException(status_code=404, detail="SDLC analysis not yet run")
    return sdlc_res


@router.post("/artefacts/generate")
async def generate_artefact(
    project_id: str,
    artefact_type: str = "srs",
    project_name: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate SRS document (only SRS is supported) with ownership check."""
    project = await verify_project_ownership(project_id, user, db)
    name = project_name or project.name
    desc = project.description or ""

    orchestrator = get_orchestrator()
    return await orchestrator.generate_srs(
        project_id=project_id,
        user_id=user.id,
        project_name=name,
        project_desc=desc,
        db=db,
    )


@router.get("/session")
async def get_session_state(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current orchestrator session state with ownership check."""
    await verify_project_ownership(project_id, user, db)

    orchestrator = get_orchestrator()
    await orchestrator.sync_from_db(project_id, db)
    return orchestrator.get_session_state(project_id)


@router.get("/audit-trail")
async def get_audit_trail(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get persistent and session audit trail with ownership check."""
    await verify_project_ownership(project_id, user, db)

    res = await db.execute(
        select(AuditLog)
        .where(AuditLog.project_id == project_id)
        .order_by(AuditLog.created_at.desc())
    )
    logs = res.scalars().all()

    orchestrator = get_orchestrator()
    agent_trail = orchestrator.get_audit_trail(project_id)

    combined = []
    for l in logs:
        combined.append({
            "id": l.id,
            "agent": l.event_type,
            "action": l.action,
            "status": "success",
            "timestamp": l.created_at.isoformat() if l.created_at else "",
            "details": l.details,
            "user_id": l.user_id,
        })
    for a in agent_trail:
        combined.append({
            "agent": a.get("agent"),
            "action": a.get("action"),
            "status": a.get("status"),
            "confidence": a.get("confidence"),
            "timestamp": a.get("timestamp"),
            "issues": a.get("issues", []),
        })

    # Sort by timestamp desc
    combined.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return combined
