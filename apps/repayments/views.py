from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from .models import LoanRepayment, TransactionStatus
from apps.accounts.models import UserRole
from apps.notifications.utils import create_notification
from apps.members.views import MemberRequiredMixin
from apps.cooperatives.views import CoopAdminRequiredMixin
from apps.loans.models import Loan

class MemberLoanRepaymentCreateView(LoginRequiredMixin, MemberRequiredMixin, CreateView):
    model = LoanRepayment
    template_name = 'member/record_repayment.html'
    fields = ['amount_paid', 'notes']
    
    def form_valid(self, form):
        loan = get_object_or_404(Loan, pk=self.kwargs['loan_pk'], member=self.request.user)
        form.instance.loan = loan
        form.instance.payment_date = timezone.now().date()
        form.instance.recorded_by = self.request.user
        form.instance.status = TransactionStatus.PENDING
        # Balance remaining will be calculated upon approval
        form.instance.balance_remaining = 0 
        response = super().form_valid(form)
        
        # Notify Admin
        admins = form.instance.loan.cooperative.users.filter(role=UserRole.COOP_ADMIN)
        for admin in admins:
            create_notification(
                user=admin,
                title="New Loan Repayment",
                message=f"{self.request.user.get_full_name()} has recorded a repayment of ₦{form.instance.amount_paid:,} for Loan #{form.instance.loan.id}.",
                link=reverse('loans:schedule', kwargs={'loan_id': form.instance.loan.id})
            )

        return response

    def get_success_url(self):
        return reverse_lazy('loans:schedule', kwargs={'loan_id': self.kwargs['loan_pk']})

class ApproveLoanRepaymentView(LoginRequiredMixin, CoopAdminRequiredMixin, View):
    def post(self, request, pk):
        repayment = get_object_or_404(LoanRepayment, pk=pk, loan__cooperative=request.user.cooperative)
        if repayment.status == TransactionStatus.PENDING:
            repayment.status = TransactionStatus.APPROVED
            
            # Update the repayment's record of balance for historical reference
            repayment.balance_remaining = repayment.loan.balance_remaining - repayment.amount_paid
            repayment.save()
            
            # Trigger dynamic schedule update
            repayment.loan.update_schedule_status()
            
            # Notify Member
            create_notification(
                user=repayment.loan.member,
                title="Repayment Approved",
                message=f"Your loan repayment of ₦{repayment.amount_paid:,} has been approved.",
                link=reverse('loans:schedule', kwargs={'loan_id': repayment.loan.id})
            )
            
            messages.success(request, f"Repayment of ₦{repayment.amount_paid} for {repayment.loan.member.get_full_name()} has been approved.")
        return redirect('loans:schedule', loan_id=repayment.loan.id)

class RejectLoanRepaymentView(LoginRequiredMixin, CoopAdminRequiredMixin, View):
    def post(self, request, pk):
        repayment = get_object_or_404(LoanRepayment, pk=pk, loan__cooperative=request.user.cooperative)
        if repayment.status == TransactionStatus.PENDING:
            repayment.status = TransactionStatus.REJECTED
            repayment.save()
            
            # Notify Member
            create_notification(
                user=repayment.loan.member,
                title="Repayment Rejected",
                message=f"Your loan repayment of ₦{repayment.amount_paid:,} has been rejected.",
                link=reverse('loans:schedule', kwargs={'loan_id': repayment.loan.id})
            )
            
            messages.warning(request, f"Repayment for {repayment.loan.member.get_full_name()} has been rejected.")
        return redirect('loans:schedule', loan_id=repayment.loan.id)
