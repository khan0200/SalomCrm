import logging
from rest_framework import serializers
from .models import (
    Student, Folder, TariffOption, EducationLevelOption,
    StudentGroupOption, LeadSourceOption, CoordinatorOption, StudentUserPreference,
    Contract
)
from .korean_translation_service import translate_name_to_korean

logger = logging.getLogger(__name__)


class MyPreferenceFieldsMixin:
    """
    Adds my_row_color/my_task_tags -- the current viewer's own "Only Me"
    color/tags for a student, private and never shared with other users.

    Resolved in bulk via context['my_prefs_by_student'] (populated by the
    view for the exact page/row being serialized, avoiding N+1 queries on
    the up-to-5000-row master roster fetch). Falls back to a single-row
    query when that bulk context isn't present (e.g. serializer used
    standalone outside the view's list()/retrieve() overrides).
    """
    def get_my_row_color(self, obj):
        pref = self._get_my_pref(obj)
        return pref.row_color if pref else None

    def get_my_task_tags(self, obj):
        pref = self._get_my_pref(obj)
        return pref.task_tags if pref else []

    def _get_my_pref(self, obj):
        prefs_by_student = self.context.get('my_prefs_by_student')
        if prefs_by_student is not None:
            return prefs_by_student.get(obj.id)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return None
        return StudentUserPreference.objects.filter(student_id=obj.id, user=user).first()


class FolderSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ('id', 'name', 'student_count', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_student_count(self, obj):
        tenant = getattr(self.context.get('request'), 'tenant', None)
        qs = Student.objects.filter(is_deleted=False, folder_ids__contains=[obj.id])
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs.count()


class StudentListSerializer(MyPreferenceFieldsMixin, serializers.ModelSerializer):
    """
    Complete serializer for main student roster table and memory cache.
    """
    creator_name = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    my_row_color = serializers.SerializerMethodField()
    my_task_tags = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = '__all__'

    def get_creator_name(self, obj):
        try:
            if obj.created_by:
                return getattr(obj.created_by, 'full_name', None) or getattr(obj.created_by, 'email', None)
        except Exception:
            return None
        return None

    def get_created_by(self, obj):
        return str(obj.created_by_id) if obj.created_by_id else None


class StudentDetailSerializer(MyPreferenceFieldsMixin, serializers.ModelSerializer):
    """
    Full comprehensive serializer for Student Detail Drawer and standalone detail view.
    """
    creator_name = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    my_row_color = serializers.SerializerMethodField()
    my_task_tags = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = '__all__'

    def get_creator_name(self, obj):
        try:
            if obj.created_by:
                return getattr(obj.created_by, 'full_name', None) or getattr(obj.created_by, 'email', None)
        except Exception:
            return None
        return None

    def get_created_by(self, obj):
        return str(obj.created_by_id) if obj.created_by_id else None



class StudentCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = (
            'balance', 'discount', 'tenant', 'created_by',
            'created_at', 'updated_at',
            'payment_id',  # Immutable — set once on create, never via API
        )

    def validate_birthday(self, value):
        if value:
            from apps.students.services import normalize_date_to_iso
            return normalize_date_to_iso(value)
        return value

    def validate_passport_issue_date(self, value):
        if value:
            from apps.students.services import normalize_date_to_iso
            return normalize_date_to_iso(value)
        return value

    def validate_passport_expire_date(self, value):
        if value:
            from apps.students.services import normalize_date_to_iso
            return normalize_date_to_iso(value)
        return value

    def create(self, validated_data):
        # pick_needed is a manual checklist (PICK_NEEDED_LIST on the frontend);
        # it is no longer auto-computed here. It previously used its own label
        # set (TELEFON, PASSPORT, MANZIL, OTA-ONA, DIPLOM / ATTESTAT, BAKALAVR
        # DIPLOM, 3x4 RASM) that overlapped, under different names, with pills
        # the checklist already has (2 ta nomer, Foreign passport, Manzil,
        # 3.5x4.5) and forcibly reset on every save regardless of what the
        # client sent, so removing a pill could never actually persist.
        validated_data.setdefault('pick_needed', [])

        # Auto-translate English Full Name to Korean Hangul if not explicitly provided
        if validated_data.get('full_name') and not validated_data.get('korean_name'):
            try:
                req = self.context.get('request')
                translated = translate_name_to_korean(validated_data['full_name'], request=req)
                if translated:
                    validated_data['korean_name'] = translated
            except Exception as e:
                logger.error(f"Auto-translation on student create failed: {e}")

        student = Student.objects.create(**validated_data)

        # A tariff assigned at creation must immediately set balance to
        # -tariff_price, same as assigning one later via update().
        if student.tariff:
            from apps.payments.services import recalculate_student_financials
            student = recalculate_student_financials(student)

        return student

    def update(self, instance, validated_data):
        # ── Student ID (primary key) rename ───────────────────────────────────
        # Student.id is a CharField PK. Django cannot UPDATE a PK in-place.
        # Since payments now FK to the immutable payment_id field (not id),
        # we can safely rename id via raw SQL UPDATE — no cascade, no SET_NULL,
        # no payment re-linking needed at all.
        raw_new_id = validated_data.get('id')
        old_id = instance.pk
        if raw_new_id and str(raw_new_id).strip().upper() != str(old_id).strip().upper():
            from django.db import connection, transaction

            new_id_upper = str(raw_new_id).strip().upper()

            with transaction.atomic():
                # Raw SQL UPDATE on id — bypasses Django's PK-change restriction.
                # payment_id is NOT updated (stays as original e.g. 'PT207').
                # All other field changes are applied in the same transaction.
                other_fields = {k: v for k, v in validated_data.items() if k != 'id'}
                for attr, value in other_fields.items():
                    setattr(instance, attr, value)

                # First rename id via raw SQL (no FK cascades since payments
                # reference payment_id, not id)
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE students SET id = %s WHERE id = %s",
                        [new_id_upper, old_id]
                    )

                # Now save remaining field changes (update_fields avoids
                # touching id or payment_id)
                if other_fields:
                    instance.pk = new_id_upper
                    instance.save(update_fields=list(other_fields.keys()) + ['updated_at'])
                else:
                    instance.pk = new_id_upper

                logger.info(
                    f"Student ID renamed {old_id} -> {new_id_upper} via raw SQL. "
                    f"payment_id '{instance.payment_id}' unchanged."
                )

            return instance
        # ── End ID rename handling ────────────────────────────────────────────

        # If full_name was changed and korean_name was NOT explicitly sent, auto-translate full_name to Korean
        if 'full_name' in validated_data and validated_data['full_name']:
            new_name = validated_data['full_name'].strip()
            old_name = (instance.full_name or '').strip()
            if new_name != old_name and 'korean_name' not in validated_data:
                try:
                    req = self.context.get('request')
                    translated = translate_name_to_korean(new_name, request=req)
                    if translated:
                        instance.korean_name = translated
                except Exception as e:
                    logger.error(f"Auto-translation on student update failed: {e}")

        # Detect tariff/certificate changes before overwriting instance fields,
        # since E-VISA pricing depends on both.
        financials_changed = (
            ('tariff' in validated_data and validated_data['tariff'] != instance.tariff) or
            ('language_certificate' in validated_data and
             validated_data['language_certificate'] != instance.language_certificate)
        )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # pick_needed is no longer force-recomputed here (see create() above):
        # whatever the client sent for it in validated_data was already applied
        # by the loop above, and is left alone.

        instance.save()

        # Recompute balance immediately so the tariff price becomes debt
        # (balance = -tariff_price plus existing payments/discounts/withdrawals)
        # rather than sitting at 0 until a payment happens to be recorded.
        # This must be synchronous, not deferred, since external consumers
        # (e.g. the Telegram bot) may read balance right after this request.
        if financials_changed:
            from apps.payments.services import recalculate_student_financials
            # The tariff itself changed, so re-capture the price: the student is
            # now owed against the newly chosen tariff's current price, not the
            # one captured for the tariff they moved off.
            instance = recalculate_student_financials(instance, reprice=True)

        return instance

    def to_representation(self, instance):
        return StudentDetailSerializer(instance, context=self.context).data


