import re
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from apps.core.permissions import IsTenantUser, IsTenantHeadManager
from .models import (
    Student, Folder, TariffOption, EducationLevelOption,
    StudentGroupOption, LeadSourceOption, CoordinatorOption
)
from .serializers import (
    StudentListSerializer, StudentDetailSerializer, StudentCreateUpdateSerializer,
    StudentSetColorSerializer, StudentSetFoldersSerializer, FolderSerializer
)
from .services import archive_student, restore_student, permanent_delete_student

def alphanumeric_key(student_id):
    """
    Sort key for alphanumeric student IDs matching Uniapp v2 logic.
    Splits into prefix and numeric components (e.g. 'UB120' -> ('UB', 120)).
    """
    if not student_id:
        return ("", 0)
    match = re.match(r'^([A-Za-z\s_-]*)(\d*)$', student_id.strip())
    if match:
        prefix = match.group(1).upper()
        num = int(match.group(2)) if match.group(2) else 0
        return (prefix, num)
    return (student_id.upper(), 0)


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
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None) or getattr(user, 'tenant', None)

        if user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN':
            tenant_param = self.request.query_params.get('tenant_id')
            if tenant_param:
                qs = Student.objects.filter(tenant_id=tenant_param)
            elif tenant:
                qs = Student.objects.filter(tenant=tenant)
            else:
                qs = Student.objects.all()
        else:
            qs = Student.objects.filter(tenant=user.tenant)

        # ── 1. Folder & Archive/Hidden Scopes ──────────────────────────────
        folder = self.request.query_params.get('folder', 'all')
        include_archive = self.request.query_params.get('include_archive', 'false').lower() == 'true'

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
        search_query = self.request.query_params.get('search', '').strip()
        search_mode = self.request.query_params.get('search_mode', 'all')

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
                    Q(father_phone__icontains=search_query) |
                    Q(mother_phone__icontains=search_query)
                )

        # ── 3. Multi-Select Filters ─────────────────────────────────────────
        tariffs = self.request.query_params.getlist('tariff') or (self.request.query_params.get('tariff', '').split(',') if self.request.query_params.get('tariff') else [])
        if tariffs and tariffs[0]:
            if 'No Tariff' in tariffs:
                qs = qs.filter(Q(tariff__in=tariffs) | Q(tariff__isnull=True) | Q(tariff=''))
            else:
                qs = qs.filter(tariff__in=tariffs)

        levels = self.request.query_params.getlist('level') or (self.request.query_params.get('level', '').split(',') if self.request.query_params.get('level') else [])
        if levels and levels[0]:
            qs = qs.filter(level__in=levels)

        groups = self.request.query_params.getlist('group') or (self.request.query_params.get('group', '').split(',') if self.request.query_params.get('group') else [])
        if groups and groups[0]:
            if 'NO_GROUP' in groups:
                qs = qs.filter(Q(student_group__in=groups) | Q(student_group__isnull=True) | Q(student_group=''))
            else:
                qs = qs.filter(student_group__in=groups)

        certs = self.request.query_params.getlist('cert') or (self.request.query_params.get('cert', '').split(',') if self.request.query_params.get('cert') else [])
        if certs and certs[0]:
            cert_q = Q()
            if 'NO CERTIFICATE' in certs:
                cert_q |= Q(language_certificate__isnull=True) | Q(language_certificate='NO CERTIFICATE')
            for c in certs:
                if c != 'NO CERTIFICATE':
                    cert_q |= Q(language_certificate=c) | Q(language_certificate_2=c) | Q(language_certificate_3=c)
            qs = qs.filter(cert_q)

        leads = self.request.query_params.getlist('lead_by') or (self.request.query_params.get('lead_by', '').split(',') if self.request.query_params.get('lead_by') else [])
        if leads and leads[0]:
            if 'NO_LEADBY' in leads:
                qs = qs.filter(Q(lead_by__in=leads) | Q(lead_by__isnull=True) | Q(lead_by=''))
            else:
                qs = qs.filter(lead_by__in=leads)

        office = self.request.query_params.get('office')
        if office:
            qs = qs.filter(office=office)

        # ── 4. Sorting ─────────────────────────────────────────────────────
        sort_by = self.request.query_params.get('sort_by', 'id')
        sort_order = self.request.query_params.get('sort_order', 'asc')

        if sort_by == 'id':
            # Evaluated in Python for perfect alphanumeric sorting matching legacy app
            student_list = list(qs.prefetch_related('folders'))
            student_list.sort(
                key=lambda s: alphanumeric_key(s.id),
                reverse=(sort_order == 'desc')
            )
            return student_list

        order_prefix = '-' if sort_order == 'desc' else ''
        return qs.order_by(f"{order_prefix}{sort_by}").prefetch_related('folders')

    def perform_create(self, serializer):
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None) or getattr(user, 'tenant', None)
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

    # ── Actions: Color / Folder Assignment ─────────────────────────────────
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
        return Response({'status': 'Color updated', 'row_color': student.row_color, 'status_row_color': student.status_row_color})

    @action(detail=True, methods=['post'])
    def set_folders(self, request, pk=None):
        student = self.get_object()
        serializer = StudentSetFoldersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student.folders.set(serializer.validated_data['folder_ids'])
        return Response({'status': 'Folders updated'})


class FolderViewSet(viewsets.ModelViewSet):
    """Student Folders CRUD ViewSet."""
    serializer_class = FolderSerializer
    permission_classes = [IsTenantUser]

    def get_queryset(self):
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None) or getattr(user, 'tenant', None)
        if user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN':
            return Folder.objects.all().order_by('name')
        return Folder.objects.filter(tenant=tenant).order_by('name')

    def perform_create(self, serializer):
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None) or getattr(user, 'tenant', None)
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
        folders = list(Folder.objects.filter(tenant=tenant).values('id', 'name')) if tenant else []

        # Fallback defaults if options are not seeded yet
        if not tariffs:
            from apps.payments.services import DEFAULT_TARIFF_PRICES
            tariffs = [{'name': k, 'price': v} for k, v in DEFAULT_TARIFF_PRICES.items()]
        if not levels:
            levels = ['COLLEGE', 'BACHELOR', 'MASTERS', 'MASTER NO CERTIFICATE', 'LANGUAGE COURSE']
        if not folders and tenant:
            # Auto ensure KDB exists
            kdb, _ = Folder.objects.get_or_create(tenant=tenant, name='KDB')
            folders = [{'id': str(kdb.id), 'name': kdb.name}]

        return Response({
            'tariffs': tariffs,
            'levels': levels,
            'groups': groups,
            'leads': leads,
            'coordinators': coordinators,
            'folders': folders,
            'offices': ['ANDIJON OFFIS', 'TOSHKENT OFFIS']
        })
