from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentViewSet, FolderViewSet, StudentOptionsViewSet, StudentExportView,
    TariffOptionViewSet, EducationLevelOptionViewSet, StudentGroupOptionViewSet,
    LeadSourceOptionViewSet, CoordinatorOptionViewSet,
    UniversityOptionViewSet, UniversityStatusOptionViewSet,
    SchoolDirectoryViewSet, MajorOptionViewSet, ExtractDocumentView
)

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'folders', FolderViewSet, basename='folder')
router.register(r'tariffs', TariffOptionViewSet, basename='tariff')
router.register(r'education-levels', EducationLevelOptionViewSet, basename='education-level')
router.register(r'student-groups', StudentGroupOptionViewSet, basename='student-group')
router.register(r'lead-sources', LeadSourceOptionViewSet, basename='lead-source')
router.register(r'coordinators', CoordinatorOptionViewSet, basename='coordinator')
router.register(r'universities', UniversityOptionViewSet, basename='university')
router.register(r'university-statuses', UniversityStatusOptionViewSet, basename='university-status')
router.register(r'schools', SchoolDirectoryViewSet, basename='school')
router.register(r'majors', MajorOptionViewSet, basename='major')

urlpatterns = [
    path('students/export/excel/', StudentExportView.as_view(), name='student-export-excel'),
    path('students/extract-document/', ExtractDocumentView.as_view(), name='student-extract-document'),
    path('student-options/', StudentOptionsViewSet.as_view({'get': 'list'}), name='student-options'),
    path('', include(router.urls)),
]

