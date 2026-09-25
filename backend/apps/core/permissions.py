from rest_framework import permissions
from apps.authentication.models import UserRole


def _is_platform_super_admin(user) -> bool:
    return bool(user.is_superuser or getattr(user, 'role', '') == UserRole.SUPER_ADMIN)


class IsPlatformSuperAdmin(permissions.BasePermission):
    """Allows access only to Platform Super Administrators."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            _is_platform_super_admin(request.user)
        )


class IsTenantHeadManager(permissions.BasePermission):
    """Allows access to Tenant Head Managers or Platform Super Admins."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if _is_platform_super_admin(request.user):
            return True
        return getattr(request.user, 'role', '') == UserRole.HEAD_MANAGER


class IsTenantManager(permissions.BasePermission):
    """Allows access to Managers, Head Managers, or Super Admins."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if _is_platform_super_admin(request.user):
            return True
        return getattr(request.user, 'role', '') in (UserRole.HEAD_MANAGER, UserRole.MANAGER)


class IsTenantUser(permissions.BasePermission):
    """Allows access to any authenticated user with a valid tenant."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if _is_platform_super_admin(request.user):
            return True
        return bool(getattr(request.user, 'tenant_id', None))


class IsTenantManagerOrReadOnly(permissions.BasePermission):
    """Allows full access to Managers, Head Managers, or Super Admins. Read-only for Tenant Staff."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if _is_platform_super_admin(request.user):
            return True
        if not getattr(request.user, 'tenant_id', None):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(request.user, 'role', '') in (UserRole.HEAD_MANAGER, UserRole.MANAGER)


class IsTenantHeadManagerOrReadOnly(permissions.BasePermission):
    """Allows full access to Head Managers or Super Admins. Read-only for other tenant users."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if _is_platform_super_admin(request.user):
            return True
        if not getattr(request.user, 'tenant_id', None):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(request.user, 'role', '') == UserRole.HEAD_MANAGER
