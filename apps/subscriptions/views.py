from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CooperativeSubscription
from apps.cooperatives.views import SuperAdminRequiredMixin

class SuperSubscriptionsView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = CooperativeSubscription
    template_name = 'coop_admin/super_subs_list.html'
    context_object_name = 'subscriptions'

    def get_queryset(self):
        return CooperativeSubscription.objects.all().select_related('cooperative', 'plan').order_by('-start_date')
