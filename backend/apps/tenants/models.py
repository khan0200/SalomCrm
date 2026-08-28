import uuid
from django.db import models
from apps.core.models import TimeStampedModel, SimpleTenantModel

class Tenant(TimeStampedModel):
    """
    Tenant represents an organization/company on the Uniapp platform.
    Examples: 'Unibridge', 'Consulting A', 'Consulting B'.
    """
    id = models.CharField(max_length=64, primary_key=True, default=uuid.uuid4, editable=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    branding_color = models.CharField(max_length=32, default='#007aff')
    description = models.TextField(blank=True, null=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'crm_tenants'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.slug})"


class Branch(SimpleTenantModel):
    """
    Branch or Office location belonging to a specific tenant.
    Mapped directly to 'offices' table.
    Examples: 'ANDIJON OFFIS', 'TOSHKENT OFFIS'.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=100, blank=True, default='Building2')

    class Meta:
        db_table = 'offices'
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"

