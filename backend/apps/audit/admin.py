from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'entity_type', 'entity_id', 'tenant', 'user', 'created_at', 'ip_address')
    list_filter = ('action', 'entity_type', 'tenant', 'created_at')
    search_fields = ('action', 'entity_type', 'entity_id', 'description', 'user__email', 'tenant__name')
    readonly_fields = ('id', 'tenant', 'user', 'action', 'entity_type', 'entity_id', 'description', 'changes', 'ip_address', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
