"""Approval workflow API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from models.approval import ApprovalRequest, ApprovalAction
from models.audit import AuditLog
from schemas.models import (
    ApprovalRequestCreate, ApprovalActionCreate,
    ApprovalRequestResponse,
)
from security.auth import get_current_user
from security.rbac import check_permission
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/projects/{project_id}/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalRequestResponse])
async def list_approvals(
    project_id: str,
    status: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ApprovalRequest).where(ApprovalRequest.project_id == project_id)
    if status:
        query = query.where(ApprovalRequest.status == status)
    result = await db.execute(query.order_by(ApprovalRequest.created_at.desc()))
    approvals = result.scalars().all()
    return [ApprovalRequestResponse.model_validate(a) for a in approvals]


@router.post("", response_model=ApprovalRequestResponse)
async def create_approval(
    project_id: str,
    data: ApprovalRequestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not check_permission(user, "approvals", "create"):
        raise HTTPException(status_code=403, detail="Cannot create approvals")

    approval = ApprovalRequest(
        id=str(uuid.uuid4()),
        project_id=project_id,
        request_type=data.request_type.value,
        title=data.title,
        description=data.description,
        target_type=data.target_type,
        target_id=data.target_id,
        target_data=data.target_data,
        required_roles=data.required_roles,
        priority=data.priority.value,
    )
    db.add(approval)
    db.add(AuditLog(event_type="approval", action="create",
                    user_id=user.id, project_id=project_id,
                    target_type="approval", target_id=approval.id))
    await db.flush()
    return ApprovalRequestResponse.model_validate(approval)


@router.post("/{approval_id}/action")
async def perform_approval_action(
    project_id: str, approval_id: str,
    data: ApprovalActionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not check_permission(user, "approvals", data.action.value):
        raise HTTPException(status_code=403, detail="Insufficient approval permissions")

    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    # Check if user's role is in required_roles
    if approval.required_roles and user.role not in approval.required_roles:
        raise HTTPException(status_code=403, detail=f"Role '{user.role}' not authorised for this approval")

    action = ApprovalAction(
        id=str(uuid.uuid4()),
        approval_request_id=approval_id,
        reviewer_id=user.id,
        action=data.action.value,
        comments=data.comments,
        modifications=data.modifications,
    )
    db.add(action)

    # Update approval status
    if data.action.value in ("approve", "reject"):
        approval.status = "approved" if data.action.value == "approve" else "rejected"
        approval.resolved_at = datetime.now(timezone.utc)
    elif data.action.value == "modify":
        approval.status = "modified"
        approval.resolved_at = datetime.now(timezone.utc)

    db.add(AuditLog(event_type="approval", action=data.action.value,
                    user_id=user.id, project_id=project_id,
                    target_type="approval", target_id=approval_id,
                    details={"comments": data.comments}))
    await db.flush()
    return {"status": "success", "approval_status": approval.status}
