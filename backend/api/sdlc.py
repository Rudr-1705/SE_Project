"""SDLC analysis and artefact generation API."""
from fastapi import APIRouter, Depends
from models.user import User
from security.auth import get_current_user
from agents.orchestrator import get_orchestrator

router = APIRouter(prefix="/api/projects/{project_id}", tags=["sdlc", "artefacts"])


@router.post("/sdlc/analyse")
async def analyse_sdlc(
    project_id: str,
    factors: dict | None = None,
    user: User = Depends(get_current_user),
):
    """Run SDLC selection analysis. Final choice requires human approval."""
    orchestrator = get_orchestrator()
    result = await orchestrator.run_sdlc_analysis(project_id, user.id, factors)
    return result


@router.get("/sdlc/result")
async def get_sdlc_result(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """Get stored SDLC analysis result."""
    orchestrator = get_orchestrator()
    session = orchestrator.get_session_state(project_id)
    results = orchestrator._get_session(project_id).get("analysis_results", {})
    return results.get("sdlc", {"message": "No SDLC analysis run yet"})


@router.post("/artefacts/generate")
async def generate_artefact(
    project_id: str,
    artefact_type: str = "srs",
    project_name: str = "",
    user: User = Depends(get_current_user),
):
    """Generate a documentation artefact (SRS, user stories, RTM, etc.)."""
    orchestrator = get_orchestrator()
    result = await orchestrator.generate_artefact(
        project_id, user.id, artefact_type, project_name
    )
    return result


@router.get("/session")
async def get_session_state(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """Get current orchestrator session state."""
    orchestrator = get_orchestrator()
    return orchestrator.get_session_state(project_id)


@router.get("/audit-trail")
async def get_audit_trail(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """Get the agent audit trail for this project."""
    orchestrator = get_orchestrator()
    return orchestrator.get_audit_trail(project_id)


@router.post("/interview/start")
async def start_interview(
    project_id: str,
    stakeholder_role: str = "business_analyst",
    user: User = Depends(get_current_user),
):
    """Start adaptive stakeholder interview."""
    orchestrator = get_orchestrator()
    return await orchestrator.start_interview(project_id, user.id, stakeholder_role)


@router.post("/interview/answer")
async def answer_interview(
    project_id: str,
    answer: str = "",
    user: User = Depends(get_current_user),
):
    """Submit answer and get next interview question."""
    orchestrator = get_orchestrator()
    return await orchestrator.answer_interview(project_id, user.id, answer)
