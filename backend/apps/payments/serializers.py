from rest_framework import serializers
from .models import Payment, PaymentMethodTemplate, PaymentReceiverTemplate, PaymentNotePill
from apps.students.models import Student

class PaymentSerializer(serializers.ModelSerializer):
    student_id = serializers.SerializerMethodField()
    student_full_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            'id', 'student_id', 'student_full_name', 'student_name',
            'amount', 'method', 'received_by', 'notes',
            'is_discount', 'is_withdrawal', 'created_by_name',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_student_id(self, obj):
        if obj.student:
            return obj.student.id
        if obj.student_id:
            return obj.student_id.lstrip('P') if obj.student_id.startswith('P') else obj.student_id
        return None

    def get_student_full_name(self, obj):
        if obj.student and obj.student.full_name:
            return obj.student.full_name
        return obj.student_name or None

    def get_created_by_name(self, obj):
        try:
            if obj.created_by:
                return obj.created_by.full_name or obj.created_by.email or 'Staff'
        except Exception:
            pass
        return obj.received_by or 'Staff'


class PaymentCreateSerializer(serializers.Serializer):
    student_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    method = serializers.CharField(max_length=100)
    received_by = serializers.CharField(max_length=100)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_discount = serializers.BooleanField(default=False)


class PaymentWithdrawSerializer(serializers.Serializer):
    student_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    reason = serializers.CharField(max_length=255)


class PaymentEditSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    method = serializers.CharField(max_length=100)
    received_by = serializers.CharField(max_length=100)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class PaymentOverviewStudentSerializer(serializers.ModelSerializer):
    """
    Student financial overview serializer with formatted tariff, balance, and discount.

    total_payments/total_withdrawals come from annotate()d queryset fields (see
    PaymentOverviewViewSet.get_queryset) so they're plain DecimalFields here, not
    SerializerMethodFields -- keeps the Payments Kanban board's per-student sums
    to one query for the whole list instead of one query per student.
    """
    total_payments = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_withdrawals = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Student
        fields = (
            'id', 'full_name', 'tariff', 'balance', 'discount',
            'student_group', 'is_deleted', 'is_permanently_deleted', 'phone1', 'office',
            'coordinator', 'level', 'level2', 'total_payments', 'total_withdrawals'
        )


class PaymentMethodTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethodTemplate
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class PaymentReceiverTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReceiverTemplate
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class PaymentNotePillSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentNotePill
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')

