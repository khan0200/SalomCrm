import re
import io
from typing import Any
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.db.models import Q
from apps.core.permissions import IsTenantUser, IsTenantHeadManager
from .models import (
    Student, Folder, TariffOption, EducationLevelOption,
    StudentGroupOption, LeadSourceOption, CoordinatorOption,
    UniversityOption, UniversityStatusOption, SchoolDirectory, MajorOption
)
from .serializers import (
    StudentListSerializer, StudentDetailSerializer, StudentCreateUpdateSerializer,
    StudentSetColorSerializer, StudentSetFoldersSerializer, FolderSerializer,
    TariffOptionSerializer, EducationLevelOptionSerializer, StudentGroupOptionSerializer,
    LeadSourceOptionSerializer, CoordinatorOptionSerializer,
    UniversityOptionSerializer, UniversityStatusOptionSerializer,
    SchoolDirectorySerializer, MajorOptionSerializer
)
from .services import archive_student, restore_student, permanent_delete_student

def alphanumeric_key(student_id):
    """
    Sort key for alphanumeric student IDs matching Uniapp v2 logic.
    Splits into prefix and numeric components (e.g. 'UB120' -> ('UB', 120)).
    """
    if not student_id:
        return ("", 0)
    match = re.match(r'^([A-Za-z\s_-]*)(\d*)$', str(student_id).strip())
    if match:
        prefix = match.group(1).upper()
        num = int(match.group(2)) if match.group(2) else 0
        return (prefix, num)
    return (str(student_id).upper(), 0)


