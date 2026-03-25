from django.urls import path
from .views import SuperSubscriptionsView

app_name = 'subscriptions'

urlpatterns = [
    path('super-management/', SuperSubscriptionsView.as_view(), name='super_list'),
]
