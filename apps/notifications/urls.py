from django.urls import path
from .views import NotificationListView, MarkNotificationReadView, MarkAllAsReadView

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='list'),
    path('mark-read/<int:pk>/', MarkNotificationReadView.as_view(), name='mark_read'),
    path('mark-all-read/', MarkAllAsReadView.as_view(), name='mark_all_read'),
]