class StudentViewSet(viewsets.ModelViewSet):
    """
    Enterprise Student Management ViewSet with server-side filtering,
    alphanumeric ID sorting, folder scopes, soft archive/restore, and color tagging.
    """
    permission_classes = [IsTenantUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return StudentCreateUpdateSerializer
        return StudentDetailSerializer

    def get_queryset(self):
        req: Any = self.request
        user = req.user
        params = getattr(req, 'query_params', getattr(req, 'GET', {}))
        tenant = getattr(req, 'tenant', None) or getattr(user, 'tenant', None)

        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'role', '') == 'SUPER_ADMIN'

        if is_super:
            tenant_param = params.get('tenant_id')
            if tenant_param:
                qs = Student.objects.filter(tenant_id=tenant_param)
            elif tenant:
                qs = Student.objects.filter(tenant=tenant)
            else:
                qs = Student.objects.all()
        else:
            qs = Student.objects.filter(tenant=tenant)

        # For detail actions (retrieve, update, set_color, set_folders, etc.), return base queryset
        if self.action != 'list':
            return qs.prefetch_related('folders')

        # ── 1. Folder & Archive/Hidden Scopes ──────────────────────────────
        folder = params.get('folder', 'all')
        include_archive = str(params.get('include_archive', 'false')).lower() == 'true'

        if folder == 'deleted' or folder == 'archive':
            qs = qs.filter(is_deleted=True)
        elif folder == 'hidden':
            qs = qs.filter(is_deleted=False, status_hidden=True)
        elif folder == 'except':
            qs = qs.filter(is_deleted=False, folders__isnull=True)
        elif folder != 'all':
            qs = qs.filter(is_deleted=False, folders__id=folder)
        else:
            if not include_archive:
                qs = qs.filter(is_deleted=False)

        # ── 2. Search Filter ──────────────────────────────────────────────
        search_query = str(params.get('search', '')).strip()
        search_mode = params.get('search_mode', 'all')

        if search_query:
            if search_mode == 'id':
                qs = qs.filter(id__icontains=search_query)
            else:
                qs = qs.filter(
                    Q(id__icontains=search_query) |
                    Q(full_name__icontains=search_query) |
                    Q(korean_name__icontains=search_query) |
                    Q(passport__icontains=search_query) |
                    Q(phone1__icontains=search_query) |
                    Q(phone2__icontains=search_query) |
                    Q(father_name__icontains=search_query) |
                    Q(mother_name__icontains=search_query) |
                    Q(university_1__icontains=search_query)
                )

        # ── 3. Multi-Select Criteria Filters ──────────────────────────────
        getlist = getattr(params, 'getlist', None)
        tariffs = (getlist('tariff') if getlist else None) or (params.get('tariff', '').split(',') if params.get('tariff') else [])
        if tariffs and tariffs[0]:
            if 'NO_TARIFF' in tariffs or 'No Tariff' in tariffs:
                clean_tariffs = [t for t in tariffs if t not in ('NO_TARIFF', 'No Tariff')]
                qs = qs.filter(Q(tariff__in=clean_tariffs) | Q(tariff__isnull=True) | Q(tariff=''))
            else:
                qs = qs.filter(tariff__in=tariffs)

        levels = (getlist('level') if getlist else None) or (params.get('level', '').split(',') if params.get('level') else [])
        if levels and levels[0]:
            if 'NO_LEVEL' in levels or 'No Level' in levels:
                clean_levels = [l for l in levels if l not in ('NO_LEVEL', 'No Level')]
                qs = qs.filter(Q(level__in=clean_levels) | Q(level2__in=clean_levels) | Q(level__isnull=True) | Q(level=''))
            else:
                qs = qs.filter(Q(level__in=levels) | Q(level2__in=levels))

        groups = (getlist('group') if getlist else None) or (params.get('group', '').split(',') if params.get('group') else [])
        if groups and groups[0]:
            if 'NO_GROUP' in groups or 'No Group' in groups:
                clean_groups = [g for g in groups if g not in ('NO_GROUP', 'No Group')]
                qs = qs.filter(Q(student_group__in=clean_groups) | Q(student_group__isnull=True) | Q(student_group=''))
            else:
                qs = qs.filter(student_group__in=groups)

        certs = (getlist('cert') if getlist else None) or (params.get('cert', '').split(',') if params.get('cert') else [])
        if certs and certs[0]:
            cert_q = Q()
            for c in certs:
                if c == 'NO CERTIFICATE':
                    cert_q |= Q(language_certificate='NO CERTIFICATE') | Q(language_certificate__isnull=True) | Q(language_certificate='')
                else:
                    cert_q |= Q(language_certificate=c) | Q(language_certificate_2=c) | Q(language_certificate_3=c)
            qs = qs.filter(cert_q)

        scores = (getlist('score') if getlist else None) or (params.get('score', '').split(',') if params.get('score') else [])
        if scores and scores[0]:
            score_q = Q()
            for s in scores:
                score_q |= Q(certificate_score__iexact=s) | Q(certificate_score_2__iexact=s) | Q(certificate_score_3__iexact=s)
            qs = qs.filter(score_q)

        tags = (getlist('tag') if getlist else None) or (params.get('tag', '').split(',') if params.get('tag') else [])
        if tags and tags[0]:
            tag_q = Q()
            for t in tags:
                tag_q |= Q(task_tags__contains=t)
            qs = qs.filter(tag_q)

        leads = (getlist('lead_by') if getlist else None) or (params.get('lead_by', '').split(',') if params.get('lead_by') else [])
        if leads and leads[0]:
            if 'NO_LEADBY' in leads or 'No Lead by' in leads:
                clean_leads = [l for l in leads if l not in ('NO_LEADBY', 'No Lead by')]
                qs = qs.filter(Q(lead_by__in=clean_leads) | Q(lead_by__isnull=True) | Q(lead_by=''))
            else:
                qs = qs.filter(lead_by__in=leads)

        office = params.get('office')
        if office:
            qs = qs.filter(office=office)

        sort_by = params.get('sort_by', 'id')
        sort_order = params.get('sort_order', 'asc')

        if sort_by != 'id':
            order_prefix = '-' if sort_order == 'desc' else ''
            qs = qs.order_by(f"{order_prefix}{sort_by}")

        return qs.prefetch_related('folders')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        params = getattr(request, 'query_params', getattr(request, 'GET', {}))
        sort_by = params.get('sort_by', 'id')
        sort_order = params.get('sort_order', 'asc')

        if sort_by == 'id':
            student_list = list(queryset)
            student_list.sort(
                key=lambda s: alphanumeric_key(s.id),
                reverse=(sort_order == 'desc')
            )
            page = self.paginate_queryset(student_list)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(student_list, many=True)
            return Response(serializer.data)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        req: Any = self.request
        user = req.user
        tenant = getattr(req, 'tenant', None) or getattr(user, 'tenant', None)
        serializer.save(
            tenant=tenant,
            created_by=user
        )

    # ── Actions: Archive / Restore / Permanent Delete ──────────────────────
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        student = self.get_object()
        archive_student(student, request.user)
        return Response({'status': 'Student archived'})

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        student = self.get_object()
        restore_student(student, request.user)
        return Response({'status': 'Student restored'})

    @action(detail=True, methods=['delete'], permission_classes=[IsTenantHeadManager])
    def permanent_delete(self, request, pk=None):
        student = self.get_object()
        permanent_delete_student(student, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Actions: Color / Folder Assignment / Custom Tags ───────────────────
    @action(detail=True, methods=['post'])
    def set_color(self, request, pk=None):
        student = self.get_object()
        serializer = StudentSetColorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if 'row_color' in serializer.validated_data:
            student.row_color = serializer.validated_data['row_color']
        if 'status_row_color' in serializer.validated_data:
            student.status_row_color = serializer.validated_data['status_row_color']
        student.save(update_fields=['row_color', 'status_row_color', 'updated_at'])
        return Response({
            'status': 'Color updated',
            'row_color': student.row_color,
            'status_row_color': student.status_row_color
        })

    @action(detail=True, methods=['post'])
    def set_folders(self, request, pk=None):
        student = self.get_object()
        serializer = StudentSetFoldersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_ids = serializer.validated_data.get('folder_ids', [])
        folders = Folder.objects.filter(id__in=raw_ids, tenant=student.tenant)
        student.folders.set(folders)
        return Response({
            'status': 'Folders updated',
            'folder_ids': [str(f.id) for f in student.folders.all()]
        })

    @action(detail=True, methods=['post'])
    def toggle_tag(self, request, pk=None):
        student = self.get_object()
        tag_name = request.data.get('tag')
        if tag_name:
            current_tags = list(student.task_tags or [])
            if tag_name in current_tags:
                current_tags.remove(tag_name)
            else:
                current_tags.append(tag_name)
            student.task_tags = current_tags
            student.save(update_fields=['task_tags', 'updated_at'])
        return Response({
            'status': 'Tag toggled',
            'task_tags': student.task_tags
        })

    @action(detail=True, methods=['post'])
    def clear_all(self, request, pk=None):
        student = self.get_object()
        student.row_color = None
        student.status_row_color = None
        student.task_tags = []
        student.save(update_fields=['row_color', 'status_row_color', 'task_tags', 'updated_at'])
        return Response({
            'status': 'Cleared',
            'row_color': None,
            'task_tags': []
        })


class FolderViewSet(viewsets.ModelViewSet):
    """Student Folders CRUD ViewSet."""
    serializer_class = FolderSerializer
    permission_classes = [IsTenantUser]
    pagination_class = None

    def get_queryset(self):
        req: Any = self.request
        user = req.user
        tenant = getattr(req, 'tenant', None) or getattr(user, 'tenant', None)
        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'role', '') == 'SUPER_ADMIN'
        if is_super:
            return Folder.objects.all().order_by('name')
        return Folder.objects.filter(tenant=tenant).order_by('name')

    def perform_create(self, serializer):
        req: Any = self.request
        user = req.user
        tenant = getattr(req, 'tenant', None) or getattr(user, 'tenant', None)
        serializer.save(tenant=tenant, created_by=user)


