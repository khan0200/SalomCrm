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
    PublicVerifyContractView,
    IdentityVerificationWebhookView,
)
from .contract_sign_views import (
    ContractSignStatusView,
    ContractConfirmIdentityView,
    ContractSignKycStartView,
    ContractSignKycStatusView,
    ContractSignKycConfirmView,
    ContractSignSubmitView,
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

    # Didit identity-verification webhook (serves the staff-prefilled
    # signing-link flow below via its "contract:<uuid>" vendor_data tag)
    path('contracts/online/verification/webhook/', IdentityVerificationWebhookView.as_view(), name='online-verification-webhook'),

    # Public verification: GET /api/contracts/public/<verification_code>/
    # No auth - see PublicVerifyContractView docstring.
    path('contracts/public/<str:code>/', PublicVerifyContractView.as_view(), name='online-contract-public-verify'),

    # Staff-prefilled, token-based contract signing link (contract_sign_views.py).
    # No account/login - sign_token in the URL is the sole access key.
    path('contracts/sign/<str:token>/', ContractSignStatusView.as_view(), name='contract-sign-status'),
    path('contracts/sign/<str:token>/confirm-identity/', ContractConfirmIdentityView.as_view(), name='contract-sign-confirm-identity'),
    path('contracts/sign/<str:token>/kyc/start/', ContractSignKycStartView.as_view(), name='contract-sign-kyc-start'),
    path('contracts/sign/<str:token>/kyc/status/', ContractSignKycStatusView.as_view(), name='contract-sign-kyc-status'),
    path('contracts/sign/<str:token>/kyc/confirm/', ContractSignKycConfirmView.as_view(), name='contract-sign-kyc-confirm'),
    path('contracts/sign/<str:token>/submit/', ContractSignSubmitView.as_view(), name='contract-sign-submit'),

    path('', include(router.urls)),
]

