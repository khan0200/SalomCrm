from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.permissions import IsPlatformSuperAdmin, IsTenantHeadManager, IsTenantUser
from .models import Tenant, Branch
from .serializers import TenantSerializer, TenantCreateWithAdminSerializer, BranchSerializer

class TenantViewSet(viewsets.ModelViewSet):
    """
    Platform Super Admin Tenant Management ViewSet.
    Allows listing, creating with initial admin, updating, deactivating, and stats inspection.
    """
    queryset = Tenant.objects.all().order_by('name')

    def get_permissions(self):
        if self.action in ('list', 'create', 'destroy', 'deactivate', 'activate'):
            return [IsPlatformSuperAdmin()]
        return [IsTenantHeadManager()]

    def get_serializer_class(self):
        if self.action == 'create':
            return TenantCreateWithAdminSerializer
        return TenantSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN':
            return Tenant.objects.all().order_by('name')
        return Tenant.objects.filter(id=user.tenant_id)

    @action(detail=True, methods=['post'], permission_classes=[IsPlatformSuperAdmin])
    def deactivate(self, request, pk=None):
        tenant = self.get_object()
        tenant.is_active = False
        tenant.save(update_fields=['is_active'])
        return Response({'status': 'Tenant deactivated'})

    @action(detail=True, methods=['post'], permission_classes=[IsPlatformSuperAdmin])
    def activate(self, request, pk=None):
        tenant = self.get_object()
        tenant.is_active = True
        tenant.save(update_fields=['is_active'])
        return Response({'status': 'Tenant activated'})


class BranchViewSet(viewsets.ModelViewSet):
    """Branch / Office ViewSet for tenant-specific locations."""
    serializer_class = BranchSerializer
    permission_classes = [IsTenantUser]

    def get_queryset(self):
        user = self.request.user
        # Honour the tenant a Super Admin has switched into (X-Tenant-ID via
        # TenantMiddleware), not just an explicit ?tenant_id= parameter.
        tenant = getattr(self.request, 'tenant', None) or getattr(user, 'tenant', None)
        if user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN':
            tenant_id = self.request.query_params.get('tenant_id')
            if tenant_id:
                return Branch.objects.filter(tenant_id=tenant_id)
            if tenant:
                return Branch.objects.filter(tenant=tenant)
            return Branch.objects.all()
        return Branch.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or user.role == 'SUPER_ADMIN'):
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()
