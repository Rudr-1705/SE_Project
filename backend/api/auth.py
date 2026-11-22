"""Auth API routes — register, login, user management, and token revocation."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from models.audit import AuditLog
from schemas.models import UserCreate, UserLogin, UserResponse, TokenResponse
from security.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
    revoke_token, security_scheme
)
from security.rbac import require_roles

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Roles forbidden from public self-registration
FORBIDDEN_REGISTRATION_ROLES = {"admin", "project_manager", "auditor"}
SAFE_DEFAULT_ROLES = {"business_analyst", "stakeholder", "architect", "security_officer", "compliance_officer"}


@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user with safe role enforcement."""
    # Enforce safe role on public registration: never allow admin creation
    requested_role = (data.role.value if hasattr(data.role, "value") else str(data.role)).lower()
    if requested_role in FORBIDDEN_REGISTRATION_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Registration with privileged role '{requested_role}' is forbidden. Public users can register as business_analyst or stakeholder."
        )

    # Safe default: if not in safe roles, assign business_analyst
    assigned_role = requested_role if requested_role in SAFE_DEFAULT_ROLES else "business_analyst"

    # Check existing email
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=assigned_role,
        organization=data.organization,
        department=data.department,
    )
    db.add(user)
    await db.flush()

    # Audit event
    db.add(AuditLog(
        event_type="auth", action="register",
        user_id=user.id, target_type="user", target_id=user.id,
        details={"assigned_role": assigned_role}
    ))

    token = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    db.add(AuditLog(
        event_type="auth", action="login",
        user_id=user.id, target_type="user", target_id=user.id
    ))

    token = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse.model_validate(user)


@router.post("/logout")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout current user and revoke JWT token across restarts."""
    if credentials and credentials.credentials:
        await revoke_token(credentials.credentials, user.id, db)

    db.add(AuditLog(
        event_type="auth", action="logout",
        user_id=user.id, target_type="user", target_id=user.id
    ))
    await db.flush()
    return {"message": "Logged out successfully", "revoked": True}


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin/PM only)."""
    if user.role not in ("admin", "project_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]
