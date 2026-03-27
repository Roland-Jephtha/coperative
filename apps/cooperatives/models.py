from django.db import models

class Cooperative(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    registration_number = models.CharField(max_length=100, null=True, blank=True)
    logo = models.ImageField(upload_to='coop_logos/', null=True, blank=True)
    setup_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class InterestCalculationType(models.TextChoices):
    FLAT = 'FLAT', 'Flat Interest'
    REDUCING = 'REDUCING', 'Reducing Balance'
    MONTHLY = 'MONTHLY', 'Monthly Interest'

class ContributionType(models.TextChoices):
    WEEKLY = 'WEEKLY', 'Weekly'
    MONTHLY = 'MONTHLY', 'Monthly'
    FLEXIBLE = 'FLEXIBLE', 'Flexible'

class LoanEligibilityType(models.TextChoices):
    IMMEDIATE = 'IMMEDIATE', 'Immediate'
    HISTORY = 'HISTORY', 'Based on Contribution History'

class RepaymentFrequency(models.TextChoices):
    WEEKLY = 'WEEKLY', 'Weekly'
    MONTHLY = 'MONTHLY', 'Monthly'

class PenaltyType(models.TextChoices):
    FIXED = 'FIXED', 'Fixed Amount'
    PERCENTAGE = 'PERCENTAGE', 'Percentage (%)'

class PenaltyFrequency(models.TextChoices):
    ONETIME = 'ONETIME', 'One-time'
    RECURRING = 'RECURRING', 'Recurring'

class CooperativeSetting(models.Model):
    cooperative = models.OneToOneField(Cooperative, on_delete=models.CASCADE, related_name='settings')
    
    # Financial Configuration
    contribution_type = models.CharField(max_length=20, choices=ContributionType.choices, default=ContributionType.MONTHLY)
    default_contribution_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    allow_custom_contributions = models.BooleanField(default=True)
    savings_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Annual interest rate for savings")

    # Loan Interest Settings
    default_loan_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    interest_calculation_type = models.CharField(
        max_length=20, choices=InterestCalculationType.choices, default=InterestCalculationType.FLAT
    )

    # Loan Limit Settings
    min_loan_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    max_loan_amount = models.DecimalField(max_digits=12, decimal_places=2, default=1000000.00)

    # Loan Duration Settings
    min_loan_duration_months = models.IntegerField(default=1)
    max_loan_duration_months = models.IntegerField(default=12)

    # Loan Eligibility Rules
    loan_eligibility_type = models.CharField(max_length=20, choices=LoanEligibilityType.choices, default=LoanEligibilityType.IMMEDIATE)
    min_contribution_months_required = models.IntegerField(default=0)

    # Repayment Settings
    repayment_frequency = models.CharField(max_length=20, choices=RepaymentFrequency.choices, default=RepaymentFrequency.MONTHLY)
    grace_period_days = models.IntegerField(default=0)

    # Late Payment Penalty
    penalty_type = models.CharField(max_length=20, choices=PenaltyType.choices, default=PenaltyType.FIXED)
    penalty_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    penalty_frequency = models.CharField(max_length=20, choices=PenaltyFrequency.choices, default=PenaltyFrequency.ONETIME)

    # Advanced Settings
    allow_early_repayment = models.BooleanField(default=True)
    apply_early_repayment_discount = models.BooleanField(default=False)

    # Bank Details for Member Deposits
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)

    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.cooperative.name} Settings"
