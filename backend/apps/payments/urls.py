from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet, PaymentOverviewViewSet, PaymentExportView,
    PaymentMethodTemplateViewSet, PaymentReceiverTemplateViewSet, PaymentNotePillViewSet
)

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'payment-overview', PaymentOverviewViewSet, basename='payment-overview')
router.register(r'payment-methods', PaymentMethodTemplateViewSet, basename='payment-method')
router.register(r'payment-receivers', PaymentReceiverTemplateViewSet, basename='payment-receiver')
router.register(r'payment-notes', PaymentNotePillViewSet, basename='payment-note')

urlpatterns = [
    path('payments/export/excel/', PaymentExportView.as_view(), name='payment-export-excel'),
    path('', include(router.urls)),
]