class StudentOptionsViewSet(viewsets.ViewSet):
    """Returns combined option lists for filters, forms, and settings."""
    permission_classes = [IsTenantUser]

    def list(self, request):
        user = request.user
        tenant = getattr(request, 'tenant', None) or getattr(user, 'tenant', None)

        tariffs = list(TariffOption.objects.filter(tenant=tenant).values('name', 'price')) if tenant else []
        levels = list(EducationLevelOption.objects.filter(tenant=tenant).values_list('name', flat=True)) if tenant else []
        groups = list(StudentGroupOption.objects.filter(tenant=tenant).values_list('name', flat=True)) if tenant else []
        leads = list(LeadSourceOption.objects.filter(tenant=tenant).values_list('name', flat=True)) if tenant else []
        coordinators = list(CoordinatorOption.objects.filter(tenant=tenant).values_list('name', flat=True)) if tenant else []
        universities = list(UniversityOption.objects.filter(tenant=tenant).values_list('name', flat=True)) if tenant else []
        folders_qs = Folder.objects.filter(tenant=tenant).order_by('name') if tenant else Folder.objects.all().order_by('name')
        folders = [
            {
                'id': str(f.id),
                'name': f.name,
                'student_count': Student.objects.filter(folders=f, is_deleted=False).count()
            }
            for f in folders_qs
        ]

        all_count = Student.objects.filter(tenant=tenant, is_deleted=False).count() if tenant else Student.objects.filter(is_deleted=False).count()
        except_count = Student.objects.filter(tenant=tenant, is_deleted=False, folders__isnull=True).count() if tenant else Student.objects.filter(is_deleted=False, folders__isnull=True).count()
        deleted_count = Student.objects.filter(tenant=tenant, is_deleted=True).count() if tenant else Student.objects.filter(is_deleted=True).count()
        hidden_count = Student.objects.filter(tenant=tenant, is_deleted=False, status_hidden=True).count() if tenant else Student.objects.filter(is_deleted=False, status_hidden=True).count()

        folder_counts = {
            'all': all_count,
            'except': except_count,
            'deleted': deleted_count,
            'archive': deleted_count,
            'hidden': hidden_count,
        }
        for f in folders_qs:
            folder_counts[str(f.id)] = Student.objects.filter(folders=f, is_deleted=False).count()

        return Response({
            'tariffs': tariffs,
            'levels': levels,
            'groups': groups,
            'leads': leads,
            'coordinators': coordinators,
            'universities': universities,
            'folders': folders,
            'folder_counts': folder_counts,
            'offices': ['ANDIJON OFFIS', 'TOSHKENT OFFIS']
        })


