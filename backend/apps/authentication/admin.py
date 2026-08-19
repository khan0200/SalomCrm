from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'role', 'tenant', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'tenant', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name', 'tenant__name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone', 'avatar_url')}),
        ('Tenant & Permissions', {'fields': ('role', 'tenant', 'branch', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'tenant', 'password', 'is_active', 'is_staff'),
        }),
    )
