from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentViewSet, FolderViewSet, StudentOptionsViewSet, StudentExportView,
    TariffOptionViewSet, EducationLevelOptionViewSet, StudentGroupOptionViewSet,
    LeadSourceOptionViewSet, CoordinatorOptionViewSet,
    UniversityOptionViewSet, UniversityStatusOptionViewSet, TagOptionViewSet,
    SchoolDirectoryViewSet, WorkplaceDirectoryViewSet, JobTitleDirectoryViewSet,
    MajorOptionViewSet, ExtractDocumentView,
    VisaCheckView, VisaDownloadPdfView, VisaStudentQuickSearchView,
    VisaStudentLookupView, VisaStudentListCreateView, VisaStudentDetailView,
    VisaStudentBulkDeleteView, VisaOptionsView,
    ExcelFillAnalyzeView, ExcelFillGenerateView,
    AICommandInterpretView,
    WordFillAnalyzeView, WordFillGenerateView,
    WordFillFieldsView, WordFillExampleDownloadView,
    WordFillScanTagsView,
    ContractViewSet
)
from .online_contract_views import (
    TenantInfoView,
    SendOtpView,
    VerifyPhoneOtpView,
    StudentSignUpView,
    StudentSignInView,
    StudentProfileView,
    SubmitContractView,
    VerifyContractView,
    ResubmitContractView,
    LogContractViewAuditView,
    PublicContractDetailView,
    CancelOnlineContractView,
    PublicVerifyContractView,
)

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'folders', FolderViewSet, basename='folder')
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'tariffs', TariffOptionViewSet, basename='tariff')
router.register(r'education-levels', EducationLevelOptionViewSet, basename='education-level')
router.register(r'student-groups', StudentGroupOptionViewSet, basename='student-group')
router.register(r'lead-sources', LeadSourceOptionViewSet, basename='lead-source')
router.register(r'coordinators', CoordinatorOptionViewSet, basename='coordinator')
router.register(r'universities', UniversityOptionViewSet, basename='university')
router.register(r'university-statuses', UniversityStatusOptionViewSet, basename='university-status')
router.register(r'tags', TagOptionViewSet, basename='tag-option')
router.register(r'schools', SchoolDirectoryViewSet, basename='school')
router.register(r'workplaces', WorkplaceDirectoryViewSet, basename='workplace')
router.register(r'job-titles', JobTitleDirectoryViewSet, basename='job-title')
router.register(r'majors', MajorOptionViewSet, basename='major')

urlpatterns = [
    path('students/export/excel/', StudentExportView.as_view(), name='student-export-excel'),
    path('students/excel-fill/analyze/', ExcelFillAnalyzeView.as_view(), name='student-excel-fill-analyze'),
    path('students/excel-fill/generate/', ExcelFillGenerateView.as_view(), name='student-excel-fill-generate'),
    path('students/word-fill/fields/', WordFillFieldsView.as_view(), name='student-word-fill-fields'),
    path('students/word-fill/example/', WordFillExampleDownloadView.as_view(), name='student-word-fill-example'),
    path('students/word-fill/scan-tags/', WordFillScanTagsView.as_view(), name='student-word-fill-scan-tags'),
    path('students/word-fill/analyze/', WordFillAnalyzeView.as_view(), name='student-word-fill-analyze'),
    path('students/word-fill/generate/', WordFillGenerateView.as_view(), name='student-word-fill-generate'),
    path('students/extract-document/', ExtractDocumentView.as_view(), name='student-extract-document'),
    path('students/visa/check/', VisaCheckView.as_view(), name='student-visa-check'),
    path('students/visa/download-pdf/', VisaDownloadPdfView.as_view(), name='student-visa-download-pdf'),
    path('students/visa/quick-search/', VisaStudentQuickSearchView.as_view(), name='student-visa-quick-search'),
    path('students/visa/lookup/', VisaStudentLookupView.as_view(), name='student-visa-lookup'),
    path('students/visa/students/', VisaStudentListCreateView.as_view(), name='student-visa-list-create'),
    path('students/visa/students/bulk-delete/', VisaStudentBulkDeleteView.as_view(), name='student-visa-bulk-delete'),
    path('students/visa/students/<str:passport>/', VisaStudentDetailView.as_view(), name='student-visa-detail'),
    path('students/visa/options/', VisaOptionsView.as_view(), name='student-visa-options'),
    path('students/ai-command/', AICommandInterpretView.as_view(), name='student-ai-command'),
    path('student-options/', StudentOptionsViewSet.as_view({'get': 'list'}), name='student-options'),

    # Online Student Contracts API
    path('contracts/online/tenant-info/<slug:slug>/', TenantInfoView.as_view(), name='online-contract-tenant-info'),
    path('contracts/online/send-otp/', SendOtpView.as_view(), name='online-contract-send-otp'),
    path('contracts/online/send-otp/<slug:tenant_slug>/', SendOtpView.as_view(), name='online-contract-send-otp-slug'),
    path('contracts/online/verify-phone/', VerifyPhoneOtpView.as_view(), name='online-contract-verify-phone'),
    path('contracts/online/sign-up/', StudentSignUpView.as_view(), name='online-contract-sign-up'),
    path('contracts/online/sign-up/<slug:tenant_slug>/', StudentSignUpView.as_view(), name='online-contract-sign-up-slug'),
    path('contracts/online/sign-in/', StudentSignInView.as_view(), name='online-contract-sign-in'),
    path('contracts/online/sign-in/<slug:tenant_slug>/', StudentSignInView.as_view(), name='online-contract-sign-in-slug'),
    path('contracts/online/profile/', StudentProfileView.as_view(), name='online-contract-profile'),
    path('contracts/online/submit-contract/', SubmitContractView.as_view(), name='online-contract-submit'),
    path('contracts/online/<uuid:contract_id>/verify-code/', VerifyContractView.as_view(), name='online-contract-verify-code'),
    path('contracts/online/<uuid:contract_id>/resubmit/', ResubmitContractView.as_view(), name='online-contract-resubmit'),
    path('contracts/online/<uuid:contract_id>/audit-view/', LogContractViewAuditView.as_view(), name='online-contract-audit-view'),
    path('contracts/online/<uuid:contract_id>/detail/', PublicContractDetailView.as_view(), name='online-contract-detail'),
    path('contracts/online/<uuid:contract_id>/cancel/', CancelOnlineContractView.as_view(), name='online-contract-cancel'),

    # Public verification: GET /api/contracts/public/<verification_code>/
    # No auth - see PublicVerifyContractView docstring.
    path('contracts/public/<str:code>/', PublicVerifyContractView.as_view(), name='online-contract-public-verify'),

    path('', include(router.urls)),
]

