from rest_framework import viewsets, permissions
from apps.core.permissions import IsTenantHeadManager
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit Log inspection ViewSet for Platform Super Admins and Tenant Head Managers.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsTenantHeadManager]

    def get_queryset(self):
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None) or getattr(user, 'tenant', None)

        if user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN':
            tenant_id = self.request.query_params.get('tenant_id')
            if tenant_id:
                return AuditLog.objects.filter(tenant_id=tenant_id)
            return AuditLog.objects.all()
        return AuditLog.objects.filter(tenant=tenant)
