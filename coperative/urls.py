from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect, render

def home_redirect(request):
    if request.user.is_authenticated:
        if request.user.role == 'SUPER_ADMIN':
            return redirect('cooperatives:super_dashboard')
        elif request.user.role == 'COOP_ADMIN':
            return redirect('cooperatives:admin_dashboard')
        elif request.user.role == 'MEMBER':
            return redirect('members:dashboard')
    
    return render(request, 'landing.html')

urlpatterns = [
    path('sys-admin/', admin.site.urls), # Standard django admin moved
    path('accounts/', include('apps.accounts.urls')),
    path('cooperative/', include('apps.cooperatives.urls')),
    path('members/', include('apps.members.urls')),
    path('contributions/', include('apps.contributions.urls')),
    path('loans/', include('apps.loans.urls')),
    path('repayments/', include('apps.repayments.urls')),
    path('subscriptions/', include('apps.subscriptions.urls')),
    path('announcements/', include('apps.announcements.urls')),
    path('notifications/', include('apps.notifications.urls')),
    # Other apps will be included when needed
    path('', home_redirect, name='home'),
]
