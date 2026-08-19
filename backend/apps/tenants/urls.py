from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, BranchViewSet

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'branches', BranchViewSet, basename='branch')

urlpatterns = [
    path('', include(router.urls)),
]
