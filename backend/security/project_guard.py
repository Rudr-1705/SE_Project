"""Project ownership and access authorization guard."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from models.project import Project


async def verify_project_ownership(
    project_id: str,
    user: User,
    db: AsyncSession,
) -> Project:
    """Verify that the project exists and that the user is the owner (or an admin).
    
    Raises:
        HTTPException 404: if the project does not exist.
        HTTPException 403: if the user does not own the project and is not an admin.
    """
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user.role != "admin" and project.owner_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to access or modify this project",
        )

    return project
