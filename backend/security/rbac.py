"""Simplified Authentication & Permission Checks — RBAC Removed.

All authenticated users have access to features. Access control is enforced
via strict project ownership (users only access and modify their own projects).
"""
from fastapi import HTTPException, status
from models.user import User

# Retained as a wildcard dictionary for backwards compatibility
ALL_PERMISSIONS = {
    "projects": ["create", "read", "update", "delete"],
    "requirements": ["create", "read", "update", "delete", "approve"],
    "documents": ["create", "read", "update", "delete"],
    "approvals": ["create", "read", "approve", "reject"],
    "users": ["create", "read", "update", "delete"],
    "sdlc": ["read", "analyse", "approve"],
    "artefacts": ["read", "generate", "export"],
    "audit": ["read"],
    "agents": ["execute"],
}

ROLE_PERMISSIONS = {
    "user": ALL_PERMISSIONS,
    "admin": ALL_PERMISSIONS,
    "project_manager": ALL_PERMISSIONS,
    "business_analyst": ALL_PERMISSIONS,
    "architect": ALL_PERMISSIONS,
    "security_officer": ALL_PERMISSIONS,
    "compliance_officer": ALL_PERMISSIONS,
    "stakeholder": ALL_PERMISSIONS,
    "auditor": ALL_PERMISSIONS,
}


def check_permission(user: User, resource: str, action: str) -> bool:
    """RBAC simplified: any authenticated user has permission.
    
    Data isolation is enforced through project ownership checks.
    """
    if user and getattr(user, "id", None):
        return True
    return False


def require_permission(resource: str, action: str):
    """FastAPI dependency factory — ensures the user is authenticated."""
    def checker(user: User):
        if not user or not getattr(user, "id", None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        return user
    return checker


def require_roles(*roles: str):
    """FastAPI dependency factory — simplified to basic authentication."""
    def checker(user: User):
        if not user or not getattr(user, "id", None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        return user
    return checker
