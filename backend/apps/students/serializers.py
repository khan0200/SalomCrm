import logging
from rest_framework import serializers
from .models import (
    Student, Folder, TariffOption, EducationLevelOption,
    StudentGroupOption, LeadSourceOption, CoordinatorOption
)
from .services import calculate_missing_documents
from .korean_translation_service import translate_name_to_korean

logger = logging.getLogger(__name__)

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


class StudentListSerializer(serializers.ModelSerializer):
    """
    Complete serializer for main student roster table and memory cache.
    """
    creator_name = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

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


class StudentDetailSerializer(serializers.ModelSerializer):
    """
    Full comprehensive serializer for Student Detail Drawer and standalone detail view.
    """
    creator_name = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

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
        read_only_fields = ('balance', 'discount', 'tenant', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        # Auto-compute initial missing documents checklist
        if 'pick_needed' not in validated_data or not validated_data['pick_needed']:
            validated_data['pick_needed'] = calculate_missing_documents(validated_data)

        # Auto-translate English Full Name to Korean Hangul if not explicitly provided
        if validated_data.get('full_name') and not validated_data.get('korean_name'):
            try:
                req = self.context.get('request')
                translated = translate_name_to_korean(validated_data['full_name'], request=req)
                if translated:
                    validated_data['korean_name'] = translated
            except Exception as e:
                logger.error(f"Auto-translation on student create failed: {e}")

        return Student.objects.create(**validated_data)

    def update(self, instance, validated_data):
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

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Auto-sync missing documents checklist
        instance.pick_needed = calculate_missing_documents({
            'phone1': instance.phone1,
            'passport': instance.passport,
            'address': instance.address,
            'father_phone': instance.father_phone,
            'mother_phone': instance.mother_phone,
            'level': instance.level,
            'pic_hand_count': instance.pic_hand_count
        })

        instance.save()
        return instance

    def to_representation(self, instance):
        return StudentDetailSerializer(instance, context=self.context).data


class StudentSetColorSerializer(serializers.Serializer):
    row_color = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status_row_color = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class StudentSetFoldersSerializer(serializers.Serializer):
    folder_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True, default=list)


class TariffOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TariffOption
        fields = ('id', 'name', 'price', 'created_at')
        read_only_fields = ('id', 'created_at')


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

