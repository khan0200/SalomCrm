from django.contrib import admin
from .models import (
    Student, Folder, TariffOption, EducationLevelOption,
    StudentGroupOption, LeadSourceOption, CoordinatorOption, TagOption
)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'tenant', 'tariff', 'balance', 'level', 'office', 'student_group', 'is_deleted', 'status_hidden', 'created_at')
    list_filter = ('tenant', 'tariff', 'level', 'office', 'student_group', 'is_deleted', 'status_hidden')
    search_fields = ('id', 'full_name', 'passport', 'phone1', 'phone2', 'tenant__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'created_at')
    list_filter = ('tenant',)
    search_fields = ('name', 'tenant__name')


@admin.register(TariffOption)
class TariffOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'tenant')
    list_filter = ('tenant',)


@admin.register(TagOption)
class TagOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'tenant')
    list_filter = ('tenant',)


admin.site.register(EducationLevelOption)
admin.site.register(StudentGroupOption)
admin.site.register(LeadSourceOption)
admin.site.register(CoordinatorOption)
