from .models import Notification
from django.conf import settings

def notification_context(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        return {
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
            'pusher_key': getattr(settings, 'PUSHER_KEY', ''),
            'pusher_cluster': getattr(settings, 'PUSHER_CLUSTER', 'mt1'),
        }
    return {}
