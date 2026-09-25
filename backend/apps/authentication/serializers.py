from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, Branch
from .models import UserRole, DataScope

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer enriching token with user details, role, and tenant info.

    Only reached by the internal CRM login (/api/auth/login/). The online
    student portal issues its own tokens via get_token() directly (see
    StudentSignUpView / StudentSignInView), bypassing validate() entirely -
    so the STUDENT check below only ever blocks a student's credentials
    from being used on the staff-facing login page, never the student
    portal itself.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['role'] = user.role
        token['tenant_id'] = str(user.tenant_id) if user.tenant_id else None
        token['is_superuser'] = user.is_superuser
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        if user.role == UserRole.STUDENT:
            raise AuthenticationFailed(
                "Bu talaba hisobi. Iltimos, o'z konsalting kompaniyangizning "
                "onlayn shartnomalar portali orqali kiring.",
                code='student_account'
            )

        data['user'] = {
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'avatar_url': user.avatar_url,
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
        return data


class UserSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'full_name', 'role', 'tenant', 'tenant_name',
            'branch', 'branch_name', 'data_scope', 'avatar_url', 'phone',
            'telegram_id', 'telegram_username',
            'is_active', 'is_staff', 'date_joined'
        )
        read_only_fields = ('id', 'date_joined')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.tenant:
            data['tenant'] = {
                'id': str(instance.tenant.id),
                'name': instance.tenant.name,
                'slug': instance.tenant.slug,
                'logo_url': instance.tenant.logo_url
            }
        return data


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'full_name', 'role', 'tenant',
            'branch', 'data_scope', 'avatar_url', 'phone',
            'telegram_id', 'telegram_username', 'is_active'
        )
        # The view sets the tenant from the request context; accepting it from
        # the client would let a caller place a user in another tenant.
        read_only_fields = ('tenant',)

    def get_fields(self):
        # Narrow the `branch` choices to the target tenant's own branches.
        # Without this, the auto-generated PrimaryKeyRelatedField accepts any
        # Branch UUID platform-wide, so a Head Manager could assign a staff
        # member to another agency's office by ID. On update the tenant is
        # pinned to the existing user's (perform_update never lets it move);
        # on create it's whichever tenant the request will create into (see
        # UserViewSet._target_tenant) - the same two cases the view itself
        # already distinguishes.
        fields = super().get_fields()
        if self.instance is not None:
            target_tenant = self.instance.tenant
        else:
            request = self.context.get('request')
            requester = getattr(request, 'user', None) if request else None
            target_tenant = (getattr(request, 'tenant', None) or getattr(requester, 'tenant', None)) if request else None
        if target_tenant is not None:
            fields['branch'].queryset = Branch.objects.filter(tenant=target_tenant)
        return fields

    def validate_role(self, value):
        # This serializer only backs UserViewSet's create/update, which
        # get_permissions() already restricts to Head Managers (or a real
        # platform Super Admin). Without this check, a Head Manager could
        # send role=SUPER_ADMIN directly - bypassing the AddStaffModal
        # dropdown, which only offers roles up to their own - and grant
        # platform-wide power to a user whose tenant stays pinned to their
        # own agency. STUDENT is excluded too: that role is only ever
        # created by the online-contract sign-up flow, never this endpoint.
        request = self.context.get('request')
        requester = getattr(request, 'user', None) if request else None
        is_platform_super_admin = bool(
            requester and (requester.is_superuser or requester.role == UserRole.SUPER_ADMIN)
        )
        if value in (UserRole.SUPER_ADMIN, UserRole.STUDENT) and not is_platform_super_admin:
            raise serializers.ValidationError(
                'Only a Platform Super Admin can assign this role.'
            )
        return value

    def validate(self, attrs):
        unset = object()
        role = attrs.get('role', getattr(self.instance, 'role', None))

        if role == UserRole.SUPER_ADMIN:
            # Platform-wide by definition (tenant=None) - "own branch" is a
            # meaningless concept for this role, so never let a stored
            # BRANCH_ONLY value linger from before a promotion.
            attrs['data_scope'] = DataScope.ALL
        else:
            # A tenant can have several HEAD_MANAGER accounts (per-branch
            # heads alongside the agency's actual owner), so - unlike role -
            # data_scope is a per-person setting even for HEAD_MANAGER/MANAGER.
            scope = attrs.get('data_scope', getattr(self.instance, 'data_scope', DataScope.ALL))
            if scope == DataScope.BRANCH_ONLY:
                branch = attrs.get('branch', unset)
                if branch is unset:
                    branch = getattr(self.instance, 'branch', None)
                if branch is None:
                    raise serializers.ValidationError({
                        'data_scope': "Filialga cheklash uchun avval xodimga filial biriktiring."
                    })

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)
