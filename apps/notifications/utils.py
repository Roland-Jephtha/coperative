from .models import Notification
from pusher import Pusher
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def create_notification(user, title, message, link=None):
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        link=link
    )
    
    # Trigger Pusher event if configured
    if all([settings.PUSHER_APP_ID, settings.PUSHER_KEY, settings.PUSHER_SECRET]):
        try:
            pusher_client = Pusher(
                app_id=settings.PUSHER_APP_ID,
                key=settings.PUSHER_KEY,
                secret=settings.PUSHER_SECRET,
                cluster=settings.PUSHER_CLUSTER,
                ssl=True,
                timeout=3 # Reduced from 5 to avoid long hangs
            )
            pusher_client.trigger(
                f'user-{user.id}', 
                'new-notification', 
                {
                    'id': notification.id,
                    'title': title,
                    'message': message,
                    'link': link or '#',
                    'created_at': 'Just now'
                }
            )
        except Exception as e:
            logger.error(f"Pusher error: {e}")
            
    return notification
