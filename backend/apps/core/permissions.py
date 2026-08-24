from rest_framework import permissions

class IsPlatformSuperAdmin(permissions.BasePermission):
    """Allows access only to Platform Super Administrators."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or getattr(request.user, 'role', '') == 'SUPER_ADMIN')
        )


class IsTenantHeadManager(permissions.BasePermission):
    """Allows access to Tenant Head Managers or Platform Super Admins."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'SUPER_ADMIN':
            return True
        return getattr(request.user, 'role', '') == 'HEAD_MANAGER'


class IsTenantManager(permissions.BasePermission):
    """Allows access to Managers, Head Managers, or Super Admins."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'SUPER_ADMIN':
            return True
        return getattr(request.user, 'role', '') in ('HEAD_MANAGER', 'MANAGER')


class IsTenantUser(permissions.BasePermission):
    """Allows access to any authenticated user with a valid tenant."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'SUPER_ADMIN':
            return True
        return bool(getattr(request.user, 'tenant_id', None))


class IsTenantManagerOrReadOnly(permissions.BasePermission):
    """Allows full access to Managers, Head Managers, or Super Admins. Read-only for Tenant Staff."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'SUPER_ADMIN':
            return True
        if not getattr(request.user, 'tenant_id', None):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(request.user, 'role', '') in ('HEAD_MANAGER', 'MANAGER')


class IsTenantHeadManagerOrReadOnly(permissions.BasePermission):
    """Allows full access to Head Managers or Super Admins. Read-only for other tenant users."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'SUPER_ADMIN':
            return True
        if not getattr(request.user, 'tenant_id', None):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(request.user, 'role', '') == 'HEAD_MANAGER'