class StudentExportView(APIView):
    """
    Exports filtered or full student roster to Excel XLSX spreadsheet.
    """
    permission_classes = [IsTenantUser]

    def get(self, request):
        user = request.user
        tenant = getattr(request, 'tenant', None) or getattr(user, 'tenant', None)
        params = getattr(request, 'query_params', getattr(request, 'GET', {}))
        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'role', '') == 'SUPER_ADMIN'

        if is_super:
            tenant_param = params.get('tenant_id')
            if tenant_param:
                qs = Student.objects.filter(tenant_id=tenant_param)
            elif tenant:
                qs = Student.objects.filter(tenant=tenant)
            else:
                qs = Student.objects.all()
        else:
            qs = Student.objects.filter(tenant=tenant)

        # Folder / Archive scope
        folder = params.get('folder', 'all')
        include_archive = str(params.get('include_archive', 'false')).lower() == 'true'

        if folder == 'deleted' or folder == 'archive':
            qs = qs.filter(is_deleted=True)
        elif folder == 'hidden':
            qs = qs.filter(is_deleted=False, status_hidden=True)
        elif folder == 'except':
            qs = qs.filter(is_deleted=False, folders__isnull=True)
        elif folder != 'all':
            qs = qs.filter(is_deleted=False, folders__id=folder)
        else:
            if not include_archive:
                qs = qs.filter(is_deleted=False)

        # Search filter
        search_query = str(params.get('search', '')).strip()
        search_mode = params.get('search_mode', 'all')
        if search_query:
            if search_mode == 'id':
                qs = qs.filter(id__icontains=search_query)
            else:
                qs = qs.filter(
                    Q(id__icontains=search_query) |
                    Q(full_name__icontains=search_query) |
                    Q(korean_name__icontains=search_query) |
                    Q(passport__icontains=search_query) |
                    Q(phone1__icontains=search_query) |
                    Q(phone2__icontains=search_query)
                )

        # Multi-select filters
        getlist = getattr(params, 'getlist', None)
        tariffs = (getlist('tariff') if getlist else None) or (params.get('tariff', '').split(',') if params.get('tariff') else [])
        if tariffs and tariffs[0]:
            if 'No Tariff' in tariffs or 'NO_TARIFF' in tariffs:
                clean_tariffs = [t for t in tariffs if t not in ('NO_TARIFF', 'No Tariff')]
                qs = qs.filter(Q(tariff__in=clean_tariffs) | Q(tariff__isnull=True) | Q(tariff=''))
            else:
                qs = qs.filter(tariff__in=tariffs)

        levels = (getlist('level') if getlist else None) or (params.get('level', '').split(',') if params.get('level') else [])
        if levels and levels[0]:
            qs = qs.filter(Q(level__in=levels) | Q(level2__in=levels))

        students_list = sorted(list(qs), key=lambda s: alphanumeric_key(s.id))

        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        if ws is None:
            ws = wb.create_sheet(title="Students Roster")
        else:
            ws.title = "Students Roster"

        headers = [
            "ID", "Full Name", "Korean Name", "Phone 1", "Phone 2", "Tariff",
            "Level", "Language Certificate", "Certificate Score", "Language Cert 2", "Cert 2 Score",
            "University 1", "University 2", "University 3", "University 4", "University 5",
            "Student Group", "Lead By", "Coordinator", "CoA", "Invoice", "Embassy"
        ]
        ws.append(headers)

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="007AFF", end_color="007AFF", fill_type="solid")

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for s in students_list:
            ws.append([
                s.id,
                s.full_name,
                s.korean_name or '',
                s.phone1 or '',
                s.phone2 or '',
                s.tariff or 'NO TARIFF',
                s.level or '',
                s.language_certificate or '',
                s.certificate_score or '',
                s.language_certificate_2 or '',
                s.certificate_score_2 or '',
                s.university_1 or '',
                s.university_2 or '',
                s.university_3 or '',
                s.university_4 or '',
                s.university_5 or '',
                s.student_group or '',
                s.lead_by or '',
                s.coordinator or '',
                s.coa or 'NOT TAKEN',
                s.invoice or 'NOT TAKEN',
                s.embassy or 'NOT TAKEN'
            ])

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            first_cell = col[0]
            if first_cell.column is not None:
                col_letter = get_column_letter(int(first_cell.column))
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="salom_crm_students.xlsx"'
        return response


