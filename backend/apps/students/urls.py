from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentViewSet, FolderViewSet, StudentOptionsViewSet, StudentExportView,
    TariffOptionViewSet, EducationLevelOptionViewSet, StudentGroupOptionViewSet,
    LeadSourceOptionViewSet, CoordinatorOptionViewSet,
    UniversityOptionViewSet, UniversityStatusOptionViewSet, TagOptionViewSet,
    SchoolDirectoryViewSet, MajorOptionViewSet, ExtractDocumentView,
    VisaCheckView, VisaDownloadPdfView, VisaStudentQuickSearchView,
    VisaStudentLookupView, VisaStudentListCreateView, VisaStudentDetailView,
    VisaStudentBulkDeleteView, VisaOptionsView
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
router.register(r'tags', TagOptionViewSet, basename='tag-option')
router.register(r'schools', SchoolDirectoryViewSet, basename='school')
router.register(r'majors', MajorOptionViewSet, basename='major')

urlpatterns = [
    path('students/export/excel/', StudentExportView.as_view(), name='student-export-excel'),
    path('students/extract-document/', ExtractDocumentView.as_view(), name='student-extract-document'),
    path('students/visa/check/', VisaCheckView.as_view(), name='student-visa-check'),
    path('students/visa/download-pdf/', VisaDownloadPdfView.as_view(), name='student-visa-download-pdf'),
    path('students/visa/quick-search/', VisaStudentQuickSearchView.as_view(), name='student-visa-quick-search'),
    path('students/visa/lookup/', VisaStudentLookupView.as_view(), name='student-visa-lookup'),
    path('students/visa/students/', VisaStudentListCreateView.as_view(), name='student-visa-list-create'),
    path('students/visa/students/bulk-delete/', VisaStudentBulkDeleteView.as_view(), name='student-visa-bulk-delete'),
    path('students/visa/students/<str:passport>/', VisaStudentDetailView.as_view(), name='student-visa-detail'),
    path('students/visa/options/', VisaOptionsView.as_view(), name='student-visa-options'),
    path('student-options/', StudentOptionsViewSet.as_view({'get': 'list'}), name='student-options'),
    path('', include(router.urls)),
]

