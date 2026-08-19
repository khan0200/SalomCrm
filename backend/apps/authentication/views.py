from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from apps.core.permissions import IsPlatformSuperAdmin, IsTenantHeadManager, IsTenantUser
from .serializers import (
    CustomTokenObtainPairSerializer, UserSerializer,
    UserCreateUpdateSerializer, ChangePasswordSerializer
)

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom Token Obtain View returning rich user & tenant claims."""
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    """Returns currently authenticated user profile and permissions."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD for Tenant Users with strict tenant isolation:
    - Platform Super Admins can manage all users.
    - Tenant Head Managers can manage users within their tenant.
    """
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [IsTenantHeadManager()]
        return [IsTenantUser()]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return UserCreateUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN':
            tenant_id = self.request.query_params.get('tenant_id')
            if tenant_id:
                return User.objects.filter(tenant_id=tenant_id)
            return User.objects.all()
        return User.objects.filter(tenant=user.tenant)

    def perform_create(self, serializer):
        user = self.request.user
        # Enforce tenant assignment for non-superadmins
        if not (user.is_superuser or user.role == 'SUPER_ADMIN'):
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()
