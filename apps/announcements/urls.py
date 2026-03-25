from django.urls import path
from .views import CooperativeAnnouncementsView, AnnouncementCreateView

app_name = 'announcements'
urlpatterns = [
    path('management/', CooperativeAnnouncementsView.as_view(), name='coop_list'),
    path('management/add/', AnnouncementCreateView.as_view(), name='add'),
]
