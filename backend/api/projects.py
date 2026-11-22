"""Project API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from models.project import Project
from models.audit import AuditLog
from schemas.models import ProjectCreate, ProjectResponse
from security.auth import get_current_user
from security.rbac import check_permission
import uuid

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not check_permission(user, "projects", "create"):
        raise HTTPException(status_code=403, detail="Cannot create projects")

    project = Project(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        use_case=data.use_case.value if hasattr(data.use_case, "value") else str(data.use_case),
        jurisdiction=data.jurisdiction,
        industry_segment=data.industry_segment,
        owner_id=user.id,
        current_stage="interview",
        metadata_={"conversation_history": [], "topics_covered": [], "analysis_results": {}},
    )
    db.add(project)
    db.add(AuditLog(event_type="project", action="create",
                    user_id=user.id, project_id=project.id,
                    target_type="project", target_id=project.id))
    await db.flush()
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == "admin":
        result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    else:
        result = await db.execute(
            select(Project).where(Project.owner_id == user.id)
            .order_by(Project.created_at.desc())
        )
    projects = result.scalars().all()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role != "admin" and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")

    return ProjectResponse.model_validate(project)


@router.put("/{project_id}/stage")
async def update_project_stage(
    project_id: str,
    stage_data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role != "admin" and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this project")

    new_stage = stage_data.get("stage")
    if new_stage:
        project.current_stage = new_stage
        await db.flush()

    return {"status": "success", "current_stage": project.current_stage}
