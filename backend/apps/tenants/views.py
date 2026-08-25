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

    @action(detail=True, methods=['get'], permission_classes=[IsPlatformSuperAdmin])
    def admins(self, request, pk=None):
        """
        Head Managers of this tenant. A tenant can have several, so the client
        must name which one to act on rather than guessing at "the" admin.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        tenant = self.get_object()
        admins = User.objects.filter(
            tenant=tenant, role='HEAD_MANAGER'
        ).order_by('date_joined')
        return Response([
            {
                'id': str(u.id),
                'email': u.email,
                'full_name': u.full_name,
                'is_active': u.is_active,
            }
            for u in admins
        ])

    @action(detail=True, methods=['post'], url_path='admin-credentials',
            permission_classes=[IsPlatformSuperAdmin])
    def admin_credentials(self, request, pk=None):
        """
        Update one tenant admin's login email and/or password.

        Credentials belong to a User, not to the Tenant row, so the target
        user_id is required and must belong to this tenant.
        """
        from django.contrib.auth import get_user_model
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.contrib.auth.password_validation import validate_password
        User = get_user_model()

        tenant = self.get_object()
        user_id = request.data.get('user_id')
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''
        full_name = (request.data.get('full_name') or '').strip()

        if not user_id:
            return Response({'detail': 'user_id is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        target = User.objects.filter(id=user_id, tenant=tenant).first()
        if not target:
            return Response({'detail': 'That user does not belong to this tenant.'},
                            status=status.HTTP_404_NOT_FOUND)

        updated = []

        if email and email != target.email:
            if User.objects.filter(email__iexact=email).exclude(id=target.id).exists():
                return Response({'detail': 'That email is already in use.'},
                                status=status.HTTP_400_BAD_REQUEST)
            target.email = email
            updated.append('email')

        if full_name and full_name != target.full_name:
            target.full_name = full_name
            updated.append('full_name')

        if password:
            try:
                validate_password(password, target)
            except DjangoValidationError as e:
                return Response({'detail': ' '.join(str(m) for m in e.messages)},
                                status=status.HTTP_400_BAD_REQUEST)
            target.set_password(password)
            updated.append('password')

        if not updated:
            return Response({'detail': 'Nothing to update.'},
                            status=status.HTTP_400_BAD_REQUEST)

        target.save()
        return Response({
            'status': 'Credentials updated',
            'updated': updated,
            'user': {
                'id': str(target.id),
                'email': target.email,
                'full_name': target.full_name,
            },
        })


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
