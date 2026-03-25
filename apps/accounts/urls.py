from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    CustomLoginView, ProfileView, 
    CustomPasswordChangeView, CustomPasswordChangeDoneView
)

app_name = 'accounts'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password-change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
]
