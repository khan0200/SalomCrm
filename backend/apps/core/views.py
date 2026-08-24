from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .telegram_service import send_telegram_notification

class TelegramNotifyView(APIView):
    """
    Direct Telegram Notification API Endpoint.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message = request.data.get("message")
        if not message or not str(message).strip():
            return Response({"error": "A non-empty message is required"}, status=status.HTTP_400_BAD_REQUEST)

        chat_id = request.data.get("chat_id")
        success = send_telegram_notification(message=str(message).strip(), chat_ids=chat_id)
        return Response({"success": success})
