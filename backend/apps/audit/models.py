import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel

class AuditLog(TimeStampedModel):
    """
    Audit Log capturing security events, financial mutations, student updates,
    tenant creations, and administrative actions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs',
        db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        db_index=True
    )
    action = models.CharField(max_length=100, db_index=True)  # e.g. 'PAYMENT_CREATED', 'STUDENT_ARCHIVED'
    entity_type = models.CharField(max_length=100, db_index=True)  # e.g. 'Student', 'Payment', 'Tenant'
    entity_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'crm_audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.action}] {self.entity_type} {self.entity_id} by {self.user}"
