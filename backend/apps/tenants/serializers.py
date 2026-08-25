from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Tenant, Branch

User = get_user_model()

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        # Branch only defines id/name (+ tenant, created_at); listing fields the
        # model does not have raises ImproperlyConfigured at serializer build time.
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class TenantSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    branches = BranchSerializer(many=True, read_only=True)

    class Meta:
        model = Tenant
        fields = (
            'id', 'name', 'slug', 'is_active', 'logo_url',
            'description', 'settings', 'user_count', 'student_count',
            'branches', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')

    def get_user_count(self, obj):
        return obj.users.count()

    def get_student_count(self, obj):
        # Accessor comes from TenantAwareModel's related_name pattern
        # "%(app_label)s_%(class)s_set" -> students_student_set.
        count = getattr(obj, 'students_count', None)
        if count is not None:
            return count
        return obj.students_student_set.filter(is_deleted=False).count()


class TenantCreateWithAdminSerializer(serializers.ModelSerializer):
    """
    Transactional creation of Tenant along with its first Head Manager user.
    """
    admin_email = serializers.EmailField(write_only=True)
    admin_full_name = serializers.CharField(write_only=True)
    admin_password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Tenant
        fields = (
            'id', 'name', 'slug', 'is_active', 'logo_url',
            'description', 'admin_email', 'admin_full_name', 'admin_password'
        )

    @transaction.atomic
    def create(self, validated_data):
        admin_email = validated_data.pop('admin_email')
        admin_full_name = validated_data.pop('admin_full_name')
        admin_password = validated_data.pop('admin_password')

        # 1. Create Tenant
        tenant = Tenant.objects.create(**validated_data)

        # 2. Create Initial Head Manager
        user = User.objects.create_user(
            email=admin_email,
            password=admin_password,
            full_name=admin_full_name,
            role='HEAD_MANAGER',
            tenant=tenant,
            is_staff=True
        )

        # 3. Create default folders (e.g. KDB)
        from apps.students.models import Folder
        Folder.objects.create(tenant=tenant, name='KDB')

        # 4. Seed the shared default option lists. These are per-tenant: the
        # new agency starts from the same universities and university statuses
        # as everyone else, and its later edits stay its own.
        from apps.students.default_options import seed_default_options
        seed_default_options(tenant)

        return tenant
