from django.urls import path
from .views import MemberDashboardView
from .views_admin import (
    CooperativeMembersView, MemberCreateView, MemberDetailView,
    MemberUpdateView, MemberSuspendView, MemberActivateView,
    MemberCreateSuccessView
)

app_name = 'members'

urlpatterns = [
    path('dashboard/', MemberDashboardView.as_view(), name='dashboard'),
    path('management/', CooperativeMembersView.as_view(), name='coop_list'),
    path('management/add/', MemberCreateView.as_view(), name='add'),
    path('management/add/success/', MemberCreateSuccessView.as_view(), name='add_success'),
    path('management/<int:member_id>/', MemberDetailView.as_view(), name='detail'),
    path('management/<int:member_id>/edit/', MemberUpdateView.as_view(), name='edit'),
    path('management/<int:member_id>/suspend/', MemberSuspendView.as_view(), name='suspend'),
    path('management/<int:member_id>/activate/', MemberActivateView.as_view(), name='activate'),
]
