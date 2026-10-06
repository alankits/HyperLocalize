"""Role checks used by every service function (ADR 0011).

Checks live in services, not only in views, so they cannot be bypassed by
calling a different URL.
"""
from django.core.exceptions import PermissionDenied

from .models import ProjectMembership, Role


def roles_for(user, project):
    if not getattr(user, "is_authenticated", False):
        return set()
    return set(ProjectMembership.objects.filter(user=user, project=project).values_list("role", flat=True))


def has_role(user, project, *roles):
    return bool(roles_for(user, project) & set(roles))


def require_role(user, project, *roles):
    if not has_role(user, project, *roles):
        names = ", ".join(Role(r).label for r in roles)
        raise PermissionDenied(f"This action needs one of these project roles: {names}.")


def require_member(user, project):
    if not roles_for(user, project):
        raise PermissionDenied("You are not a member of this project.")


def require_administrator(user):
    if not (getattr(user, "is_authenticated", False) and user.is_administrator):
        raise PermissionDenied("This action needs the Administrator role.")