class StudentSetColorSerializer(serializers.Serializer):
    row_color = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status_row_color = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    scope = serializers.ChoiceField(choices=['mine', 'all'], required=False, default='all')


class StudentSetFoldersSerializer(serializers.Serializer):
    folder_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True, default=list)


class TariffOptionSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = TariffOption
        fields = ('id', 'name', 'price', 'contract_text', 'is_active', 'created_at', 'student_count')
        read_only_fields = ('id', 'created_at')

    def get_student_count(self, obj):
        from apps.students.models import Student
        return Student.objects.filter(tenant=obj.tenant, tariff=obj.name).count()


class EducationLevelOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevelOption
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class StudentGroupOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentGroupOption
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class LeadSourceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadSourceOption
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class CoordinatorOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoordinatorOption
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class UniversityOptionSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import UniversityOption
        model = UniversityOption
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class UniversityStatusOptionSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import UniversityStatusOption
        model = UniversityStatusOption
        fields = ('id', 'name', 'color_class', 'created_at')
        read_only_fields = ('id', 'created_at')


class TagOptionSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import TagOption
        model = TagOption
        fields = ('id', 'name', 'icon', 'created_at')
        read_only_fields = ('id', 'created_at')


class SchoolDirectorySerializer(serializers.ModelSerializer):
    class Meta:
        from .models import SchoolDirectory
        model = SchoolDirectory
        fields = ('id', 'name', 'address', 'website', 'phone', 'email', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class WorkplaceDirectorySerializer(serializers.ModelSerializer):
    class Meta:
        from .models import WorkplaceDirectory
        model = WorkplaceDirectory
        fields = ('id', 'name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class JobTitleDirectorySerializer(serializers.ModelSerializer):
    class Meta:
        from .models import JobTitleDirectory
        model = JobTitleDirectory
        fields = ('id', 'name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class MajorOptionSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import MajorOption
        model = MajorOption
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class B2BOptionSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import B2BOption
        model = B2BOption
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class VisaStudentSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import VisaStudent
        model = VisaStudent
        fields = (
            'id', 'student_id', 'full_name', 'passport', 'birthday', 'visa_type',
            'application_no', 'status', 'application_date', 'status_date',
            'last_checked', 'rejection_reason', 'pdf_url', 'api_response',
            'tariff', 'university', 'coordinator', 'b2b',
            'flag', 'refund_application', 'pinned', 'batch_selected',
            'is_deleted', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ContractListSerializer(serializers.ModelSerializer):
    student_id = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    student_passport = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    rejected_by_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = (
            'id', 'contract_number', 'title', 'template_name',
            'content', 'signature_data',
            'student', 'student_id', 'student_name', 'student_passport',
            'status', 'version', 'is_deleted', 'is_archived', 'archived_at',
            'tariff_name', 'tariff_price', 'discount', 'email', 'office', 'phone1', 'phone2',
            'education_level', 'date_of_birth', 'full_name', 'passport_number',
            'student_id_assigned', 'verification_code', 'verification_code_expires_at',
            'verification_code_used', 'verified_at', 'rejection_reason',
            'rejected_at', 'rejected_by_name',
            'created_at', 'updated_at', 'signed_at', 'created_by_name'
        )
        read_only_fields = ('id', 'version', 'created_at', 'updated_at')

    def get_student_id(self, obj):
        return obj.student_id_assigned or (obj.student.id if obj.student else None)

    def get_student_name(self, obj):
        return obj.full_name or (obj.student.full_name if obj.student else None)

    def get_student_passport(self, obj):
        return obj.passport_number or (obj.student.passport if obj.student else None)

    def get_created_by_name(self, obj):
        if obj.created_by:
            return getattr(obj.created_by, 'full_name', None) or getattr(obj.created_by, 'email', None) or str(obj.created_by)
        return None

    def get_rejected_by_name(self, obj):
        if obj.rejected_by:
            return getattr(obj.rejected_by, 'full_name', None) or getattr(obj.rejected_by, 'email', None) or str(obj.rejected_by)
        return None

    def get_email(self, obj):
        if obj.student_account and getattr(obj.student_account, 'email', None):
            return obj.student_account.email
        if obj.student and getattr(obj.student, 'email', None):
            return obj.student.email
        if obj.snapshot_data and isinstance(obj.snapshot_data, dict):
            return obj.snapshot_data.get('email', '')
        return ''


class ContractDetailSerializer(serializers.ModelSerializer):
    student_id = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    student_passport = serializers.SerializerMethodField()
    student_phone = serializers.SerializerMethodField()
    student_tariff = serializers.SerializerMethodField()
    student_university = serializers.CharField(source='student.university_1', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()
    rejected_by_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = (
            'id', 'contract_number', 'title', 'template_name',
            'content', 'status', 'version', 'is_deleted', 'is_archived', 'archived_at',
            'student', 'student_id', 'student_name', 'student_passport',
            'student_phone', 'student_tariff', 'student_university',
            'tariff_name', 'tariff_price', 'discount', 'email', 'passport_number', 'full_name',
            'education_level', 'date_of_birth', 'office', 'phone1', 'phone2',
            'signature_data', 'is_minor', 'guardian_full_name', 'guardian_passport_number',
            'guardian_relation', 'guardian_phone', 'guardian_address', 'guardian_signature_data',
            'declarations_accepted', 'agreement_confirmations',
            'contract_hash', 'student_id_assigned', 'verification_code',
            'verification_code_expires_at', 'verification_code_generated_at',
            'verification_code_used', 'verified_at', 'rejection_reason',
            'rejected_at', 'rejected_by_name', 'sign_token', 'signed_at', 'signer_ip', 'signer_user_agent',
            'created_at', 'updated_at', 'created_by_name', 'updated_by_name'
        )
        read_only_fields = ('id', 'version', 'created_at', 'updated_at')

    def get_student_id(self, obj):
        return obj.student_id_assigned or (obj.student.id if obj.student else None)

    def get_student_name(self, obj):
        return obj.full_name or (obj.student.full_name if obj.student else None)

    def get_student_passport(self, obj):
        return obj.passport_number or (obj.student.passport if obj.student else None)

    def get_student_phone(self, obj):
        return obj.phone1 or (obj.student.phone1 if obj.student else None)

    def get_student_tariff(self, obj):
        return obj.tariff_name or (obj.student.tariff if obj.student else None)

    def get_created_by_name(self, obj):
        if obj.created_by:
            return getattr(obj.created_by, 'full_name', None) or getattr(obj.created_by, 'email', None) or str(obj.created_by)
        return None

    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return getattr(obj.updated_by, 'full_name', None) or getattr(obj.updated_by, 'email', None) or str(obj.updated_by)
        return None

    def get_rejected_by_name(self, obj):
        if obj.rejected_by:
            return getattr(obj.rejected_by, 'full_name', None) or getattr(obj.rejected_by, 'email', None) or str(obj.rejected_by)
        return None

    def get_email(self, obj):
        if obj.student_account and getattr(obj.student_account, 'email', None):
            return obj.student_account.email
        if obj.student and getattr(obj.student, 'email', None):
            return obj.student.email
        if obj.snapshot_data and isinstance(obj.snapshot_data, dict):
            return obj.snapshot_data.get('email', '')
        return ''


class ContractCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = (
            'id', 'student', 'contract_number', 'title',
            'template_name', 'content', 'status', 'version'
        )
        read_only_fields = ('id', 'version')


