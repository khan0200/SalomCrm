import uuid
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from apps.core.permissions import IsTenantUser, IsTenantManager, IsTenantManagerOrReadOnly
from apps.students.models import Student
from apps.students.views import alphanumeric_key
from .serializers import (
    StatusStudentListSerializer, StatusQuickUpdateSerializer,
    EmbassyDrawerUpdateSerializer, calculate_days_left
)

class StatusBoardViewSet(viewsets.ModelViewSet):
    """
    Dedicated Status Board ViewSet for General Status and KDB processing workflows.
    """
    serializer_class = StatusStudentListSerializer
    permission_classes = [IsTenantManagerOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None) or getattr(user, 'tenant', None)

        if user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN':
            qs = Student.objects.filter(tenant=tenant) if tenant else Student.objects.all()
        else:
            qs = Student.objects.filter(tenant=user.tenant)

        # 1. Base non-deleted
        qs = qs.filter(is_deleted=False)

        # 2. Status hidden handling
        show_hidden = self.request.query_params.get('show_hidden', 'false').lower() == 'true'
        folder = self.request.query_params.get('folder', 'all')

        if folder == 'hidden' or show_hidden:
            qs = qs.filter(status_hidden=True)
        elif folder == 'except':
            qs = qs.filter(status_hidden=False).filter(Q(folder_ids=[]) | Q(folder_ids__isnull=True))
        elif folder != 'all':
            try:
                folder_uuid = uuid.UUID(str(folder).strip())
                qs = qs.filter(status_hidden=False, folder_ids__contains=[folder_uuid])
            except (ValueError, TypeError):
                qs = qs.none()
        else:
            qs = qs.filter(status_hidden=False)

        # 3. Search query
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(id__icontains=search) |
                Q(full_name__icontains=search) |
                Q(passport__icontains=search) |
                Q(phone1__icontains=search)
            )

        return qs.order_by('id')

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        sort_by = request.query_params.get('sort_by', 'id')
        sort_order = request.query_params.get('sort_order', 'asc')

        students_list = list(qs)

        if sort_by == 'left':
            def left_sort_key(s):
                days = calculate_days_left(s.kdb_take_date)
                return (days if days is not None else 999999, alphanumeric_key(s.id))

            students_list.sort(key=left_sort_key, reverse=(sort_order == 'desc'))
        elif sort_by == 'id':
            students_list.sort(key=lambda s: alphanumeric_key(s.id), reverse=(sort_order == 'desc'))

        page = self.paginate_queryset(students_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(students_list, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsTenantManager])
    def quick_update(self, request, id=None):
        student = self.get_object()
        serializer = StatusQuickUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for attr, value in serializer.validated_data.items():
            setattr(student, attr, value)

        student.save()
        return Response(StatusStudentListSerializer(student).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsTenantManager])
    def embassy_drawer(self, request, id=None):
        student = self.get_object()
        serializer = EmbassyDrawerUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for attr, value in serializer.validated_data.items():
            setattr(student, attr, value)

        student.save()
        return Response(StatusStudentListSerializer(student).data)
