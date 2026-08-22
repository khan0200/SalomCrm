from datetime import datetime, date
from rest_framework import serializers
from apps.students.models import Student

def calculate_days_left(take_date_str):
    """
    Computes integer days remaining until KDB TAKE date.
    Returns None if no take date is configured.
    """
    if not take_date_str or take_date_str in ('NO KDB', 'KDB DONE', 'EDIT', 'None', ''):
        return None

    # Try common date formats
    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'):
        try:
            target_date = datetime.strptime(take_date_str.strip(), fmt).date()
            today = date.today()
            return (target_date - today).days
        except ValueError:
            continue
    return None


class StatusStudentListSerializer(serializers.ModelSerializer):
    """
    Serializer optimized for Status Page table (General and KDB modes).
    """
    days_left = serializers.SerializerMethodField()
    urgency = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = (
            'id', 'full_name', 'level', 'invoice', 'invoice_university',
            'coa', 'embassy', 'embassy_documents', 'status_hidden',
            'kdb_put_date', 'kdb_take_date', 'days_left', 'urgency',
            'embassy_father_docs', 'embassy_mother_docs', 'embassy_sponsor_notes',
            'status_row_color', 'folder_ids', 'created_at'
        )

    def get_days_left(self, obj):
        return calculate_days_left(obj.kdb_take_date)

    def get_urgency(self, obj):
        days = calculate_days_left(obj.kdb_take_date)
        if days is None:
            return None
        if days < 0:
            return 'OVERDUE'
        if days <= 3:
            return 'CRITICAL'
        if days <= 7:
            return 'URGENT'
        return 'NORMAL'


class StatusQuickUpdateSerializer(serializers.Serializer):
    """Serializer for rapid inline table updates on Status page."""
    invoice = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    coa = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    kdb_put_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    kdb_take_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    embassy = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status_hidden = serializers.BooleanField(required=False)
    status_row_color = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class EmbassyDrawerUpdateSerializer(serializers.Serializer):
    """Serializer for Embassy Documents Drawer updates."""
    embassy_father_docs = serializers.ListField(child=serializers.CharField(), required=False)
    embassy_mother_docs = serializers.ListField(child=serializers.CharField(), required=False)
    embassy_sponsor_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    embassy = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status_hidden = serializers.BooleanField(required=False)
