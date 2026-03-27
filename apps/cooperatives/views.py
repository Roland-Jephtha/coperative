from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from apps.accounts.models import UserRole

class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == UserRole.SUPER_ADMIN

class CoopAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == UserRole.COOP_ADMIN

class SuperAdminDashboardView(LoginRequiredMixin, SuperAdminRequiredMixin, TemplateView):
    template_name = 'coop_admin/super_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO: Add platform-wide stats
        return context

class CoopAdminDashboardView(LoginRequiredMixin, CoopAdminRequiredMixin, TemplateView):
    template_name = 'coop_admin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        coop = self.request.user.cooperative
        
        # Base Metrics
        from apps.accounts.models import User, UserRole
        from django.db.models import Sum
        context['members_count'] = User.objects.filter(cooperative=coop, role=UserRole.MEMBER).count()
        
        from apps.contributions.models import Contribution, TransactionStatus
        total_contrib = Contribution.objects.filter(cooperative=coop, status=TransactionStatus.APPROVED).aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_contributions'] = f"{total_contrib:,.2f}"
        
        from apps.loans.models import Loan
        active_loans = Loan.objects.filter(cooperative=coop, status='ACTIVE').aggregate(Sum('amount'))['amount__sum'] or 0
        context['active_loans_total'] = f"{active_loans:,.2f}"

        # Pending Actions
        from apps.repayments.models import LoanRepayment
        context['pending_contributions_count'] = Contribution.objects.filter(cooperative=coop, status=TransactionStatus.PENDING).count()
        context['pending_repayments_count'] = LoanRepayment.objects.filter(loan__cooperative=coop, status=TransactionStatus.PENDING).count()
        context['total_pending_actions'] = context['pending_contributions_count'] + context['pending_repayments_count']

        # Chart Data Computation (Simple YTD Monthly Grouping)
        import datetime
        from django.utils import timezone
        import json
        
        today = timezone.now()
        months = []
        contrib_data = []
        expected_data = []
        collected_data = []

        from apps.repayments.models import LoanRepayment
        
        # Build last 6 months data
        for i in range(5, -1, -1):
            d = today - datetime.timedelta(days=30*i)
            months.append(d.strftime('%b'))
            
            # Simple aggregation by month/year matching
            c_sum = Contribution.objects.filter(
                cooperative=coop,
                status=TransactionStatus.APPROVED,
                contribution_date__year=d.year,
                contribution_date__month=d.month
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            contrib_data.append(float(c_sum))
            
            # Since there is no expected schedule tracker model, we will fallback to 0 for expected and calculate actual amount_paid
            expected_data.append(0.0)
            
            a_sum = LoanRepayment.objects.filter(
                loan__cooperative=coop,
                status=TransactionStatus.APPROVED,
                payment_date__year=d.year,
                payment_date__month=d.month
            ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
            collected_data.append(float(a_sum))

        context['contrib_labels'] = json.dumps(months)
        context['contrib_data'] = json.dumps(contrib_data)
        
        context['repay_labels'] = json.dumps(months)
        context['repay_expected'] = json.dumps(expected_data)
        context['repay_collected'] = json.dumps(collected_data)

        return context

from django.views.generic import ListView
from .models import Cooperative

class SuperCooperativesView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = Cooperative
    template_name = 'coop_admin/super_coops_list.html'
    context_object_name = 'cooperatives'

    def get_queryset(self):
        return Cooperative.objects.all().order_by('-created_at')


from django.views import View
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login
from django.utils import timezone

class CooperativeRegisterView(View):
    template_name = 'auth/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, 'cooperative') and request.user.cooperative and not request.user.cooperative.setup_complete:
                return redirect('cooperatives:onboarding')
            return redirect('cooperatives:admin_dashboard')
        return render(request, self.template_name)

    def post(self, request):
        # Step 1: Admin Registration Fields
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        coop_name = request.POST.get('coop_name', '').strip()
        password = request.POST.get('password', '')

        errors = []
        if not all([first_name, last_name, email, phone, coop_name, password]):
            errors.append("All fields are required.")
        
        from apps.accounts.models import User
        if User.objects.filter(username=email).exists():
            errors.append("An account with this email already exists.")

        if errors:
            return render(request, self.template_name, {'errors': errors, 'post': request.POST})

        from django.db import transaction
        from apps.accounts.models import UserRole
        from .models import Cooperative, CooperativeSetting

        try:
            with transaction.atomic():
                cooperative = Cooperative.objects.create(
                    name=coop_name,
                    phone=phone,
                    email=email
                )
                # Create default settings
                CooperativeSetting.objects.create(cooperative=cooperative)
                
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role=UserRole.COOP_ADMIN,
                    cooperative=cooperative,
                    is_active_member=True,
                    joined_at=timezone.now()
                )
            
            login(request, user)
            messages.success(request, f"Welcome, {first_name}! Let's set up your cooperative's financial rules.")
            return redirect('cooperatives:onboarding')
        except Exception as e:
            errors.append(f"An error occurred: {str(e)}")
            return render(request, self.template_name, {'errors': errors, 'post': request.POST})


from .models import (
    ContributionType, InterestCalculationType, LoanEligibilityType,
    RepaymentFrequency, PenaltyType, PenaltyFrequency, CooperativeSetting
)

class CooperativeOnboardingView(LoginRequiredMixin, CoopAdminRequiredMixin, View):
    template_name = 'auth/onboarding_wizard.html'

    def get(self, request):
        cooperative = request.user.cooperative
        if not cooperative or cooperative.setup_complete:
            return redirect('cooperatives:admin_dashboard')
        
        settings = getattr(cooperative, 'settings', None)
        if not settings:
            settings = CooperativeSetting.objects.create(cooperative=cooperative)

        context = {
            'cooperative': cooperative,
            'settings': settings,
            'contribution_types': ContributionType.choices,
            'interest_types': InterestCalculationType.choices,
            'eligibility_types': LoanEligibilityType.choices,
            'repayment_frequencies': RepaymentFrequency.choices,
            'penalty_types': PenaltyType.choices,
            'penalty_frequencies': PenaltyFrequency.choices,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        cooperative = request.user.cooperative
        settings = cooperative.settings

        # Step 6: Final check and save
        try:
            # Update Settings
            settings.contribution_type = request.POST.get('contribution_type')
            settings.default_contribution_amount = request.POST.get('default_contribution_amount', 0)
            settings.allow_custom_contributions = request.POST.get('allow_custom_contributions') == 'on'
            
            settings.default_loan_interest_rate = request.POST.get('default_loan_interest_rate', 0)
            settings.interest_calculation_type = request.POST.get('interest_calculation_type')
            
            settings.min_loan_amount = request.POST.get('min_loan_amount', 0)
            settings.max_loan_amount = request.POST.get('max_loan_amount', 0)
            settings.min_loan_duration_months = request.POST.get('min_loan_duration_months', 1)
            settings.max_loan_duration_months = request.POST.get('max_loan_duration_months', 12)
            
            settings.loan_eligibility_type = request.POST.get('loan_eligibility_type')
            settings.min_contribution_months_required = request.POST.get('min_contribution_months_required', 0)
            
            settings.repayment_frequency = request.POST.get('repayment_frequency')
            settings.grace_period_days = request.POST.get('grace_period_days', 0)
            
            settings.penalty_type = request.POST.get('penalty_type')
            settings.penalty_value = request.POST.get('penalty_value', 0)
            settings.penalty_frequency = request.POST.get('penalty_frequency')
            
            settings.allow_early_repayment = request.POST.get('allow_early_repayment') == 'on'
            settings.apply_early_repayment_discount = request.POST.get('apply_early_repayment_discount') == 'on'
            
            settings.bank_name = request.POST.get('bank_name')
            settings.account_number = request.POST.get('account_number')
            settings.account_name = request.POST.get('account_name')
            settings.savings_interest_rate = request.POST.get('savings_interest_rate', 0)
            
            # Notification Preferences
            settings.email_notifications = request.POST.get('email_notifications') == 'on'
            settings.in_app_notifications = request.POST.get('in_app_notifications') == 'on'
            # sms_notifications is disabled/coming soon in UI, but we can set it if posted
            settings.sms_notifications = request.POST.get('sms_notifications') == 'on'

            settings.save()
            
            # Mark setup complete
            cooperative.setup_complete = True
            cooperative.save()
            
            messages.success(request, "Cooperative setup completed successfully! Welcome to your dashboard.")
            return redirect('cooperatives:admin_dashboard')
        except Exception as e:
            messages.error(request, f"Error saving configuration: {str(e)}")
            return self.get(request)

from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin

class CooperativeSettingsUpdateView(LoginRequiredMixin, CoopAdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CooperativeSetting
    template_name = 'coop_admin/settings.html'
    fields = [
        'contribution_type', 'default_contribution_amount', 'allow_custom_contributions',
        'savings_interest_rate', 'bank_name', 'account_number', 'account_name',
        'default_loan_interest_rate', 'interest_calculation_type',
        'min_loan_amount', 'max_loan_amount', 'min_loan_duration_months', 'max_loan_duration_months',
        'loan_eligibility_type', 'min_contribution_months_required',
        'repayment_frequency', 'grace_period_days',
        'penalty_type', 'penalty_value', 'penalty_frequency',
        'allow_early_repayment', 'apply_early_repayment_discount',
        'email_notifications', 'in_app_notifications', 'sms_notifications'
    ]
    success_url = reverse_lazy('cooperatives:settings')
    success_message = "Cooperative settings updated successfully!"

    def get_object(self, queryset=None):
        from .models import CooperativeSetting
        return get_object_or_404(CooperativeSetting, cooperative=self.request.user.cooperative)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cooperative Settings'
        context['description'] = 'Manage your financial rules and bank details.'
        return context

