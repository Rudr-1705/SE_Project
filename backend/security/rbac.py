"""RBAC — Role-Based Access Control with least-privilege enforcement."""
from functools import wraps
from fastapi import HTTPException, status
from models.user import User

# Role hierarchy: what each role is allowed to do
ROLE_PERMISSIONS = {
    "admin": {
        "projects": ["create", "read", "update", "delete"],
        "requirements": ["create", "read", "update", "delete", "approve"],
        "documents": ["create", "read", "update", "delete"],
        "approvals": ["create", "read", "approve", "reject"],
        "users": ["create", "read", "update", "delete"],
        "sdlc": ["read", "analyse", "approve"],
        "artefacts": ["read", "generate", "export"],
        "audit": ["read"],
        "agents": ["execute"],
    },
    "project_manager": {
        "projects": ["create", "read", "update"],
        "requirements": ["create", "read", "update", "approve"],
        "documents": ["create", "read", "update"],
        "approvals": ["create", "read", "approve", "reject"],
        "users": ["read"],
        "sdlc": ["read", "analyse", "approve"],
        "artefacts": ["read", "generate", "export"],
        "audit": ["read"],
        "agents": ["execute"],
    },
    "business_analyst": {
        "projects": ["create", "read", "update"],
        "requirements": ["create", "read", "update"],
        "documents": ["create", "read"],
        "approvals": ["create", "read", "approve"],
        "users": ["read"],
        "sdlc": ["read", "analyse"],
        "artefacts": ["read", "generate"],
        "audit": ["read"],
        "agents": ["execute"],
    },
    "architect": {
        "projects": ["read"],
        "requirements": ["read", "update", "approve"],
        "documents": ["read"],
        "approvals": ["read", "approve", "reject"],
        "sdlc": ["read", "analyse", "approve"],
        "artefacts": ["read", "generate"],
        "audit": ["read"],
    },
    "security_officer": {
        "projects": ["read"],
        "requirements": ["read", "update", "approve"],
        "documents": ["read"],
        "approvals": ["read", "approve", "reject"],
        "sdlc": ["read", "approve"],
        "artefacts": ["read"],
        "audit": ["read"],
    },
    "compliance_officer": {
        "projects": ["read"],
        "requirements": ["read", "update", "approve"],
        "documents": ["read"],
        "approvals": ["read", "approve", "reject"],
        "sdlc": ["read", "approve"],
        "artefacts": ["read"],
        "audit": ["read"],
    },
    "stakeholder": {
        "projects": ["read"],
        "requirements": ["read"],
        "documents": ["read"],
        "approvals": ["read"],
        "sdlc": ["read"],
        "artefacts": ["read"],
    },
    "auditor": {
        "projects": ["read"],
        "requirements": ["read"],
        "documents": ["read"],
        "approvals": ["read"],
        "sdlc": ["read"],
        "artefacts": ["read"],
        "audit": ["read"],
    },
}


def check_permission(user: User, resource: str, action: str) -> bool:
    """Check if a user's role grants a specific permission."""
    perms = ROLE_PERMISSIONS.get(user.role, {})
    allowed = perms.get(resource, [])
    return action in allowed


def require_permission(resource: str, action: str):
    """FastAPI dependency factory — raises 403 if user lacks permission."""
    def checker(user: User):
        if not check_permission(user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' lacks '{action}' permission on '{resource}'",
            )
        return user
    return checker


def require_roles(*roles: str):
    """FastAPI dependency factory — requires user to have one of the specified roles."""
    def checker(user: User):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return user
    return checker
