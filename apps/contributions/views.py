from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Contribution, TransactionStatus
from apps.cooperatives.views import CoopAdminRequiredMixin
from django.utils import timezone
from apps.accounts.models import UserRole
from apps.notifications.utils import create_notification

class CooperativeContributionsView(LoginRequiredMixin, CoopAdminRequiredMixin, ListView):
    model = Contribution
    template_name = 'coop_admin/contributions_list.html'
    context_object_name = 'contributions'

    def get_queryset(self):
        return Contribution.objects.filter(cooperative=self.request.user.cooperative).order_by('-contribution_date')

from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
import uuid

class ContributionCreateView(LoginRequiredMixin, CoopAdminRequiredMixin, CreateView):
    model = Contribution
    template_name = 'components/generic_form.html'
    fields = ['member', 'amount', 'contribution_date', 'notes']
    success_url = reverse_lazy('contributions:coop_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        from apps.accounts.models import User, UserRole
        form.fields['member'].queryset = User.objects.filter(cooperative=self.request.user.cooperative, role=UserRole.MEMBER)
        return form

    def form_valid(self, form):
        form.instance.cooperative = self.request.user.cooperative
        form.instance.recorded_by = self.request.user
        form.instance.payment_reference = str(uuid.uuid4())[:8].upper()
        response = super().form_valid(form)
        
        # Notify Member
        create_notification(
            user=form.instance.member,
            title="Savings Recorded",
            message=f"Management has recorded a savings deposit of ₦{form.instance.amount:,} to your account.",
            link="/contributions/member/"
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Record Deposit'
        context['description'] = 'Log a new saving deposit or contribution for a member.'
        return context

from apps.members.views import MemberRequiredMixin

class MemberContributionsView(LoginRequiredMixin, MemberRequiredMixin, ListView):
    model = Contribution
    template_name = 'member/contributions_list.html'
    context_object_name = 'contributions'

    def get_queryset(self):
        return Contribution.objects.filter(member=self.request.user).order_by('-contribution_date')

class MemberContributionCreateView(LoginRequiredMixin, MemberRequiredMixin, CreateView):
    model = Contribution
    template_name = 'member/add_savings.html'
    fields = ['amount', 'notes'] # Simplified for members
    success_url = reverse_lazy('contributions:member_list')

    def form_valid(self, form):
        form.instance.member = self.request.user
        form.instance.cooperative = self.request.user.cooperative
        form.instance.contribution_date = timezone.now().date()
        form.instance.recorded_by = self.request.user
        form.instance.payment_reference = f"MEM-{uuid.uuid4().hex[:8].upper()}"
        form.instance.status = TransactionStatus.PENDING
        response = super().form_valid(form)
        
        # Notify Admin
        admins = form.instance.cooperative.users.filter(role=UserRole.COOP_ADMIN)
        for admin in admins:
            create_notification(
                user=admin,
                title="New Savings Deposit",
                message=f"{self.request.user.get_full_name()} has recorded a savings deposit of ₦{form.instance.amount:,}.",
                link="/contributions/management/"
            )
        return response

from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

class ApproveContributionView(LoginRequiredMixin, CoopAdminRequiredMixin, View):
    def post(self, request, pk):
        contribution = get_object_or_404(Contribution, pk=pk, cooperative=request.user.cooperative)
        if contribution.status == TransactionStatus.PENDING:
            contribution.status = TransactionStatus.APPROVED
            contribution.save()
            
            # Notify Member
            create_notification(
                user=contribution.member,
                title="Savings Deposit Approved",
                message=f"Your savings deposit of ₦{contribution.amount:,} has been approved.",
                link="/contributions/member/"
            )
            
            messages.success(request, f"Contribution for {contribution.member.get_full_name()} has been approved.")
        return redirect('contributions:coop_list')

class RejectContributionView(LoginRequiredMixin, CoopAdminRequiredMixin, View):
    def post(self, request, pk):
        contribution = get_object_or_404(Contribution, pk=pk, cooperative=request.user.cooperative)
        if contribution.status == TransactionStatus.PENDING:
            contribution.status = TransactionStatus.REJECTED
            contribution.save()
            
            # Notify Member
            create_notification(
                user=contribution.member,
                title="Savings Deposit Rejected",
                message=f"Your savings deposit of ₦{contribution.amount:,} has been rejected.",
                link="/contributions/member/"
            )
            
            messages.warning(request, f"Contribution for {contribution.member.get_full_name()} has been rejected.")
        return redirect('contributions:coop_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = getattr(self.request.user.cooperative, 'settings', None)
        context['title'] = 'Add Savings'
        context['description'] = 'Record a new savings deposit to your ledger.'
        return context
