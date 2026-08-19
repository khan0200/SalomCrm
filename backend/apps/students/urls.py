from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, FolderViewSet, StudentOptionsViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'folders', FolderViewSet, basename='folder')

urlpatterns = [
    path('student-options/', StudentOptionsViewSet.as_view({'get': 'list'}), name='student-options'),
    path('', include(router.urls)),
]
