from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.db.models import Q
from apps.core.permissions import IsPlatformSuperAdmin, IsTenantHeadManager, IsTenantUser
from .serializers import (
    CustomTokenObtainPairSerializer, UserSerializer,
    UserCreateUpdateSerializer, ChangePasswordSerializer
)
from .telegram_auth import verify_telegram_authorization

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom Token Obtain View returning rich user & tenant claims."""
    serializer_class = CustomTokenObtainPairSerializer


class TelegramAuthView(APIView):
    """
    Authenticates users via the Official Telegram Login Widget.
    Validates HMAC-SHA256 signature and returns JWT tokens.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        is_valid, error_msg = verify_telegram_authorization(data)
        if not is_valid:
            return Response({'detail': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        telegram_id = str(data.get('id'))
        telegram_username = data.get('username')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        photo_url = data.get('photo_url')

        # 1. Match by telegram_id
        user = User.objects.filter(telegram_id=telegram_id).first()

        # 2. If not found by telegram_id, try matching by telegram_username
        if not user and telegram_username:
            user = User.objects.filter(
                Q(telegram_username__iexact=telegram_username) |
                Q(email__istartswith=f"{telegram_username}@")
            ).first()
            if user:
                user.telegram_id = telegram_id
                user.save(update_fields=['telegram_id'])

        # 3. If still not found, return a helpful error
        if not user:
            # Check if there is only 1 superadmin and no users yet (or first setup)
            tg_handle = f"@{telegram_username}" if telegram_username else f"ID: {telegram_id}"
            return Response({
                'detail': f"No CRM account found for Telegram user {tg_handle}. Please ask your administrator to link your Telegram username in CRM User Management."
            }, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            return Response({'detail': 'Your CRM user account is inactive. Please contact support.'}, status=status.HTTP_403_FORBIDDEN)

        # Update avatar or username if available
        updated_fields = []
        if telegram_username and user.telegram_username != telegram_username:
            user.telegram_username = telegram_username
            updated_fields.append('telegram_username')
        if photo_url and not user.avatar_url:
            user.avatar_url = photo_url
            updated_fields.append('avatar_url')
        if updated_fields:
            user.save(update_fields=updated_fields)

        # Generate JWT tokens
        refresh = CustomTokenObtainPairSerializer.get_token(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'avatar_url': user.avatar_url,
                'telegram_id': user.telegram_id,
                'telegram_username': user.telegram_username,
                'is_superuser': user.is_superuser,
                'tenant': {
                    'id': str(user.tenant.id),
                    'name': user.tenant.name,
                    'slug': user.tenant.slug,
                    'logo_url': user.tenant.logo_url
                } if user.tenant else None,
                'branch': {
                    'id': str(user.branch.id),
                    'name': user.branch.name
                } if user.branch else None
            }
        }, status=status.HTTP_200_OK)


class TelegramLinkView(APIView):
    """Allows an authenticated user to link or unlink their Telegram account."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        is_valid, error_msg = verify_telegram_authorization(data)
        if not is_valid:
            return Response({'detail': error_msg}, status=status.HTTP_400_BAD_REQUEST)

        telegram_id = str(data.get('id'))
        telegram_username = data.get('username')

        # Check if already linked to another user
        existing = User.objects.filter(telegram_id=telegram_id).exclude(id=request.user.id).first()
        if existing:
            return Response({'detail': f'This Telegram account is already linked to user {existing.email}.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.telegram_id = telegram_id
        if telegram_username:
            user.telegram_username = telegram_username
        if data.get('photo_url') and not user.avatar_url:
            user.avatar_url = data.get('photo_url')
        user.save()

        return Response({'message': 'Telegram account successfully linked!', 'user': UserSerializer(user).data})


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
        # Mutating another user (or any role change) is a Head Manager action.
        # Without this, a STAFF user could PATCH their own role to HEAD_MANAGER.
        if self.action in ('create', 'destroy', 'update', 'partial_update'):
            return [IsTenantHeadManager()]
        return [IsTenantUser()]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return UserCreateUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        # request.tenant is set by TenantMiddleware from the X-Tenant-ID header
        # when a Super Admin switches into a tenant's context. Ignoring it here
        # leaked every tenant's users into that tenant's Staff page.
        tenant = getattr(self.request, 'tenant', None) or getattr(user, 'tenant', None)
        if user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN':
            tenant_id = self.request.query_params.get('tenant_id')
            if tenant_id:
                return User.objects.filter(tenant_id=tenant_id)
            if tenant:
                return User.objects.filter(tenant=tenant)
            return User.objects.all()
        return User.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        user = self.request.user
        # Enforce tenant assignment for non-superadmins
        if not (user.is_superuser or user.role == 'SUPER_ADMIN'):
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        # Never allow a tenant user to move someone into another tenant.
        if not (user.is_superuser or user.role == 'SUPER_ADMIN'):
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        # A head manager must not delete their own account (would lock the
        # agency out of staff management), nor a platform super admin.
        if instance.pk == user.pk:
            raise ValidationError('You cannot delete your own account.')
        if instance.role == 'SUPER_ADMIN' and not (
            user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN'
        ):
            raise PermissionDenied('You cannot delete a platform super admin.')
        instance.delete()

