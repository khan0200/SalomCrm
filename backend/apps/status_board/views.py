from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from apps.core.permissions import IsTenantUser
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
    permission_classes = [IsTenantUser]

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
            qs = qs.filter(status_hidden=False, folders__isnull=True)
        elif folder != 'all':
            qs = qs.filter(status_hidden=False, folders__id=folder)
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

        # 4. Sorting (ID vs Remaining Days 'left')
        sort_by = self.request.query_params.get('sort_by', 'id')
        sort_order = self.request.query_params.get('sort_order', 'asc')

        students_list = list(qs.prefetch_related('folders'))

        if sort_by == 'left':
            def left_sort_key(s):
                days = calculate_days_left(s.kdb_take_date)
                # Items without dates go to the bottom
                return (days if days is not None else 999999, alphanumeric_key(s.id))

            students_list.sort(key=left_sort_key, reverse=(sort_order == 'desc'))
            return students_list

        if sort_by == 'id':
            students_list.sort(key=lambda s: alphanumeric_key(s.id), reverse=(sort_order == 'desc'))
            return students_list

        return qs.order_by('id')

    @action(detail=True, methods=['patch'])
    def quick_update(self, request, pk=None):
        student = self.get_object()
        serializer = StatusQuickUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for attr, value in serializer.validated_data.items():
            setattr(student, attr, value)

        student.save()
        return Response(StatusStudentListSerializer(student).data)

    @action(detail=True, methods=['patch'])
    def embassy_drawer(self, request, pk=None):
        student = self.get_object()
        serializer = EmbassyDrawerUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for attr, value in serializer.validated_data.items():
            setattr(student, attr, value)

        student.save()
        return Response(StatusStudentListSerializer(student).data)