class BaseOptionViewSet(viewsets.ModelViewSet):
    model_class: Any = None
    permission_classes = [IsTenantUser]
    pagination_class = None

    def get_queryset(self):
        req: Any = self.request
        user = req.user
        tenant = getattr(req, 'tenant', None) or getattr(user, 'tenant', None)
        if not tenant or self.model_class is None:
            return self.model_class.objects.none() if self.model_class else Student.objects.none()
        return self.model_class.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        req: Any = self.request
        user = req.user
        tenant = getattr(req, 'tenant', None) or getattr(user, 'tenant', None)
        serializer.save(tenant=tenant)


class TariffOptionViewSet(BaseOptionViewSet):
    model_class = TariffOption
    serializer_class = TariffOptionSerializer


class EducationLevelOptionViewSet(BaseOptionViewSet):
    model_class = EducationLevelOption
    serializer_class = EducationLevelOptionSerializer


class StudentGroupOptionViewSet(BaseOptionViewSet):
    model_class = StudentGroupOption
    serializer_class = StudentGroupOptionSerializer


class LeadSourceOptionViewSet(BaseOptionViewSet):
    model_class = LeadSourceOption
    serializer_class = LeadSourceOptionSerializer


class CoordinatorOptionViewSet(BaseOptionViewSet):
    model_class = CoordinatorOption
    serializer_class = CoordinatorOptionSerializer


class UniversityOptionViewSet(BaseOptionViewSet):
    model_class = UniversityOption
    serializer_class = UniversityOptionSerializer


class UniversityStatusOptionViewSet(BaseOptionViewSet):
    model_class = UniversityStatusOption
    serializer_class = UniversityStatusOptionSerializer


