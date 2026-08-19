from django.contrib import admin
from .models import Payment, PaymentMethodTemplate, PaymentReceiverTemplate, PaymentNotePill

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'amount', 'method', 'received_by', 'is_discount', 'is_withdrawal', 'tenant', 'created_at')
    list_filter = ('tenant', 'method', 'received_by', 'is_discount', 'is_withdrawal', 'created_at')
    search_fields = ('student__id', 'student__full_name', 'student_name', 'notes', 'received_by', 'tenant__name')
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(PaymentMethodTemplate)
admin.site.register(PaymentReceiverTemplate)
admin.site.register(PaymentNotePill)
