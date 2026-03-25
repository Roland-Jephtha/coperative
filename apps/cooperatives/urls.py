from django.urls import path
from .views import (
    SuperAdminDashboardView, CoopAdminDashboardView, 
    SuperCooperativesView, CooperativeRegisterView,
    CooperativeOnboardingView, CooperativeSettingsUpdateView
)

app_name = 'cooperatives'

urlpatterns = [
    path('register/', CooperativeRegisterView.as_view(), name='register'),
    path('onboarding/', CooperativeOnboardingView.as_view(), name='onboarding'),
    path('settings/', CooperativeSettingsUpdateView.as_view(), name='settings'),
    path('super-dashboard/', SuperAdminDashboardView.as_view(), name='super_dashboard'),
    path('manage-cooperatives/', SuperCooperativesView.as_view(), name='super_list'),
    path('dashboard/', CoopAdminDashboardView.as_view(), name='admin_dashboard'),
]
