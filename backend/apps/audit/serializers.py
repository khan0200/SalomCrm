from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            'id', 'tenant', 'tenant_name', 'user', 'user_email', 'user_name',
            'action', 'entity_type', 'entity_id', 'description', 'changes',
            'ip_address', 'created_at'
        )
        read_only_fields = fields
