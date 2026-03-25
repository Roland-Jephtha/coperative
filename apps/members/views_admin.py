from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.contrib import messages
from apps.accounts.models import User, UserRole
from apps.cooperatives.views import CoopAdminRequiredMixin
from apps.contributions.models import Contribution
from apps.loans.models import Loan, LoanStatus
from django.shortcuts import render



class CooperativeMembersView(LoginRequiredMixin, CoopAdminRequiredMixin, ListView):
    model = User
    template_name = 'coop_admin/members_list.html'
    context_object_name = 'members'

    def get_queryset(self):
        qs = User.objects.filter(
            cooperative=self.request.user.cooperative,
            role=UserRole.MEMBER
        ).order_by('-date_joined')
        
        q = self.request.GET.get('q', '')
        status = self.request.GET.get('status', '')
        if q:
            qs = qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q) | qs.filter(email__icontains=q)
        if status == 'active':
            qs = qs.filter(is_suspended=False, is_active_member=True)
        elif status == 'suspended':
            qs = qs.filter(is_suspended=True)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        coop = self.request.user.cooperative
        context['total_members'] = User.objects.filter(cooperative=coop, role=UserRole.MEMBER).count()
        context['active_members'] = User.objects.filter(cooperative=coop, role=UserRole.MEMBER, is_suspended=False, is_active_member=True).count()
        context['suspended_members'] = User.objects.filter(cooperative=coop, role=UserRole.MEMBER, is_suspended=True).count()
        context['q'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


import random
import string

class MemberCreateView(LoginRequiredMixin, CoopAdminRequiredMixin, CreateView):
    model = User
    template_name = 'components/generic_form.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'gender', 'address']
    
    def form_valid(self, form):
        coop = self.request.user.cooperative
        if not coop:
            messages.error(self.request, "Your account is not associated with any cooperative. Please contact support.")
            return redirect('cooperatives:admin_dashboard')
        
        # Auto-generate username: <cooperative_name>/<unique_number>
        coop_slug = coop.name.lower().replace(' ', '')[:10]
        member_count = User.objects.filter(cooperative=coop, role=UserRole.MEMBER).count()
        username = f"{coop_slug}/{member_count + 101}"
        
        # Ensure unique
        while User.objects.filter(username=username).exists():
            member_count += 1
            username = f"{coop_slug}/{member_count + 101}"
        
        # Auto-generate password: simple 4 letters + 4 numbers
        letters = ''.join(random.choices(string.ascii_lowercase, k=4))
        numbers = ''.join(random.choices(string.digits, k=4))
        generated_password = f"{letters}{numbers}"
        
        form.instance.username = username
        form.instance.cooperative = coop
        form.instance.role = UserRole.MEMBER
        form.instance.joined_at = timezone.now()
        form.instance.set_password(generated_password)
        form.instance.must_change_password = True
        
        self.object = form.save()
        
        # Store for success page
        self.request.session['last_created_member_id'] = self.object.pk
        self.request.session['last_created_member_password'] = generated_password
        
        return redirect('members:add_success')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Member'
        context['description'] = 'Register a new member. Username and password will be automatically generated.'
        return context


class MemberCreateSuccessView(LoginRequiredMixin, CoopAdminRequiredMixin, TemplateView):
    template_name = 'coop_admin/member_create_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_id = self.request.session.get('last_created_member_id')
        password = self.request.session.get('last_created_member_password')
        
        if not member_id or not password:
             return context # Should probably redirect but let's be safe for now
             
        member = get_object_or_404(User, pk=member_id, cooperative=self.request.user.cooperative)
        context.update({
            'member': member,
            'generated_password': password,
            'title': 'Member Created Successfully'
        })
        return context


class MemberDetailView(LoginRequiredMixin, CoopAdminRequiredMixin, DetailView):
    model = User
    template_name = 'coop_admin/member_detail.html'
    context_object_name = 'member'
    pk_url_kwarg = 'member_id'

    def get_object(self, queryset=None):
        return get_object_or_404(
            User,
            pk=self.kwargs['member_id'],
            cooperative=self.request.user.cooperative,
            role=UserRole.MEMBER
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.object

        # Contributions
        contributions = Contribution.objects.filter(member=member).order_by('-contribution_date')
        total_contributions = contributions.aggregate(total=Sum('amount'))['total'] or 0
        last_contribution = contributions.first()
        
        # Loans
        loans = Loan.objects.filter(member=member).order_by('-created_at')
        active_loans = loans.filter(status__in=[LoanStatus.ACTIVE, LoanStatus.APPROVED])
        total_outstanding = active_loans.aggregate(total=Sum('amount'))['total'] or 0
        
        # Repayments
        from apps.repayments.models import LoanRepayment
        repayments = LoanRepayment.objects.filter(loan__member=member).order_by('-payment_date')
        total_repaid = repayments.aggregate(total=Sum('amount_paid'))['total'] or 0

        # Activity timeline from audit logs
        from apps.audit_logs.models import AuditLog
        from django.contrib.contenttypes.models import ContentType
        user_ct = ContentType.objects.get_for_model(User)
        activity = AuditLog.objects.filter(
            content_type=user_ct, object_id=member.pk
        ).order_by('-timestamp')[:20]

        context.update({
            'contributions': contributions[:10],
            'all_contributions': contributions,
            'total_contributions': total_contributions,
            'last_contribution': last_contribution,
            'loans': loans,
            'active_loans': active_loans,
            'total_outstanding': total_outstanding,
            'repayments': repayments[:10],
            'total_repaid': total_repaid,
            'activity': activity,
        })
        return context


class MemberUpdateView(LoginRequiredMixin, CoopAdminRequiredMixin, UpdateView):
    model = User
    template_name = 'components/generic_form.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'gender', 'address']
    pk_url_kwarg = 'member_id'

    def get_object(self, queryset=None):
        return get_object_or_404(
            User,
            pk=self.kwargs['member_id'],
            cooperative=self.request.user.cooperative,
            role=UserRole.MEMBER
        )

    def get_success_url(self):
        return reverse('members:detail', kwargs={'member_id': self.kwargs['member_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Member — {self.object.get_full_name()}'
        context['description'] = 'Update the member\'s personal details.'
        return context


class MemberSuspendView(LoginRequiredMixin, CoopAdminRequiredMixin, View):
    def post(self, request, member_id):
        member = get_object_or_404(User, pk=member_id, cooperative=request.user.cooperative, role=UserRole.MEMBER)
        member.is_suspended = True
        member.is_active = False
        member.save()
        
        # Log the action
        try:
            from apps.audit_logs.models import AuditLog
            from django.contrib.contenttypes.models import ContentType
            AuditLog.objects.create(
                user=request.user,
                action_performed=f"Suspended member: {member.get_full_name()}",
                content_type=ContentType.objects.get_for_model(User),
                object_id=member.pk,
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception:
            pass

        messages.success(request, f"Member {member.get_full_name()} has been suspended successfully.")
        return redirect(request.META.get('HTTP_REFERER', reverse('members:coop_list')))


class MemberActivateView(LoginRequiredMixin, CoopAdminRequiredMixin, View):
    def post(self, request, member_id):
        member = get_object_or_404(User, pk=member_id, cooperative=request.user.cooperative, role=UserRole.MEMBER)
        member.is_suspended = False
        member.is_active = True
        member.save()
        
        try:
            from apps.audit_logs.models import AuditLog
            from django.contrib.contenttypes.models import ContentType
            AuditLog.objects.create(
                user=request.user,
                action_performed=f"Reactivated member: {member.get_full_name()}",
                content_type=ContentType.objects.get_for_model(User),
                object_id=member.pk,
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception:
            pass

        messages.success(request, f"Member {member.get_full_name()} has been reactivated successfully.")
        return redirect(request.META.get('HTTP_REFERER', reverse('members:coop_list')))
