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

        # Always route through the caller's own tenant bot/chat — a plain
        # chat_id in the request body must never let one tenant's user push
        # a message into another tenant's (or the platform's) chat.
        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'tenant', None)
        success = send_telegram_notification(message=str(message).strip(), tenant=tenant)
        return Response({"success": success})
