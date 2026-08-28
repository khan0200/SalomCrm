from django.contrib import admin
from .models import Tenant, Branch

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'id', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'id')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'tenant', 'created_at')
    list_filter = ('tenant',)
    search_fields = ('name', 'tenant__name')

    readonly_fields = ('created_at',)
