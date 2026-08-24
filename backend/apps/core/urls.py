from django.urls import path
from .views import TelegramNotifyView

urlpatterns = [
    path('notify/', TelegramNotifyView.as_view(), name='telegram-notify'),
]
