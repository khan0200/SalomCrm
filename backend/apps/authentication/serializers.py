from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, Branch

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer enriching token with user details, role, and tenant info.
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
                'branding_color': user.tenant.branding_color,
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
            'branch', 'branch_name', 'avatar_url', 'phone',
            'telegram_id', 'telegram_username',
            'is_active', 'is_staff', 'date_joined'
        )
        read_only_fields = ('id', 'date_joined')


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'full_name', 'role', 'tenant',
            'branch', 'avatar_url', 'phone',
            'telegram_id', 'telegram_username', 'is_active'
        )

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
