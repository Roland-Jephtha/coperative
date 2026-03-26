from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from .models import Loan, LoanStatus
from apps.cooperatives.views import CoopAdminRequiredMixin
from apps.accounts.models import UserRole
from apps.notifications.utils import create_notification

class CooperativeLoansView(LoginRequiredMixin, CoopAdminRequiredMixin, ListView):
    model = Loan
    template_name = 'coop_admin/loans_list.html'
    context_object_name = 'loans'

    def get_queryset(self):
        return Loan.objects.filter(cooperative=self.request.user.cooperative).order_by('-created_at')

from django.views.generic.edit import CreateView
from django.urls import reverse_lazy, reverse

class LoanCreateView(LoginRequiredMixin, CoopAdminRequiredMixin, CreateView):
    model = Loan
    template_name = 'components/generic_form.html'
    fields = ['member', 'amount', 'interest_rate', 'duration_months', 'interest_type', 'status']
    success_url = reverse_lazy('loans:coop_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter members to only show members of the current cooperative
        from apps.accounts.models import User, UserRole
        form.fields['member'].queryset = User.objects.filter(cooperative=self.request.user.cooperative, role=UserRole.MEMBER)
        return form

    def form_valid(self, form):
        form.instance.cooperative = self.request.user.cooperative
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Loan Application'
        context['description'] = 'Process a new loan for a cooperative member.'
        return context

from apps.members.views import MemberRequiredMixin

class MemberLoansView(LoginRequiredMixin, MemberRequiredMixin, ListView):
    model = Loan
    template_name = 'member/loans_list.html'
    context_object_name = 'loans'

    def get_queryset(self):
        return Loan.objects.filter(member=self.request.user).order_by('-created_at')

class MemberLoanCreateView(LoginRequiredMixin, MemberRequiredMixin, CreateView):
    model = Loan
    template_name = 'components/generic_form.html'
    fields = ['amount', 'duration_months', 'interest_type', 'purpose'] # Fixed: Loan has purpose not notes
    success_url = reverse_lazy('loans:member_list')

    def form_valid(self, form):
        form.instance.member = self.request.user
        form.instance.cooperative = self.request.user.cooperative
        # Use coop settings for interest rate if available, or default
        coop_settings = getattr(self.request.user.cooperative, 'settings', None)
        if coop_settings:
            form.instance.interest_rate = coop_settings.default_loan_interest_rate
        else:
            form.instance.interest_rate = 10.0
            
        form.instance.status = LoanStatus.PENDING # Always pending when member applies
        response = super().form_valid(form)
        
        # Notify Admin
        admins = form.instance.cooperative.users.filter(role=UserRole.COOP_ADMIN)
        for admin in admins:
            create_notification(
                user=admin,
                title="New Loan Application",
                message=f"{self.request.user.get_full_name()} has applied for a loan of ₦{form.instance.amount:,}.",
                link=reverse('loans:coop_list')
            )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Apply for a Loan'
        context['description'] = 'Submit a new loan request. Your application will be reviewed by the cooperative admin.'
        return context

class LoanScheduleView(LoginRequiredMixin, DetailView):
    model = Loan
    template_name = 'loans/schedule.html'
    context_object_name = 'loan'
    pk_url_kwarg = 'loan_id'

    def get_queryset(self):
        user = self.request.user
        if user.role in [UserRole.COOP_ADMIN, UserRole.SUPER_ADMIN]:
            return Loan.objects.filter(cooperative=user.cooperative)
        return Loan.objects.filter(member=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schedules'] = self.object.schedules.all().order_by('month_number')
        context['repayments'] = self.object.repayments.all().order_by('-payment_date')
        return context

from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

class ApproveLoanView(LoginRequiredMixin, CoopAdminRequiredMixin, View):
    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, id=loan_id, cooperative=request.user.cooperative)
        if loan.status == LoanStatus.PENDING:
            loan.status = LoanStatus.APPROVED
            loan.approval_date = timezone.now().date()
            loan.save()
            loan.generate_repayment_schedule()
            
            # Notify Member
            create_notification(
                user=loan.member,
                title="Loan Approved",
                message=f"Your loan request for ₦{loan.amount:,} has been approved.",
                link=reverse('loans:member_list')
            )
            
            messages.success(request, f"Loan for {loan.member.get_full_name()} has been approved and schedule generated.")
        return redirect('loans:coop_list')

class DisburseLoanView(LoginRequiredMixin, CoopAdminRequiredMixin, View):
    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, id=loan_id, cooperative=request.user.cooperative)
        if loan.status == LoanStatus.APPROVED:
            loan.status = LoanStatus.ACTIVE
            if 'proof_of_payment' in request.FILES:
                loan.proof_of_payment = request.FILES['proof_of_payment']
            loan.save()
            
            # Notify Member
            create_notification(
                user=loan.member,
                title="Loan Disbursed",
                message=f"Your loan of ₦{loan.amount:,} has been disbursed and is now ACTIVE.",
                link=reverse('loans:schedule', kwargs={'loan_id': loan.id})
            )
            
            messages.success(request, f"Loan for {loan.member.get_full_name()} has been marked as ACTIVE (Disbursed).")
        return redirect('loans:coop_list')

class RejectLoanView(LoginRequiredMixin, CoopAdminRequiredMixin, View):
    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, id=loan_id, cooperative=request.user.cooperative)
        if loan.status == LoanStatus.PENDING:
            loan.status = LoanStatus.REJECTED
            loan.save()
            
            # Notify Member
            create_notification(
                user=loan.member,
                title="Loan Rejected",
                message=f"Your loan request for ₦{loan.amount:,} has been rejected.",
                link=reverse('loans:member_list')
            )
            
            messages.warning(request, f"Loan for {loan.member.get_full_name()} has been rejected.")
        return redirect('loans:coop_list')


import csv
from django.http import HttpResponse

def export_loans_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="loans.csv"'
    writer = csv.writer(response)
    writer.writerow(['Member', 'Amount', 'Interest Rate', 'Duration', 'Status', 'Date Applied'])
    
    loans = Loan.objects.filter(cooperative=request.user.cooperative)
    for loan in loans:
        writer.writerow([
            loan.member.get_full_name(), 
            loan.amount, 
            loan.interest_rate, 
            loan.duration_months, 
            loan.get_status_display(),
            loan.application_date
        ])
    return response
