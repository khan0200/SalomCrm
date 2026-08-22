import uuid
from typing import Any
from django.db import models
from django.conf import settings

class TimeStampedModel(models.Model):
    """Abstract model providing self-updating created_at and updated_at fields."""
    id: Any
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantManager(models.Manager):
    """Manager that automatically scopes querysets by tenant."""
    def get_queryset(self):
        return super().get_queryset()


class TenantAwareModel(TimeStampedModel):
    """
    Abstract model for every entity that belongs strictly to a tenant.
    Guarantees tenant field and created_by audit link.
    """
    id: Any
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        db_column='tenant_id',
        db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        db_column='created_by_id',
        db_index=True
    )

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True


class SimpleTenantModel(models.Model):
    """
    Abstract model for lightweight option/lookup tables belonging to a tenant (without updated_at / created_by).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        db_column='tenant_id',
        db_index=True
    )

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
