from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Announcement
from apps.cooperatives.views import CoopAdminRequiredMixin

class CooperativeAnnouncementsView(LoginRequiredMixin, CoopAdminRequiredMixin, ListView):
    model = Announcement
    template_name = 'coop_admin/announcements_list.html'
    context_object_name = 'announcements'

    def get_queryset(self):
        return Announcement.objects.filter(cooperative=self.request.user.cooperative).order_by('-created_at')

from django.views.generic.edit import CreateView
from django.urls import reverse_lazy

class AnnouncementCreateView(LoginRequiredMixin, CoopAdminRequiredMixin, CreateView):
    model = Announcement
    template_name = 'components/generic_form.html'
    fields = ['title', 'message']
    success_url = reverse_lazy('announcements:coop_list')

    def form_valid(self, form):
        form.instance.cooperative = self.request.user.cooperative
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Notify all members
        from apps.accounts.models import UserRole
        from apps.notifications.utils import create_notification
        from django.urls import reverse
        
        members = form.instance.cooperative.users.filter(role=UserRole.MEMBER)
        for member in members:
            dashboard_url = reverse('members:dashboard')
            create_notification(
                user=member,
                title="New Announcement",
                message=f"Management has posted a new announcement: {form.instance.title}",
                link=f"{dashboard_url}?announcement_id={form.instance.id}"
            )
            
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Post Announcement'
        context['description'] = 'Broadcast a new system-wide or cooperative update.'
        return context
from apps.members.views import MemberRequiredMixin

class MemberAnnouncementListView(LoginRequiredMixin, MemberRequiredMixin, ListView):
    model = Announcement
    template_name = 'announcements/member_list.html'
    context_object_name = 'announcements'

    def get_queryset(self):
        return Announcement.objects.filter(cooperative=self.request.user.cooperative).order_by('-created_at')