class SchoolDirectoryViewSet(BaseOptionViewSet):
    model_class = SchoolDirectory
    serializer_class = SchoolDirectorySerializer

    @action(detail=False, methods=['post'], url_path='upsert')
    def upsert(self, request: Request):
        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant required'}, status=status.HTTP_400_BAD_REQUEST)
        
        name = str(request.data.get('name', '')).strip()
        if not name:
            return Response({'error': 'School name is required'}, status=status.HTTP_400_BAD_REQUEST)

        address = request.data.get('address', None)
        website = request.data.get('website', None)
        phone = request.data.get('phone', None)
        email = request.data.get('email', None)

        school, created = SchoolDirectory.objects.update_or_create(
            tenant=tenant,
            name=name,
            defaults={
                'address': address if address is not None else '',
                'website': website if website is not None else '',
                'phone': phone if phone is not None else '',
                'email': email if email is not None else '',
                'created_by': request.user if request.user.is_authenticated else None
            }
        )
        return Response(SchoolDirectorySerializer(school).data, status=status.HTTP_200_OK)


class MajorOptionViewSet(BaseOptionViewSet):
    model_class = MajorOption
    serializer_class = MajorOptionSerializer

    @action(detail=False, methods=['post'], url_path='upsert')
    def upsert(self, request: Request):
        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant required'}, status=status.HTTP_400_BAD_REQUEST)
        
        name = str(request.data.get('name', '')).strip().upper()
        if not name:
            return Response({'error': 'Major name is required'}, status=status.HTTP_400_BAD_REQUEST)

        major, created = MajorOption.objects.get_or_create(
            tenant=tenant,
            name=name,
            defaults={'created_by': request.user if request.user.is_authenticated else None}
        )
        return Response(MajorOptionSerializer(major).data, status=status.HTTP_200_OK)


class ExtractDocumentView(APIView):
    """
    Enterprise in-memory document extraction and OCR service for student profiles.
    Zero permanent file storage - processes in RAM with strict size and concurrency limits.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request):
        from .ocr_service import process_document_ephemeral
        from .ocr_preprocessor import PreprocessError

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'A document file (PDF, JPG, PNG, WEBP) must be uploaded via multipart/form-data.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Enforce maximum upload size (10 MB)
        if file_obj.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'File size exceeds maximum allowed limit of 10MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Enforce valid document extensions & magic bytes
        filename = file_obj.name or ''
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext not in ('pdf', 'jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff'):
            return Response(
                {'error': 'Unsupported file format. Supported formats: PDF, JPG, PNG, WEBP, BMP.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_bytes = file_obj.read()
        if not file_bytes:
            return Response({'error': 'Uploaded file is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Debug mode enabled for staff/superusers with ?debug=true
        is_debug = request.user.is_staff and (request.query_params.get('debug') in ('1', 'true'))

        try:
            extracted_data = process_document_ephemeral(file_bytes, filename, debug=is_debug)

            # Check student ID for parent passport intelligence
            student_id = request.data.get('student_id') or request.query_params.get('student_id')
            if student_id:
                try:
                    student = Student.objects.filter(id=student_id).first()
                    if student and student.birthday and extracted_data.get('document_type') in ('PASSPORT', 'ID_CARD'):
                        extracted_dob = extracted_data.get('fields', {}).get('DATE_OF_BIRTH')
                        if extracted_dob and str(extracted_dob) < str(student.birthday):
                            # Parent passport detected!
                            extracted_data['is_parent_passport'] = True
                            sex = extracted_data.get('fields', {}).get('SEX', '')
                            full_name = extracted_data.get('fields', {}).get('FULL_NAME', '')
                            if sex == 'MALE' and full_name:
                                extracted_data['fields']['FATHER_FULLNAME'] = full_name
                            elif sex == 'FEMALE' and full_name:
                                extracted_data['fields']['MOTHER_FULLNAME'] = full_name
                except Exception:
                    pass

            return Response(extracted_data, status=status.HTTP_200_OK)
        except PreprocessError as pe:
            return Response({'error': str(pe)}, status=status.HTTP_400_BAD_REQUEST)
        except TimeoutError as te:
            return Response({'error': str(te)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({'error': f'Failed to process document: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


