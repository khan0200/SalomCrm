from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, PaymentOverviewViewSet, PaymentExportView

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'payment-overview', PaymentOverviewViewSet, basename='payment-overview')

urlpatterns = [
    path('payments/export/excel/', PaymentExportView.as_view(), name='payment-export-excel'),
    path('', include(router.urls)),
]
