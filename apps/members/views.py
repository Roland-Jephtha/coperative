from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.accounts.models import UserRole

class MemberRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == UserRole.MEMBER

class MemberDashboardView(LoginRequiredMixin, MemberRequiredMixin, TemplateView):
    template_name = 'member/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        coop = user.cooperative
        
        from apps.contributions.models import Contribution, TransactionStatus
        from apps.loans.models import Loan, LoanStatus
        from django.db.models import Sum
        
        # Savings
        contributions = Contribution.objects.filter(member=user).order_by('-contribution_date')
        total_contributions = contributions.filter(status=TransactionStatus.APPROVED).aggregate(total=Sum('amount'))['total'] or 0
        
        # Loans
        active_loans = Loan.objects.filter(member=user, status__in=[LoanStatus.ACTIVE, LoanStatus.APPROVED])
        active_loan_balance = sum(loan.balance_remaining for loan in active_loans)
        
        # Announcements
        from apps.announcements.models import Announcement
        announcements = Announcement.objects.filter(cooperative=coop).order_by('-created_at')[:5]
        
        # Auto-open announcement if ID is provided
        target_announcement = None
        announcement_id = self.request.GET.get('announcement_id')
        if announcement_id:
            try:
                target_announcement = Announcement.objects.get(id=announcement_id, cooperative=coop)
            except (Announcement.DoesNotExist, ValueError):
                pass

        context.update({
            'cooperative': coop,
            'total_contributions': f"{total_contributions:,.2f}",
            'active_loan_balance': f"{active_loan_balance:,.2f}",
            'recent_contributions': contributions[:3],
            'announcements': announcements[:2],
            'target_announcement': target_announcement,
        })
        return context
