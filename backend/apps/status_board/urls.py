from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StatusBoardViewSet

router = DefaultRouter()
router.register(r'status', StatusBoardViewSet, basename='status-board')

urlpatterns = [
    path('', include(router.urls)),
]
