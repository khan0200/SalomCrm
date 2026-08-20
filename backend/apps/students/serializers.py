from rest_framework import serializers
from .models import (
    Student, Folder, TariffOption, EducationLevelOption,
    StudentGroupOption, LeadSourceOption, CoordinatorOption
)
from .services import calculate_missing_documents

class FolderSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ('id', 'name', 'student_count', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_student_count(self, obj):
        return obj.students.filter(is_deleted=False).count()


class StudentListSerializer(serializers.ModelSerializer):
    """
    Lightweight, high-performance serializer for main student roster table.
    """
    folder_ids = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source='folders')

    class Meta:
        model = Student
        fields = (
            'id', 'full_name', 'korean_name', 'phone1', 'phone2',
            'level', 'level2', 'tariff', 'balance', 'discount',
            'language_certificate', 'certificate_score',
            'language_certificate_2', 'certificate_score_2',
            'language_certificate_3', 'certificate_score_3',
            'university_1', 'university_1_status', 'university_1_major',
            'university_2', 'university_2_status', 'university_2_major',
            'university_3', 'university_3_status', 'university_3_major',
            'university_4', 'university_4_status', 'university_4_major',
            'university_5', 'university_5_status', 'university_5_major',
            'office', 'student_group', 'lead_by', 'coordinator',
            'row_color', 'status_row_color', 'task_tags', 'folder_ids',
            'is_deleted', 'status_hidden', 'created_at'
        )


class StudentDetailSerializer(serializers.ModelSerializer):
    """
    Full comprehensive serializer for Student Detail Drawer and standalone detail view.
    """
    folder_ids = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source='folders')
    creator_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = '__all__'

    def get_creator_name(self, obj):
        return getattr(obj.created_by, 'full_name', None) if getattr(obj, 'created_by', None) else None


class StudentCreateUpdateSerializer(serializers.ModelSerializer):
    folder_ids = serializers.ListField(child=serializers.UUIDField(), required=False, write_only=True)

    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ('balance', 'discount', 'tenant', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        folder_ids = validated_data.pop('folder_ids', [])
        # Auto-compute initial missing documents checklist
        if 'pick_needed' not in validated_data or not validated_data['pick_needed']:
            validated_data['pick_needed'] = calculate_missing_documents(validated_data)

        student = Student.objects.create(**validated_data)
        if folder_ids:
            student.folders.set(folder_ids)
        return student

    def update(self, instance, validated_data):
        folder_ids = validated_data.pop('folder_ids', None)
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
        if folder_ids is not None:
            instance.folders.set(folder_ids)
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

